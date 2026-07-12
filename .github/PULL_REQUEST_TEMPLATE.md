<!--
Thanks for contributing to pyvesync! Please read the contribution rules first:
https://webdjoe.github.io/pyvesync/latest/development/contributing

These checkboxes are self-attested and enforced through review, not CI.
Please fill them in honestly. PRs that bundle unrelated changes or add/modify
device behavior without real-hardware testing will be asked to change before review.
-->

## Description

<!-- What does this PR change, and why? Link any related issue. -->

## Type of change

<!-- This PR must be a SINGLE feature, fix, or edit. Pick one. -->

- [ ] Bug fix (`fix:`)
- [ ] New feature or device support (`feat:`)
- [ ] Documentation (`docs:`)
- [ ] Refactor / test / chore (no functional change)

## Checklist

- [ ] This PR is a **single** feature, fix, or edit (not a bundle of unrelated changes).
- [ ] The change follows the intended architecture (base class → device + API mixin → device map; state in `DeviceState`; models in `models/`; constants in `pyvesync.const`).
- [ ] No API request/response fields were invented — all come from a real packet capture.
- [ ] `ruff check`, `mypy`, and `pytest` pass locally.
- [ ] Tests added/updated and API fixtures written (`pytest --write_api`) where relevant.
- [ ] Documentation updated if behavior or public API changed.

## Real-hardware verification

<!-- Required for new device support and any change to device behavior.
     Testing only through Home Assistant does NOT satisfy this. -->

- [ ] Tested on the physical device.
  - Model: `____`
  - Firmware version: `____`
- [ ] Not applicable (explain why): `____`
- [ ] I do not own the device; a packet capture is provided / the device has been shared with a maintainer for verification.
