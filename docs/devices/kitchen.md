# VeSync Air Fryers

pyvesync supports these Cosori smart air fryers. All of them are in
`manager.devices.air_fryers` after `get_devices()`.

| Model | Class | Chambers | Preheat | Pause / resume | Unit before first `update()` |
| --- | --- | --- | --- | --- | --- |
| CS137-AF, CS158-AF (3.7 and 5.8 Qt.) | `VeSyncAirFryer158` | 1 | ✔ | ✔ | °F |
| CAF-DC601S TurboBlaze 6 Qt. | `VeSyncTurboBlazeFryer` | 1 | ✔ | | °F |
| CAF-P583S Dual Blaze 6.8 Qt. (KUS, KEU) | `VeSyncDualBlazeFryer` | 1 | | | °F (KUS), °C (KEU) |
| CAF-TF101S Dual Air Fryer | `VeSyncDualAirFryer` | 1, 2, whole, both | | | °C |
| CAF-DC111S-AEU Turbo Tower Pro | `VeSyncDualAirFryer` | 1 (upper), 2 (lower), both | | | °C |

The CAF-TF102S uses `VeSyncDualAirFryer` and the same chambers, without the
Dry mode. Its mapping comes from the VeSync app and is pending hardware
verification. The CAF-P583S KEU has no packet capture; it is assumed to match
the KUS apart from its Celsius unit. The CAF-DC111S-AEU mapping comes from
the VeSync app and the status captures supplied with PR #536; its cook and
end requests are pending hardware verification.

Every fryer has `set_mode()`, `set_mode_from_recipe()`, `end()` and
`update()`. `stop()`, `resume()` and `cook_from_preheat()` are only
implemented for the CS137/CS158; on the other fryers they log a message and
return `False` without sending a request. Air fryers have no on/off command
and no `turn_on()` / `turn_off()`; the CS137/CS158 `toggle_switch()` is
deprecated and sends no request.

## Quick start

```python
import asyncio
from pyvesync import VeSync


async def main():
    async with VeSync(username="EMAIL", password="PASSWORD") as manager:
        await manager.login()
        await manager.get_devices()

        fryer = manager.devices.air_fryers[0]
        await fryer.update()
        print(fryer.state.cook_status, fryer.temp_unit)

        # Cook for 15 minutes at 400 °F (converted on Celsius fryers)
        if await fryer.set_mode(15 * 60, 400, temp_unit='f'):
            print(fryer.state.cook_time_remaining)

        await fryer.end()


asyncio.run(main())
```

Every control method returns `True` when the device accepted the command and
`False` otherwise. A rejected argument (unsupported chamber, cook mode,
temperature, time or unit) returns `False` before any request is sent, with a
log message saying why. The control methods and `update()` log problems
rather than raising them.

A failed or unreadable `update()` (no response, an error code, an unknown
cook status, an out-of-range step) logs a message and leaves the chamber
state as it was, so a command afterwards still sees the last known phase.
On the dual-chamber fryers (CAF-TF101S/TF102S, CAF-DC111S-AEU) both
chambers take the connection status and update time from the response, and
a chamber with an unknown status keeps its state.
A reported temperature unit pyvesync does not recognise is logged and the
current unit kept.

A command the fryer refuses returns `False` and leaves the state as it was;
`fryer.last_response` names the reason. For example, the CAF-DC111S-AEU can
refuse a Sync cook (`chamber=BOTH`) with `BYPASS_SYNC_FINISH_FAIL_1` (open
the other basket), `BYPASS_SYNC_FINISH_FAIL_2` (reduce the cooking time of
the current basket) or `BYPASS_AVATAR_SYNC_FAIL` (Sync cannot start while
cooking).

## Cooking

```python
await fryer.set_mode(cook_time, cook_temp, *, temp_unit=None,
                     preheat_time=None, cook_mode=None, chamber=CHAMBER_1)
```

- `cook_time` and `preheat_time` are in **seconds**, as whole numbers (a
  fraction is dropped). `cook_time` must be at least 1 second. The CS137/CS158
  API counts in whole minutes, so pyvesync rounds the time down to the minute
  (90 s is sent as 1 minute) and rejects a `cook_time` under 60 s. There is
  no upper limit: pyvesync does not check the app's per-mode time ranges
  (for example 1-60 minutes for most modes), so a longer time is sent as
  given and the fryer may refuse it.
