# tasks.md — Stylistic & Small Consistency Fixes

Findings from a full audit of `src/pyvesync/` against the documented conventions
in [CLAUDE.md](CLAUDE.md) and
[docs/development/contributing.md](docs/development/contributing.md).

**How to work this list — per the [Contribution Rules](docs/development/contributing.md):**

- **One change per PR.** Each numbered group below is scoped to be a single,
  focused PR. Do not batch unrelated groups together.
- **Verify on real hardware before merge** any change marked ⚠️ — these alter
  request payloads, enum values, serialization, or device structure and can
  change runtime behavior. Sections 1–3 are documentation/lint-only and carry no
  runtime risk.
- Line numbers are approximate; confirm before editing.

---

## 1. Documentation inaccuracies (no runtime risk)

The docs describe classes/methods/paths that do not match the code.

- [ ] `docs/development/contributing.md:~306` — Binary-state naming table is
  **backwards**. Code uses `turn_on_<state>()` / `turn_off_<state>()`
  (e.g. `turn_on_child_lock`), not `turn_<state>_on()`. Fix the pattern and the
  examples. *(Note: this table was in the doc before this session's edits.)*
- [ ] `docs/development/index.md:23,39` — `VeSyncToggleDevice` → `VeSyncBaseToggleDevice`.
- [ ] `docs/development/index.md:114,141,180` — `pyvesync.data_models` / `data_models` folder → `pyvesync.models` / `models/`.
- [ ] `docs/development/index.md:280` — `get_outlet_config()` does not exist; use `device_map.get_device_config()` or remove the example.
- [ ] `docs/development/index.md:417,420` — `call_bypassv1_mixin` → `call_bypassv1_api`.
- [ ] `docs/development/index.md:429,432,445,466` — `process_bypassv1_response` → `process_bypassv1_result`.
- [ ] `docs/development/index.md:559,562,575,589` — `process_bypassv2_response` / `process_bypassv2_results` → `process_bypassv2_result`.
- [ ] `docs/development/index.md:37` — binary-state example `turn_on_power`/`turn_off_power` don't exist (power is `turn_on`/`turn_off`); use a named state example.
- [ ] `docs/development/index.md:205` vs `docs/pyvesync3.md:282` — one uses `.from_dict(response_bytes)`, the other `.from_json(response_bytes)`; input is bytes → both should use `from_json`.
- [ ] `docs/development/data_models.md:8` — `bypassv2_models` module → `bypass_models`.
- [ ] `docs/pyvesync3.md:51` — `outlet.dumps()` does not exist; use `outlet.to_json(state=True)` / `to_jsonb(state=True)`.
- [ ] `docs/pyvesync3.md:222,261` — `data_models` folder/import → `models`.
- [ ] `docs/pyvesync3.md:231` — list item `airfryer_models` links to `fryer_models`; relabel to `fryer_models`.
- [ ] `docs/usage.md:147` — `manager.outlets` → `manager.devices.outlets`.
- [ ] `docs/usage.md:154` — `manager.devices.purifiers` → `manager.devices.air_purifiers`.
- [x] `README.md:79` — `VeSyncFan` → `VeSyncFanBase`. *(Fixed, along with `VeSyncHumid`→`VeSyncHumidifier` and `VeSyncAir`→`VeSyncPurifier` on adjacent lines.)*
- [x] `README.md:83` — `VeSyncAirFryer` → `VeSyncFryer` (concrete: `VeSyncAirFryer158`).
- [x] `CLAUDE.md:~88` — `TestBase` mocks `async_call_api()`, not `call_api()`.
- [x] `CLAUDE.md:~39` vs `docs/development/contributing.md:~344` — tox env mapping for `lint`/`pylint`/`flake8` disagrees; reconcile both against `tox.ini`. *(CLAUDE.md fixed; contributing.md was already correct.)*
- [ ] **Missing docs** — `src/pyvesync/vesynchome.py` and `src/pyvesync/models/home_models.py` (home/room grouping, WIP) are undocumented in CLAUDE.md "Key modules" / index.md / data_models.md. Add a note or document them.

## 2. In-code docstring corrections (no runtime risk)

- [ ] `base_devices/fryer_base.py:1` — module docstring is `"""Air Purifier Base Class."""` → `"""Air Fryer Base Class."""`.
- [ ] `base_devices/humidifier_base.py:192` — `Return:` → `Returns:` (Google style) in `drying_mode_seconds_remaining`.
- [ ] `base_devices/bulb_base.py:274` — docstring types `brightness` as `NUMERIC_T`; signature is `int`.
- [ ] `base_devices/humidifier_base.py:547` — `toggle_drying_mode` summary not a capitalized imperative sentence.
- [ ] `base_devices/purifier_base.py:276` — `supports_light_detection` uses `"""Returns True if..."""`; siblings use imperative `"""Return True if..."""`.
- [ ] `devices/vesyncpurifier.py:989` — `VeSyncAirRH131` docstring says "LV-PUR131S, using BypassV1 API" but class uses `BypassV2Mixin` (LV-PUR131S is `VeSyncAir131`).
- [ ] `devices/vesynchumidifier.py:233` — `automatic_stop_off` docstring says "...automatic stop **on**." but turns it off.
- [ ] `devices/vesyncbulb.py:757` — `_build_request` docstring documents a `method` arg that isn't in the signature.
- [ ] `devices/vesyncbulb.py:808` — `_call_valceno_api` Returns says `tuple[bytes, Any]`; returns `dict | None`.
- [ ] `utils/device_mixins.py:95` — `process_bypassv2_result` docstring opens "Process the Bypass **V1** API response."
- [ ] `utils/device_mixins.py:54,193,278` — Returns types wrong: `process_bypassv1_result` returns `T_MODEL | None` (doc says `dict`); `call_bypassv2_api`/`call_bypassv1_api` return `dict | None` (doc says `bytes`).
- [ ] `utils/errors.py:56` — `ResponseInfo` docstring types don't match fields (`error_type: str`, `code: int | None`).
- [ ] `utils/errors.py:90,111,750,755,870` — `ErrorTypes` docstring omits `TOKEN_ERROR`/`CROSS_REGION`; `ErrorInfo` should be `ResponseInfo`; `get_error_info` returns `ResponseInfo` (not `dict`); `raise_api_errors` Raises lists `VeSyncTokenError` which it never raises.
- [ ] `utils/helpers.py:150,563` — `model_maker` arg order/type mismatch; `parse_error_code` returns `ResponseInfo` (doc says `list[int]`).
- [ ] `utils/colors.py:170` — `Color.from_rgb` Args documented as `NUMERIC_STRICT`; signature is `float | None`.
- [ ] `utils/logs.py:1` — module docstring titled `library_logger.py` with a `from library_logger import ...` example; actual module is `pyvesync.utils.logs`.
- [ ] `const.py:374,655,678,859,888` — enum docstrings list non-existent members / omit real ones: `AirQualityLevel` (refs `AirQualityLevels`), `HumidifierModes` (`AUTOPRO`), `FanModes` (`ADVANCED_SLEEP` listed, `ECO` missing), `EnergyIntervals` (`DAILY/WEEKLY/MONTHLY/YEARLY` vs `WEEK/MONTH/YEAR`), `DryingModes` (`ON/OFF` vs `DONE/RUNNING/PAUSE`).
- [ ] `models/bulb_models.py:54,61` — `RequestESL100Status`/`RequestESL100Brightness` both docstring'd "...bulb details." (copy-paste).
- [ ] `models/purifier_models.py:225,232` — `RequestPurifier131Mode`/`Level` reuse "Purifier 131 Request Dict." verbatim.
- [ ] `models/fan_models.py:46,56` — `FanTowerSleepPreferences`/`FanPedestalSleepPreferences` reuse base docstring verbatim.
- [ ] `models/home_models.py:33,75` — `RequestHomeModel`/`RequestHomeInfoModel` docstrings claim they inherit `RequestVeSyncInstanceMixin`; they inherit `RequestBaseModel`.
- [ ] `device_map.py:157,239,269,1117` — `OutletMap` re-lists attrs twice & omits `energy_intervals`; `FanMap.modes` doc `list[str]` vs field `dict[str,str]`; `HumidifierMap` mist-level doc types vs `list[int]`; `full_device_list` docstring vs actual contents (missing outlet/switch/bulb modules).
- [ ] `vesync.py:217,308,383` — `redact` property docstring says "debug flag"; `get_devices()` docstring says returns a tuple (returns `bool`); `update()` docstring references non-existent `outlets`/`switches`/`_device_list` attributes.
- [ ] `auth.py:49` — class docstring Note references `token_file_path` / token-auth constructor args that don't exist.
- [ ] `vesynchome.py:87` — `build_homes` docstring claims it populates `manager.homes`; it doesn't (WIP). Soften or implement.

## 3. Style & type-hint consistency (low / no runtime risk)

- [ ] ⚠️(public rename) `base_devices/thermostat_base.py:181` — method `set_fan_ciruclate` is misspelled → `set_fan_circulate`. Check callers/tests; it's a public method.
- [ ] `_LOGGER` → `logger` (documented module-logger name) in: `base_devices/thermostat_base.py`, `devices/vesyncpurifier.py`, `devices/vesyncswitch.py`, `devices/vesyncthermostat.py`, `utils/colors.py`, `utils/helpers.py`, `vesynchome.py` (update all call sites).
- [ ] Add generic state parameter to base-class declarations (bulb_base already does `[BulbState]`): `fan_base.py:134` `[FanState]`, `humidifier_base.py:218` `[HumidifierState]`, `outlet_base.py:147` `[OutletState]`, `purifier_base.py:209` `[PurifierState]`, `switch_base.py:103` `[SwitchState]`, `fryer_base.py:47` `[FryerState]`, `thermostat_base.py:120` `[ThermostatState]`.
- [ ] `base_devices/bulb_base.py:12` — move `HSV`, `RGB` (used only in annotations) into the `if TYPE_CHECKING:` block; keep `Color` at runtime.
- [ ] `base_devices/purifier_base.py:279` — `toggle_display(self, mode: bool)` param `mode` → `toggle` (matches sibling toggles).
- [ ] `base_devices/fan_base.py:138` — docstring line is 91 chars; wrap to ≤90.
- [ ] `device_map.py:101` — `T_MAPS` uses `Union[...]` with `# noqa: UP007`; switch to `|` union and drop the `typing.Union` import.
- [ ] `utils/errors.py:844` — `msg: None | str = None` → `msg: str | None = None`.
- [ ] `utils/helpers.py:241,297,312,329` — `keys: tuple[str]` should be `tuple[str, ...]` (variable-length).
- [ ] `utils/logs.py:334,595` — `log_api_status_error`/`error_mashumaro_response` build messages with f-strings then log; use %-style deferred formatting.
- [ ] `models/outlet_models.py:23` — remove unused `T = TypeVar('T', bound='RequestWHOGYearlyEnergy')`.
- [ ] `models/outlet_models.py:276` — `__post_serialize__` annotates `self` and uses bare `dict`; match `vesync_models.py:97` (`d: dict[Any, Any]`, no self annotation).
- [ ] `devices/vesyncoutlet.py:785,954-956` — camelCase state attrs `voltageUpperThreshold`, `protectionStatus`, `currentUpperThreshold` → snake_case (verify no external consumers first).
- [ ] `devices/vesyncpurifier.py:728`, `devices/vesyncthermostat.py:31` — add `__slots__ = ()` to match every sibling concrete device class (and document this class convention in CLAUDE.md/contributing.md).

## 4. ⚠️ Constant / magic-literal usage (verify runtime unchanged)

Replace hardcoded mode/status strings with the `const` enums. Confirm each
enum's `.value` equals the literal being replaced so payloads are unchanged;
device-behavior changes require hardware testing.

- [ ] `devices/vesyncpurifier.py:955` — `'online'` → `ConnectionStatus.ONLINE`.
- [ ] `devices/vesyncpurifier.py:892` — `'on'/'off'` → `DeviceStatus`.
- [ ] `devices/vesyncswitch.py:252,272` — `== 'off'` → `== DeviceStatus.OFF`.
- [ ] `devices/vesyncbulb.py:363` — `'status': 'on'` → `DeviceStatus.ON`.
- [ ] `devices/vesyncbulb.py:164,186,198,207-211` — hardcoded `'color'`/`'white'` color modes → new `const` enum.
- [ ] `devices/vesynchumidifier.py:357-360,387` — `'on'/'off'` + color-mode strings → `DeviceStatus`/const.
- [ ] `devices/vesyncoutlet.py:786` — `'on'/'off'` → `DeviceStatus`.
- [ ] `devices/vesynckitchen.py:56-61` — module-level constants (`REFRESH_INTERVAL`, `RECIPE_ID`, `RECIPE_TYPE`, `CUSTOM_RECIPE`, `COOK_MODE`) → move to `pyvesync.const`.
- [ ] `base_devices/purifier_base.py:399` — default `room_size: int = 800` → named `const` default.
- [ ] `auth.py:87,88,350,413`, `vesync.py:144,343,559,577,628` — hardcoded `'US'`/`'EU'` regions, `'en'` language, and API success code literal `0` → named `const` values.
- [ ] `device_map.py:781,802,1042,1044,1070,1079` — hardcoded mode strings `'autoPro'`/`'advancedSleep'` and API method names `'setTowerFanMode'`/`'setFanMode'` → `const`. **Related to §5**: the `HumidifierModes.AUTOPRO` / `FanModes.ADVANCED_SLEEP` members referenced in docstrings don't exist — add them, then use them here.
- [ ] `device_map.py:162` — `OutletMap.product_line` defaults to `ProductLines.WIFI_LIGHT` (mislabels outlets as lights); use the correct outlet product line.

## 5. ⚠️ Enum / const consistency (may change values — test)

- [ ] `const.py:683` — **`FanModes.MANUAL = 'normal'` silently aliases `NORMAL='normal'`.** Likely should be `'manual'`. `device_map.py` relies on these values — verify against a real fan before changing.
- [ ] `const.py:354` — `AirQualityLevel(Enum)` with hand-rolled `__int__`/`__str__` → `IntEnum` per convention.
- [ ] `const.py:667,704` — unify mode-enum bases: `FanModes` inherits `StrEnum` directly while `PurifierModes`/`HumidifierModes` use `Features`; thermostat enums mix `IntEnum` and `IntEnumMixin`.
- [ ] `const.py:88` — `ProductLines.SWITCHES = 'Switches'` casing inconsistent with lowercase-hyphenated siblings.
- [ ] `const.py:107` — class `IntFlag` shadows stdlib `enum.IntFlag`; rename (e.g. `NotSupportedIntFlag`).
- [ ] `const.py:923` — `DRYING_MODES` dict duplicates `DryingModes.__int__`/`from_int`; derive from the enum.

## 6. ⚠️ Model inheritance/config consistency (test serialization)

Several models bypass the shared base classes / config; normalizing them may
change serialization. Test round-trip (de)serialization after each change.

- [ ] `models/humidifier_models.py:53` — `BypassV2InnerErrorResult` missing `@dataclass`; also oddly named for the humidifier module (→ `HumidifierInnerErrorResult`).
- [ ] `models/humidifier_models.py:47` — `InnerHumidifierBaseResult.Config`/module docstring claim discriminator subclassing but none is configured.
- [ ] Normalize base classes to `ResponseBaseModel`/`RequestBaseModel` where siblings do:
  `bulb_models.py:22,139` · `outlet_models.py:56,70` · `purifier_models.py:68` · `switch_models.py:53` · `thermostat_models.py:40,48,63,95,117` · `fan_models.py:41,87,95` · `home_models.py:115-168`.
- [ ] `base_models.py:65,80` + `bypass_models.py:59,92` — `Config` inherits `BaseConfig` vs `BaseModelConfig` inconsistently and redundantly re-sets `orjson_options`; standardize on `BaseModelConfig`. Also apply/remove `# type: ignore[override]` on `Config` subclasses consistently.
- [ ] `models/bulb_models.py:91` + `thermostat_models.py` — field aliasing via `field(metadata=field_options(alias=...))` vs `Annotated[T, Alias(...)]` used in outlet/humidifier models; standardize on one.
- [ ] `models/vesync_models.py:172` — `traceId = str(DefaultValues.traceId())` evaluated at import; use `field(default_factory=DefaultValues.traceId)`.
- [ ] `models/home_models.py:41` — `RequestHomeModel` account/token/country fields should be `field(init=False)` (comment says so; sibling does it).
- [ ] `models/vesync_models.py:63,109` — `RespGetTokenResultModel`/`RespLoginTokenResultModel` use `Resp` abbreviation vs documented `Response...`.
- [ ] `models/home_models.py:115-168` — internal models named `IntResponse...Model` but module docstring documents `IntResp...Model`; align names or the documented prefix.

## 7. ⚠️ Structural / architecture (larger — separate PRs, real-device testing REQUIRED)

These touch request-building and device structure; each is its own PR and MUST
be verified on the physical device.

- [ ] `devices/vesyncbulb.py:674` — `VeSyncBulbValcenoA19MC` uses no API mixin and re-implements request machinery (`_build_request`, `_call_valceno_api`); should use the appropriate Bypass mixin.
- [ ] `devices/vesynckitchen.py:331` — `VeSyncAirFryer158` uses no API mixin and defines request machinery on the concrete class.
- [ ] `devices/vesynckitchen.py:64` — `AirFryer158138State` (a `DeviceState` subclass) is defined in `devices/`; per docs it belongs in `base_devices/`.
- [ ] `devices/vesynchumidifier.py:879` — `VeSyncHumid1000S.toggle_display` hand-builds the request instead of calling `call_bypassv2_api`.
- [ ] `base_devices/purifier_base.py:282` — `toggle_display` raises `NotImplementedError`, breaking the subsystem's unimplemented-stub pattern (log + `return False`). Either conform or document `NotImplementedError` as intended.

## 8. Potential logic bugs (NOT stylistic — investigate; test before fixing)

Surfaced during the audit. Beyond the "stylistic" scope but worth tracking.

- [ ] `device_container.py:49` — `_clean_string` regex `r'[^a0zA-Z0-9]'` — `a0z` is almost certainly a typo for `a-z`, so most lowercase letters are stripped during fuzzy name matching.
- [ ] `device_container.py:287` — `if self.device_exists(...) not in self._data:` compares a `bool` (return of `device_exists`) against the device set — likely not the intended membership check.
- [ ] `base_devices/vesyncbasedevice.py:228-234` — `set_state` does `setattr(self, ...)` (on the device) while `get_state` reads `self.state` — asymmetric; confirm intended.

---

### Undocumented conventions worth adding to CLAUDE.md / contributing.md

- Concrete device classes define `__slots__ = ()` (see §3 for two that omit it).
- Unimplemented base-class methods follow a stub pattern: `del <args>`, a
  `logger.debug/warning` distinguishing "not supported" vs "not configured", then
  `return False` (see §7 purifier exception).
- State classes expose `@property`/setter pairs backed by private `_`-prefixed
  slots with validation/derivation in the accessors.
