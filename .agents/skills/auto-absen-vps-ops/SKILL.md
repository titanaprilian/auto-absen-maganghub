---
name: auto-absen-vps-ops
description: Safely inspect, troubleshoot, or deploy the Auto Absen MagangHub instance hosted on the user's VPS. Start with read-only SSH checks; use before touching production code, cron schedules, services, or running attendance commands.
---

# Auto Absen MagangHub VPS Operations

Use this skill for troubleshooting or deployment work on the hosted instance. The user identified the SSH alias `hostdataid`; the observed checkout path is `/home/titanic/project/auto-absen-maganghub`. Re-check both rather than assuming they remain valid.

## Default to read-only

- Begin with narrow SSH checks, for example:
  - `ssh hostdataid 'hostname; id -un'`
  - `ssh hostdataid 'git -C /home/titanic/project/auto-absen-maganghub status --short --branch'`
  - `ssh hostdataid 'git -C /home/titanic/project/auto-absen-maganghub log -1 --format=%h'`
  - `ssh hostdataid 'crontab -l | grep AutoAbsenMaganghub'`
- Inspect only the files, schedule entries, or service status needed to answer the question. Do not dump full logs, databases, shell history, process environments, or configuration files.
- Never read or print `.env`, credentials, tokens, or private user data. If configuration must be verified, check presence or setting names without retrieving values.
- The observed user-level `systemctl` query failed because no user bus was available. Do not assume user services are manageable through `systemctl --user`; identify the actual scheduler/service from current evidence and the repo's `README.md` and `setup_cron.sh`.

## Production safety boundary

- An SSH connection is not permission to change production. Before any write or externally visible action, get explicit user confirmation for that action and its target.
- Treat these as mutating actions requiring confirmation: pulling or merging code, copying files to the server, changing cron or systemd configuration, installing packages, restarting/disabling services, editing remote files, and running `main.py absen` or `main.py remind` without `--dry-run`.
- Never run destructive Git commands such as `reset`, `clean`, `checkout`, `stash`, or force operations on the VPS unless explicitly requested and the user has approved a recovery plan.
- Before deployment, inspect remote Git status and reconcile any existing local modifications with the user. Do not overwrite, discard, or silently deploy over them. Back up or preserve user changes only as directed.
- Do not run live attendance as a deployment smoke test. Use tests and non-submitting checks; ask for explicit confirmation if a live external action is necessary.

## Deployment and diagnosis

- Read the current checkout's documented deployment path before proposing commands. The repository has multiple independent execution paths: Linux/VPS cron (`setup_cron.sh`), GitHub Actions workflows, and Vercel endpoints/configuration. Confirm which one is active instead of assuming.
- Prefer inspecting cron markers and status over changing schedules. `setup_cron.sh` replaces its marked entries idempotently and may change active automation; run it only after explicit approval.
- For code-level diagnosis, compare the deployed commit and working-tree status with the local checkout. Do not disclose uncommitted diff contents unless relevant, and keep secrets out of command output.
- After an approved change, verify only the requested target, report exactly what changed, what was checked, and any remaining risk. Do not claim a deployment succeeded without verifying the resulting deployed state.

## Known state to re-check

A read-only inspection on 2026-11-25 found the checkout at the path above on branch `main`, with commit `13347b2`, multiple modified tracked files, additional untracked log-pool files, and a server-only `.agents/skills/maganghub-logbook-generator/SKILL.md`. This is a point-in-time observation, not a guarantee of current state. Preserve those changes and re-check before any operation. The user-level systemd bus was unavailable in that SSH session.