- `cook_temp` is in the fryer's `temp_unit`, or in `temp_unit` if you pass
  one (see [Temperature units](#temperature-units)).
- With no `cook_mode`, the fryer's default preset is used: Manual Cooking on
  the CS137/CS158 and Air Fry on the others. Only the preset's mode, recipe
  ID, name and type are sent; the time and temperature are yours. See
  [Cook modes](#cook-modes) for the other modes.
- The temperature is rounded to the nearest step of the mode, never
  rejected for being off-step, and then checked against the mode's range
  (see [Temperature limits](#temperature-limits)).
- `preheat_time` starts a preheat phase on fryers with preheat. There it must
  be 0 (no preheat) or at least one API time unit: 1 second, or 60 seconds on
  the CS137/CS158, which also rounds it down to whole minutes. A negative or
  shorter time returns `False` without a request. The CAF-P583S and the
  dual-chamber fryers (CAF-TF101S/TF102S, CAF-DC111S-AEU) have no preheat
  and drop it (with a debug log).
- pyvesync sends `readyStart` false. The CS137/CS158 capture shows the cook
  then starts at once, without the start button; the other models are assumed
  to behave the same.

After a successful command the chamber's state is set from the request
(status, set time, remaining time, temperature and mode), and the remaining
times count down locally. The next `update()` replaces them with what the
device reports.

## Recipes

`get_mode_recipe(cook_mode)` returns a cook mode's preset at the VeSync app's
default time and temperature, as an `AirFryerPresetRecipe`, or `None` if the
fryer has no such mode. Pass it to `set_mode_from_recipe()`, changing the
time, temperature or preheat first if needed:

```python
from dataclasses import replace
from pyvesync.const import AirFryerCookModes

recipe = fryer.get_mode_recipe(AirFryerCookModes.ROAST)
if recipe is not None:
    recipe = replace(recipe, cook_time=25 * 60, preheat_time=3 * 60)
    await fryer.set_mode_from_recipe(recipe)
```

`AirFryerPresetRecipe` holds `recipe_name`, `cook_mode`, `recipe_id`,
`recipe_type`, `target_temp`, `temp_unit` (`'f'` or `'c'`), `cook_time` and
`preheat_time` (both in seconds; `preheat_time` is optional). The recipe's
temperature is converted to the fryer's unit if needed, rounded and checked
against the limits of the recipe's `cook_mode`. The times are checked as for
`set_mode()`. The recipe's `cook_mode` must be one of the fryer's modes (see
[Cook modes](#cook-modes)); otherwise the method returns `False` without a
request. Its mode, ID, name and type are sent as given, so start from
`get_mode_recipe()` rather than inventing them. `cook_mode` is the API mode
string (`'AirFry'`, `'poultry'`) or an `AirFryerCookModes` key; the API mode
string is what is sent. A recipe `temp_unit` that does not start with `c` or
`f` returns `False` without a request.

`fryer.default_preset` is the recipe `set_mode()` copies when no `cook_mode`
is given. Each fryer has its own copy, so changing it affects only that
fryer. Its own time and temperature are pyvesync defaults and can differ
from `get_mode_recipe()` for the same mode; use `get_mode_recipe()` for the
app's defaults.

## Controlling a cook

| Method | What it does | Fryers |
| --- | --- | --- |
| `end(chamber)` | Ends the cook or preheat and returns the chamber to standby. | All |
| `stop(chamber)` | Pauses the cook or preheat. | CS137/CS158 |
| `resume(chamber)` | Resumes a paused cook or preheat. | CS137/CS158 |
| `cook_from_preheat(chamber)` | Starts the cook once preheat has finished (`PREHEAT_END`). | CS137/CS158 |

On the CS137/CS158, `end()`, `stop()` and `resume()` use the last known
status (from `update()` or the last successful command) to choose between the
cook and preheat commands. Paused, basket-out and preheat-finished count as in
a phase.

- `stop()` and `resume()` are always sent: the preheat command during a
  preheat phase, otherwise the cook command (also in standby). They don't
  check whether the fryer is already paused or running.
- `end()` returns `False` without a request when the fryer is in neither a
  cook nor a preheat phase (standby, or `APPOINTING`, so a scheduled cook
  cannot be cancelled).
- Every successful command sets the state to the phase it sent (`stop()`
  gives `COOK_STOP` or `PREHEAT_STOP`, `resume()` gives `COOKING` or
  `HEATING`), so the next command picks the matching one without an
  `update()`. The remaining time carries over, so `resume()` while running
  does not restart the countdown.

Call `update()` first if the fryer may have changed state on its own.

The dual-chamber fryers have no pause command. Their status maps have
`cookStop` and `pullOut`; per the app's behaviour, pulling a basket out
pauses that chamber and pushing it back in resumes it. The CAF-DC111S-AEU
captures report both statuses during a cook, with the remaining time held;
no TF101S capture of them exists yet.

## Reading status

`update()` polls the device. Single-chamber fryers keep their status in
`fryer.state`; dual-chamber fryers have `state_chamber_1` and
`state_chamber_2` (`state` is `state_chamber_1`), and `get_chamber_state()`
returns the state for one chamber. All times are in seconds and all
temperatures in the fryer's `temp_unit`.

| Attribute | Meaning |
| --- | --- |
| `cook_status` | An `AirFryerCookStatus` member (see below). |
| `cook_mode`, `recipe` | The API mode string and recipe name of the current or last cook (`cook_mode` is kept in standby). After a local command, `recipe` is set only on the dual-chamber fryers; the other fryers fill it on `update()`. |
| `cook_set_temp`, `current_temp` | The set and measured temperatures. The dual-chamber fryers' status has no measured-temperature field, so `current_temp` stays `None`. |
| `cook_set_time`, `preheat_set_time` | The set cook and preheat times. |
| `cook_time_remaining`, `preheat_time_remaining` | Remaining cook and preheat time, counting down from the last update while running (and during `HOLD` while the other chamber cooks, where `cook_time_remaining` is the wait before the chamber starts). `None` outside that phase. |
| `total_time_remaining` | Time until the cook finishes, preheat included. `None` in standby, and on the CS137/CS158 during preheat once an `update()` has run (that fryer reports no cook time then). |
| `is_cooking`, `is_preheating`, `is_running` | `is_cooking` is True in `COOKING`, `is_preheating` in `HEATING`, `is_running` in either. |
| `is_in_cook_mode`, `is_in_preheat_mode` | True in any cook or preheat status, running or not (for example `COOK_STOP`, `COOK_END`, `PREHEAT_END`), and with the basket out during that phase. |
| `can_resume` | True when paused (`COOK_STOP` or `PREHEAT_STOP`). |

`AirFryerCookStatus` values (from `pyvesync.const`). Not every fryer reports
every status:

| Member | Meaning |
| --- | --- |
| `STANDBY` | Idle. |
| `HEATING` | Preheating. |
| `PREHEAT_STOP` | Preheat paused. |
| `PREHEAT_END` | Preheat finished, waiting for `cook_from_preheat()` (CS137/CS158). |
| `COOKING` | Cooking. |
| `COOK_STOP` | Cook paused. |
| `PULL_OUT` | Basket pulled out. |
| `COOK_END` | Cook finished. |
| `READY` | Set up and waiting to start on the fryer. |
| `APPOINTING` | Waiting for a delayed start set in the app (CS137/CS158). pyvesync cannot set one. |
| `HOLD` | Sync cook with different times: this chamber waits so both finish together (CAF-DC111S-AEU). `cook_time_remaining` is the wait and `total_time_remaining` includes the cook; both count down only while the other chamber is cooking, and stop while it is paused. Counts as cook mode; `is_running` is False. pyvesync's `BOTH` sends the same settings to both chambers, so only a Sync cook started in the app or on the fryer reports it. |

The CAF-P583S status map maps `keeping` (keep-warm) to `COOKING`; no capture
of it exists yet. `COMPLETED` and `UNKNOWN` are in the enum but no supported
fryer reports them.

Each state's `to_dict()` / `to_json()` gives all of these values at once.

## Chambers

Every fryer method that targets a basket takes a `chamber` argument, an
`AirFryerChamber` member (from `pyvesync.const`) or its integer value. The
values match the API's `workChamber` / `chamber` fields.

| Member | Value | Meaning |
| --- | --- | --- |
| `CHAMBER_1` | 1 | Chamber 1 (left; upper on the CAF-DC111S-AEU). The default, and the only chamber on single-basket fryers. |
| `CHAMBER_2` | 2 | Chamber 2 (right; lower on the CAF-DC111S-AEU). Dual-chamber fryers only. |
| `WHOLE` | 3 | The merged basket with the divider removed. CAF-TF101S/TF102S only (`WHOLE_CHAMBER` feature). |
| `BOTH` | 4 | Both chambers with the same settings, sent as the app's Sync mode (both chambers finish together). Dual-chamber fryers only. |

`supported_chambers` lists the chambers a fryer accepts, and `is_dual_chamber`
is True for dual-basket models.

On a dual-chamber fryer:

```python
from pyvesync.const import AirFryerChamber

await fryer.set_mode(600, 200, chamber=AirFryerChamber.CHAMBER_2)
await fryer.set_mode_from_recipe(recipe, chamber=AirFryerChamber.BOTH)
await fryer.end(AirFryerChamber.BOTH)

await fryer.update()
chamber_state = fryer.get_chamber_state(AirFryerChamber.CHAMBER_2)
if chamber_state is not None:
    remaining = chamber_state.cook_time_remaining
```

A chamber the fryer does not support makes the method return `False` without
sending a request. `get_chamber_state()` returns `None` (with a debug log)
for `BOTH`, which names two states (read `state_chamber_1` and
`state_chamber_2` instead), and for a chamber the fryer does not support.

`sync_chambers` and `work_chamber` are read-only. `update()` sets both from
the device; `sync_chambers` is also set by a successful start or `end(BOTH)`.
They are the same on the fryer and on both chamber states, and on
single-chamber fryers they are always `False` and `None`.

- `sync_chambers` is True only when the device reports the app's Sync mode
  (both chambers finish together). The app's Match mode reports False. A
  successful `set_mode()` or `set_mode_from_recipe()` also sets it (True for
  `BOTH`, False otherwise), and `end(BOTH)` clears it.
- `work_chamber` is the chamber the device reports as active. It is `None`
  when the fryer is idle, and always `None` on single-chamber fryers. Besides
  `update()`, a successful `WHOLE` start sets it to `WHOLE`, any other start
  clears a `WHOLE` value, and a successful `end(WHOLE)` or `end(BOTH)` clears
  it.

To cook both chambers, pass `chamber=AirFryerChamber.BOTH`. During a Sync
cook, `end()` with one chamber sends an end for that chamber only; use
`end(AirFryerChamber.BOTH)` to end both. During a whole-basket cook
(`work_chamber` is `WHOLE`), `end()` with the default `CHAMBER_1` ends the
whole basket.

## Cook modes

`cook_modes` lists each fryer's presets from the VeSync app, keyed by
`AirFryerCookModes` (from `pyvesync.const`). Each entry holds the mode string
the API uses, the preset's recipe ID and name, its default time and
temperatures, and its temperature limits. `get_cook_mode()` looks one up by
key or by API mode string.

| Fryer | Modes |
| --- | --- |
| CS137/CS158 | `CUSTOM` (Manual Cooking, the default), `STEAK`, `CHICKEN`, `SEAFOOD`, `BACON`, `VEGETABLES`, `ROOT_VEGETABLES`, `FROZEN`, `DESSERTS`, `SHRIMP`, `BREAD`, `FRENCH_FRIES` |
| CAF-DC601S | `AIRFRY` (default), `ROAST`, `BROIL`, `FROZEN`, `REHEAT`, `BAKE`, `DRY`, `PROOF`, `WARM` |
| CAF-P583S | `AIRFRY` (default), `BROIL`, `ROAST`, `BAKE`, `CHICKEN`, `STEAK`, `SEAFOOD`, `VEGETABLES`, `FRENCH_FRIES`, `FROZEN`, `REHEAT` |
| CAF-TF101S | `AIRFRY` (default), `ROAST`, `BAKE`, `GRILL`, `REHEAT`, `DRY` |
| CAF-TF102S | `AIRFRY` (default), `ROAST`, `BAKE`, `GRILL`, `REHEAT` |
| CAF-DC111S-AEU | `AIRFRY` (default), `BAKE`, `ROAST`, `GRILL`, `REHEAT`, `DRY`, `PROOF` |

`set_mode(..., cook_mode=...)` accepts an `AirFryerCookModes` key or the API
mode string, and sends that preset's recipe ID, name and type. With no `cook_mode`
it sends the fryer's default preset. `set_mode(cook_mode=...)` with a mode the
fryer does not have returns `False` without sending a request.

`set_mode_from_recipe()` sends the recipe's own `cook_mode` and checks its
temperature against that mode's limits, or the default mode's limits if the
fryer has no such mode.

```python
from pyvesync.const import AirFryerCookModes

# Bake exists on the CAF-DC601S, CAF-P583S, CAF-TF101S/TF102S and CAF-DC111S-AEU
await fryer.set_mode(1200, 330, temp_unit='f', cook_mode=AirFryerCookModes.BAKE)

# The preset at its app defaults, for set_mode_from_recipe()
recipe = fryer.get_mode_recipe(AirFryerCookModes.BAKE)
if recipe is not None:
    await fryer.set_mode_from_recipe(recipe)
```

## Temperature limits

Each cook mode has its own temperature range and step in both Celsius and
Fahrenheit, taken from the VeSync app. `temp_limits(cook_mode)` returns them
in the fryer's current `temp_unit`; with no mode, or a mode the fryer does
not have, it returns the default mode's limits.

```python
limits = fryer.temp_limits('Grill')  # CAF-TF101S/TF102S Grill
print(limits.min_temp, limits.max_temp, limits.step)
```

A requested temperature is rounded to the nearest multiple of its mode's
step, then checked against its mode's range. Off-step temperatures are
always rounded, never rejected. Rounding uses Python's `round()`, so a value exactly halfway
between two steps goes to the even multiple: with a 10° step, 395 becomes 400
but 385 becomes 380. A temperature outside the range makes the method return
`False` without sending a request.

`min_temp` and `max_temp` are the widest span across all of the fryer's
modes, for display. A temperature inside that span can still be outside the
range of the mode you cook with; check `temp_limits(cook_mode)` before
calling `set_mode()`. `temperature_step` is the default mode's step.

Only temperatures have per-mode limits. Cook times are checked only for the
minimum described under [Cooking](#cooking).

## Temperature units

The fryer's `temp_unit` comes from each `update()`. Before the first update it
is the device map's default for that model or region. Temperatures in the
state, and `cook_temp` passed to `set_mode()`, are in this unit.

Pass `temp_unit` to give `cook_temp` in another unit; pyvesync converts it to
the device unit before sending:

```python
await fryer.set_mode(600, 390, temp_unit='f')  # sent as 200 C on a Celsius fryer
```

`temp_unit` accepts a `TemperatureUnits` member or a string starting with
`c` or `f` (`'c'`, `'celsius'`, `'F'`, ...). Any other string makes the method
return `False` without sending a request.

A unit changed on the device between `update()` and a command is not
detected; call `update()` first if the unit may have changed.

pyvesync converts with the formula (`TemperatureUnits.to_celsius` /
`to_fahrenheit`) and then rounds to the cook mode's step. The VeSync app
instead pairs each mode's Celsius and Fahrenheit lists by position, so a
converted temperature can be one step away from what the app shows for the
same input. Pass `cook_temp` in the device's own unit to avoid conversion.

## API reference

::: pyvesync.devices.vesynckitchen
    options:
        show_root_heading: true
        members: false

::: pyvesync.devices.vesynckitchen.VeSyncAirFryer158
    options:
        show_root_heading: true
        members_order: source
        filters:
            - "!^_.*"

::: pyvesync.devices.vesynckitchen.VeSyncTurboBlazeFryer
    options:
        show_root_heading: true
        members_order: source
        filters:
            - "!^_.*"

::: pyvesync.devices.vesynckitchen.VeSyncDualBlazeFryer
    options:
        show_root_heading: true
        members_order: source
        filters:
            - "!^_.*"

::: pyvesync.devices.vesynckitchen.VeSyncDualAirFryer
    options:
        show_root_heading: true
        members_order: source
        filters:
            - "!^_.*"

::: pyvesync.base_devices.fryer_base.FryerState
    options:
        show_root_heading: true
        members_order: source
        filters:
            - "!^_.*"

::: pyvesync.base_devices.fryer_base.VeSyncFryer
    options:
        show_root_heading: true
        members_order: source
        filters:
            - "!^_.*"
