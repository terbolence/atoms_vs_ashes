#!/usr/bin/env bash
# Parallel API response audit — launches each connector as a background process.
# All connectors hit different API servers so they can run simultaneously.
# Per-site calls within each connector are serial (rate-limited by the connector).
#
# Usage:
#   bash scripts/run_audit_parallel.sh                  # default run_id
#   bash scripts/run_audit_parallel.sh my_custom_run_id # custom run_id
#
# Logs:  logs/audit_rerun/<run_id>/<connector>.log
# Safety: writes ONLY to site_raw_responses — zero domain table overwrites.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

# Activate virtualenv if present
if [ -f "venv_test/bin/activate" ]; then
    source "venv_test/bin/activate"
elif [ -f "venv/bin/activate" ]; then
    source "venv/bin/activate"
fi

RUN_ID="${1:-audit_$(date +%Y%m%dT%H%M%S)}"
LOG_DIR="logs/audit_rerun/$RUN_ID"
mkdir -p "$LOG_DIR"

CONNECTORS="bdticm_bedrock copernicus_dem copernicus_ems corine natura2000 egdi_geology onegeology noaa_ncei soilgrids"

echo "============================================================"
echo "  API Response Audit — Parallel Launcher"
echo "============================================================"
echo "  RUN_ID:     $RUN_ID"
echo "  LOG_DIR:    $LOG_DIR"
echo "  CONNECTORS: $CONNECTORS"
echo "  STARTED:    $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "============================================================"
echo ""

# --- EGDI probe --------------------------------------------------------
echo "[probe] Testing EGDI WFS availability..."
if curl -sf --max-time 15 \
    "https://maps.europe-geology.eu/wfs/?service=WFS&version=2.0.0&request=GetFeature&typeName=ms:EGDI_HIKE_Faults&count=1&outputFormat=application/json" \
    > /dev/null 2>&1; then
    echo "[probe] EGDI WFS is UP — will include egdi_geology"
else
    echo "[probe] EGDI WFS is DOWN — skipping egdi_geology (weekend outage pattern)"
    CONNECTORS=$(echo "$CONNECTORS" | sed 's/egdi_geology//')
fi
echo ""

# --- Launch each connector as a background process ---------------------
PIDS=""
SLUGS=""
LAUNCHED=0

for slug in $CONNECTORS; do
    [ -z "$slug" ] && continue
    echo "[launch] $slug → $LOG_DIR/${slug}.log"
    PYTHONPATH=src python -u scripts/rerun_audit_responses.py \
        --run-id "$RUN_ID" --connectors "$slug" \
        > "$LOG_DIR/${slug}.log" 2>&1 &
    pid=$!
    PIDS="$PIDS $pid"
    SLUGS="$SLUGS $slug"
    LAUNCHED=$((LAUNCHED + 1))
done

echo ""
echo "[info] Launched $LAUNCHED connector processes"
echo "[info] Monitoring... (Ctrl+C to cancel all)"
echo ""

# --- Wait for all processes, collect exit codes ------------------------
FAILED=0
SUCCEEDED=0
i=0
for pid in $PIDS; do
    i=$((i + 1))
    slug=$(echo "$SLUGS" | awk "{print \$$i}")
    if wait "$pid" 2>/dev/null; then
        SUCCEEDED=$((SUCCEEDED + 1))
        echo "[done] $slug — OK (exit 0)"
    else
        ec=$?
        FAILED=$((FAILED + 1))
        echo "[done] $slug — FAILED (exit $ec)"
    fi
done

# --- Summary -----------------------------------------------------------
echo ""
echo "============================================================"
echo "  SUMMARY"
echo "============================================================"
echo "  RUN_ID:    $RUN_ID"
echo "  FINISHED:  $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "  LAUNCHED:  $LAUNCHED"
echo "  SUCCEEDED: $SUCCEEDED"
echo "  FAILED:    $FAILED"
echo "  LOGS:      $LOG_DIR/"
echo "============================================================"

# --- Post-run DB verification ------------------------------------------
echo ""
echo "[verify] Querying site_raw_responses for run_id=$RUN_ID ..."
PYTHONPATH=src python -c "
from dotenv import load_dotenv
import os
load_dotenv(os.path.join(os.getcwd(), '.env'))
from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.engine import init_engine, session_scope
from sqlalchemy import text
settings = Settings()
init_engine(settings)
with session_scope() as s:
    rows = s.execute(text('''
        SELECT connector_slug, COUNT(*) as responses, COUNT(DISTINCT site_id) as sites
        FROM site_raw_responses
        WHERE run_id = :rid
        GROUP BY connector_slug
        ORDER BY connector_slug
    '''), {'rid': '$RUN_ID'}).fetchall()
    print(f'  {\"CONNECTOR\":<25s} {\"RESPONSES\":>10s} {\"SITES\":>8s}')
    print(f'  {\"-\"*25} {\"-\"*10} {\"-\"*8}')
    for r in rows:
        print(f'  {r[0]:<25s} {r[1]:>10d} {r[2]:>8d}')
    total_rows = sum(r[1] for r in rows) if rows else 0
    total_sites = sum(r[2] for r in rows) if rows else 0
    print(f'  {\"-\"*25} {\"-\"*10} {\"-\"*8}')
    print(f'  {\"TOTAL\":<25s} {total_rows:>10d} {total_sites:>8d}')
    if not rows:
        print('  (no rows found)')
" 2>&1

exit $FAILED
