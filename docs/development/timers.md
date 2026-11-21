# Timers

Most VeSync devices have a countdown timer that turns the device on or off
when it ends. This page describes how pyvesync models timers, which APIs the
devices use, and what is known about how the devices handle them.

## Public interface

Every device has three timer methods, declared on
[`VeSyncBaseDevice`][pyvesync.base_devices.vesyncbasedevice.VeSyncBaseDevice].
Devices without timer support keep the base-class stubs, which log a debug
message and return `False` or `None`.

| Method | Purpose |
| ------ | ------- |
| `get_timer()` | Read the timer from the API and set `state.timer` |
| `set_timer(duration, action=None)` | Start a timer of `duration` seconds |
| `clear_timer()` | Cancel the running timer |

The timer is held in `state.timer`, a
[`Timer`][pyvesync.utils.helpers.Timer] object, or `None` when no timer is
known. `Timer` holds the `timer_duration` in seconds, the `action` (`on` or
`off`) and the timer `id`. It counts down locally from the last update:
`time_remaining`, `running` and `done` are computed from the time the timer
was last set or read (`update_ts()`).

`state.timer` is set in up to three ways, depending on the device:

1. `get_timer()` reads the timer list and keeps the first timer.
2. `set_timer()` stores the new timer after the API accepts it.
3. Some devices report the remaining seconds in their status (for example
   `timerRemain`), so `update()` builds or refreshes the timer. A status
   timer keeps the id and duration of a timer set earlier, and becomes `None`
   when the status reports 0.

## Timer APIs

Each device family uses one of these request sets. The request and response
shapes are in `models/bypass_models.py` and the device modules.

| Family | Read | Add | Cancel | Timer id |
| ------ | ---- | --- | ------ | -------- |
| Bypass V1 cloud (ESW15 and outdoor outlets, wall and dimmer switches, ESL100 bulbs) | `timer/getTimers` | `timer/addTimer` (`counterTime`, `action`) | `timer/deleteTimer` (`timerId`) | Large id assigned by the cloud |
| 7A outlet | `GET /v2/device/{cid}/timer` | `POST /v2/device/{cid}/timer` | `DELETE /v2/device/{cid}/timer/{id}` | Assigned by the cloud |
| Bypass V2, V1-style timer (Core purifiers, ESW10 outlet, Classic 200S, Classic 300S, Dual 200S, LUH-A602S, LUH-O451S and LUH-M101S humidifiers) | `getTimer` | `addTimer` (`action`, `total`) | `delTimer` (`id`) | 1 |
| Bypass V2, V2 timer (Vital, EverestAir, Sprout and Vital Pet Pro purifiers, LV600S humidifier) | `getTimerV2` | `addTimerV2` (`startAct`, `total`) | `delTimerV2` (`id`) | 1 |

The tower fan (LTF-F422S) uses its own `getTimer`, `setTimer` and
`clearTimer` requests.

Two classes differ from the app captures and will be corrected separately:
the Vital, EverestAir and Sprout classes read the timer with `getTimer`
instead of `getTimerV2`, and the LUH-M101S class uses the V1-style requests
although an EU capture shows the V2 timer requests.

## Single-timer devices

The VeSync app handles a single timer on every timer screen. It reads the
timer list, uses the first timer, and shows either that timer with a Cancel
button or the page to add one. It never adds a timer while one is running.
When it cancels a timer without a known id, it sends id 1.

Bypass V2 devices hold one timer slot, and its id is always 1:

- Adding a timer returns id 1.
- Adding a second timer while the first is running returns id 1 and
  replaces the running timer. The list then holds only the new timer.
- Deleting id 1 succeeds, also when no timer is running.

For these devices the timer id is the constant
[`DEFAULT_TIMER_ID`][pyvesync.const.DEFAULT_TIMER_ID] (1). A device that uses
it does not read the timer list before adding or cancelling a timer:

- `set_timer()` sends the add request without checking for a running timer,
  and stores the timer with `DEFAULT_TIMER_ID`.
- `clear_timer()` sends the cancel request with `DEFAULT_TIMER_ID`, whether
  or not `state.timer` holds a timer, and sets `state.timer` to `None` on
  success.

The Vital Pet Pro (LAP-P501S) follows this. Other device families are being
moved to it one family at a time.

Bypass V1 cloud devices and the 7A outlet use large ids assigned by the
cloud, so `DEFAULT_TIMER_ID` does not apply to them. They need the id from
`set_timer()` or `get_timer()` before `clear_timer()` can cancel a timer.

## Adding timer support to a device

Only implement the timer requests that have been captured from the VeSync app
(see [Capturing](capturing.md)). When the device uses one of the request sets
above, follow the closest existing device class. For a bypass V2 device with
one timer slot, use `DEFAULT_TIMER_ID` and do not read the timer list in
`set_timer()` or `clear_timer()`.
