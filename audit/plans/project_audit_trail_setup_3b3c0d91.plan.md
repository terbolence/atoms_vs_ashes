---
name: Project Audit Trail Setup
overview: Create an in-repo audit trail with `audit/conversations/` and `audit/plans/` folders, a Cursor rule to enforce logging of every session, and seed both folders with existing history.
todos:
  - id: create-audit-folders
    content: Create `audit/conversations/`, `audit/plans/`, and `audit/README.md` with naming conventions and required sections.
    status: completed
  - id: create-cursor-rule
    content: "Create `.cursor/rules/audit-trail.mdc` with alwaysApply: true enforcing conversation logging and plan copying."
    status: completed
  - id: seed-plans
    content: Copy existing plan (`automated_system_architecture_split`) into `audit/plans/`.
    status: in_progress
  - id: seed-conversations
    content: Write retroactive conversation logs for prior sessions (architecture split, ownership table).
    status: pending
  - id: update-index
    content: Add audit trail reference in `requirements/00_index.md` linking to QA 13.1.6.
    status: pending
isProject: false
---

# Project Audit Trail Setup

## Context

IAEA QA requirement 13.1.6 (`[requirements/11_quality_assurance.md](requirements/11_quality_assurance.md)`) mandates that all correspondence be preserved in the project repository. Cursor stores conversations and plans in its own internal directories outside the workspace. This plan brings them under version control.

## 1. Create Folder Structure

```
audit/
  conversations/        # One markdown file per agent conversation
  plans/                # Copy of every plan created for this project
  README.md             # Explains audit trail conventions
```

## 2. Create `audit/README.md`

A short document defining:

- Naming convention for conversation logs: `YYYY-MM-DD_<short-slug>.md` (e.g. `2026-03-11_architecture-split.md`)
- Naming convention for plans: original plan filename preserved as-is
- Required sections in each conversation log (date, objective, key decisions, files changed, outcome)
- Reference to IAEA QA requirement 13.1.6

## 3. Create Cursor Rule: `.cursor/rules/audit-trail.mdc`

An `alwaysApply: true` rule that instructs the agent to:

- At the **end of every conversation** that produces changes, write a structured log to `audit/conversations/YYYY-MM-DD_<slug>.md` containing:
  - Date and session identifier
  - Objective / user request summary
  - Key decisions made
  - Files created, modified, or deleted
  - Outcome (completed / partial / deferred)
- When a **plan is created or implemented**, copy the plan content to `audit/plans/` preserving the original filename
- Never skip this step, even for small changes

## 4. Seed With Existing History

- Copy the current plan file `automated_system_architecture_split_e8922903.plan.md` from `~/.cursor/plans/` into `audit/plans/`
- Write a retroactive conversation log for the sessions that have already occurred in this project (architecture split, ownership table addition), based on the existing agent transcripts

## 5. Update `requirements/00_index.md`

Add a note in the Phase-to-File Mapping or a new row pointing to `audit/` as the audit trail, linking it to QA requirement 13.1.6.
