# AGENTS.md

Guidance for AI coding assistants (Claude Code, Cursor, Copilot, Codex, etc.)
working in the pyvesync repository. The human opening the pull request is
responsible for the result — follow these rules.

## Read these first

- [`CLAUDE.md`](CLAUDE.md) — architecture overview, commands, and the
  Contribution Rules in AI-focused form.
- [`docs/development/contributing.md`](docs/development/contributing.md) —
  authoritative contribution guide (rules, code style, testing, diagnostics).
- [`docs/development/capturing.md`](docs/development/capturing.md) — how API
  request/response shapes are obtained.

## The rules (short form)

1. **Follow the intended architecture.** Three-tier hierarchy:
   `base_devices/` → `devices/` + API mixin (`BypassV1Mixin` / `BypassV2Mixin`)
   → `device_map.py`. Device state in the base `DeviceState` subclass; models in
   `models/`; constants and modes in `pyvesync.const`.
2. **Never invent API request/response fields.** They must come from a real
   packet capture. No capture → the behavior cannot be implemented. Do not guess.
3. **Real-hardware verification is required before merge.** New device support
   and any device-behavior change must be tested on the physical device, and the
   PR must state the model + firmware. An assistant cannot verify hardware — do
   not claim a device works; flag that a human with the device must test it.
4. **One change per PR.** A single feature, fix, or edit. Never batch unrelated
   or speculative changes into one large PR.
5. **Provide diagnostic info** (model, `product_type`, firmware, region,
   pyvesync/Python version, redacted `DEBUG` log, `device.last_response`) as
   described in `docs/development/contributing.md`.

If a request would violate these rules, do not produce speculative code —
explain the blocker and what is needed to proceed.
