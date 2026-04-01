<!-- man_hours: 2.0 -->
# Audit Trail

**Project:** SMR Siting Assessment — Automated Site Evaluation System

**QA Reference:** IAEA QA requirement 13.1.6 (see `requirements/11_quality_assurance.md`) — all raw data, intermediate calculations, software code, and correspondence shall be preserved in the project repository.

---

## Folder Structure

```
audit/
  conversations/    One markdown file per agent conversation session
  plans/            Copy of every plan created and implemented for this project
  README.md         This file
```

---

## Conversation Logs

### Naming Convention

```
YYYY-MM-DD_<short-slug>.md
```

Examples:
- `2026-03-11_architecture-split.md`
- `2026-03-11_ownership-table.md`

If multiple conversations occur on the same date with the same topic, append a sequence number: `2026-03-11_architecture-split_02.md`.

### Required Sections

Every conversation log must contain:

| Section | Content |
|---|---|
| **Date** | ISO 8601 date of the session |
| **Session ID** | Cursor conversation/agent transcript identifier, if available |
| **Objective** | What the user requested |
| **Key Decisions** | Choices made during the session (e.g. module boundaries, technology picks, naming conventions) |
| **Files Changed** | List of files created, modified, or deleted with a one-line description of each change |
| **Outcome** | Completed / Partial / Deferred — and any follow-up items |

---

## Plans

### Naming Convention

Plans are copied verbatim from Cursor's plan system. The original filename is preserved:

```
<plan_name>_<hash>.plan.md
```

Example: `automated_system_architecture_split_e8922903.plan.md`

### Contents

Each plan file contains the full plan as authored, including frontmatter with todo status. Plans are copied into `audit/plans/` when they are created or after implementation is complete, whichever comes first.

---

## Versioning

All audit trail files are committed to Git alongside the changes they document. The audit log for a given session should be included in the same commit (or the final commit) of the work it describes.
