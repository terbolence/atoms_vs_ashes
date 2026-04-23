"""Progressive SA(T) enrichment — batches of 20, auto-continue after first clean batch."""
import json
import os
import sys
import time
import uuid

from dotenv import load_dotenv

load_dotenv(os.path.join(os.getcwd(), ".env"))

from sqlalchemy import create_engine, text

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.connectors.seismic_hazard.client import SeismicHazardConnector
from atoms_vs_ashes.db.engine import init_engine, session_scope
from atoms_vs_ashes.db.models import Site, SiteNaturalHazards

BATCH_SIZE = 20


def get_remaining_site_ids(engine) -> list[str]:
    with engine.connect() as conn:
        r = conn.execute(
            text("""
            SELECT s.site_id
            FROM sites s
            JOIN site_natural_hazards nh ON s.site_id = nh.site_id
            WHERE nh.spectral_accel_json IS NOT NULL
            ORDER BY s.country_code, s.name
        """)
        )
        ids = []
        for row in r:
            d_raw = conn.execute(
                text(
                    "SELECT spectral_accel_json FROM site_natural_hazards WHERE site_id = :sid"
                ),
                {"sid": row.site_id},
            ).scalar()
            d = d_raw if isinstance(d_raw, dict) else json.loads(d_raw)
            sa = d.get("sa_values", {})
            hc = d.get("hazard_curve")
            if not sa and hc is not None:
                ids.append(str(row.site_id))
        return ids


def run_batch(
    connector: SeismicHazardConnector,
    site_ids: list[str],
    batch_num: int,
    run_id: str,
) -> dict:
    from atoms_vs_ashes.connectors.seismic_hazard.batch import enrich_batch

    with session_scope() as session:
        for uid_str in site_ids:
            row = session.get(SiteNaturalHazards, uuid.UUID(uid_str))
            if row:
                row.run_id = None
        session.commit()

        result = enrich_batch(
            connector,
            session,
            run_id,
            site_ids=[uuid.UUID(u) for u in site_ids],
        )

    sa_counts = []
    with session_scope() as session:
        for uid_str in site_ids:
            row = session.get(SiteNaturalHazards, uuid.UUID(uid_str))
            if row and row.spectral_accel_json:
                d = row.spectral_accel_json
                if isinstance(d, str):
                    d = json.loads(d)
                n_sa = len(d.get("sa_values", {}))
                sa_counts.append(n_sa)
            else:
                sa_counts.append(0)

    return {
        "batch_num": batch_num,
        "total": result.total_sites,
        "succeeded": result.succeeded,
        "failed": result.failed,
        "cached": result.skipped_cached,
        "elapsed_s": round(result.elapsed_s, 1),
        "sa_counts": sa_counts,
        "errors": [
            (s.site_name, s.error) for s in result.per_site if s.status == "error"
        ],
    }


def main():
    settings = Settings()
    init_engine(settings)

    db_url = (
        f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
        f"@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}"
        f"/{os.environ['POSTGRES_DB']}"
    )
    engine = create_engine(db_url)

    remaining = get_remaining_site_ids(engine)
    print(f"Sites needing SA(T): {len(remaining)}")
    if not remaining:
        print("Nothing to do.")
        return

    n_batches = (len(remaining) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"Batches of {BATCH_SIZE}: {n_batches}")
    print(f"Strategy: review after batch 1; auto-continue if 0 errors\n")

    run_id_base = f"nh01_sa_batch_{int(time.time())}"
    consecutive_ok = 0
    auto_mode = False
    total_done = 0
    total_failed = 0
    t_global = time.monotonic()

    with SeismicHazardConnector(settings) as conn:
        conn._fetch_spectral_periods = True
        conn.enable_audit_log(run_id_base)

        for batch_idx in range(n_batches):
            start = batch_idx * BATCH_SIZE
            end = min(start + BATCH_SIZE, len(remaining))
            batch_ids = remaining[start:end]
            run_id = f"{run_id_base}_b{batch_idx + 1:02d}"

            print(f"{'='*60}")
            print(
                f"BATCH {batch_idx + 1}/{n_batches}  "
                f"sites {start + 1}-{end}/{len(remaining)}  "
                f"run_id={run_id}"
            )
            print(f"{'='*60}")

            result = run_batch(conn, batch_ids, batch_idx + 1, run_id)

            total_done += result["succeeded"]
            total_failed += result["failed"]
            sa_ok = sum(1 for c in result["sa_counts"] if c == 6)
            sa_partial = sum(1 for c in result["sa_counts"] if 0 < c < 6)
            sa_none = sum(1 for c in result["sa_counts"] if c == 0)

            print(f"\n  Result: {result['succeeded']} ok, {result['failed']} failed, "
                  f"{result['cached']} cached  ({result['elapsed_s']}s)")
            print(f"  SA(T):  {sa_ok} complete (6/6), {sa_partial} partial, {sa_none} none")

            if result["errors"]:
                for name, err in result["errors"]:
                    print(f"  ERROR: {name}: {err}")

            elapsed_total = time.monotonic() - t_global
            rate = total_done / elapsed_total if elapsed_total > 0 else 0
            eta = (len(remaining) - end) / rate if rate > 0 else 0
            print(
                f"  Progress: {end}/{len(remaining)} "
                f"({total_done} ok, {total_failed} fail)  "
                f"ETA: {eta / 60:.0f} min"
            )

            if result["failed"] > 0:
                consecutive_ok = 0
                if auto_mode:
                    print("\n*** ERRORS detected in auto-mode — stopping for review ***")
                    sys.exit(1)
                else:
                    print("\n*** ERRORS in batch — stopping for review ***")
                    sys.exit(1)
            else:
                consecutive_ok += 1

            if not auto_mode and consecutive_ok >= 1:
                print(f"\n  >> First batch clean ({consecutive_ok * BATCH_SIZE} "
                      f"consecutive OK) — switching to auto-mode")
                auto_mode = True

    elapsed_total = time.monotonic() - t_global
    print(f"\n{'='*60}")
    print(f"ALL DONE: {total_done} ok, {total_failed} failed  "
          f"({elapsed_total / 60:.1f} min)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
