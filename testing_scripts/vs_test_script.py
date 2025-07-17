"""Testing script for pyvesync library.

This script tests the functionality of the pyvesync library by
interacting with VeSync devices. It can be run from the command line or
in VS code. It supports testing devices, timers, and logging to a file.

Usage:
    python testing_scripts/vs_console_script.py \
            --email <your_email> \
            --password <your_password> \
            [--test_devices] \
            [--test_timers] \
            [--output-file <output_file>] \
            [--test_dev_type <device_type>]

By default, it will only log in, pull the device list, and update all devices. Using
the `--test_devices` flag will run device specific methods on all devices. The
`--test_timers` flag will run timer methods on all devices. To test a specific device
type, use the `--test_dev_type` flag with one of the following values: "bulbs",
"switches", "outlets", "humidifiers", "air_purifiers", "fans". If no device type
is specified, it will test all devices.

Example:
    The script can be debugged in an IDE by setting the USERNAME, PASSWORD and
    other arguments at the top of the file. This injects the values into the
    command line arguments. Command line arguments will override these values.
"""

import argparse
import sys
import random
from pathlib import Path
import asyncio
import logging
from typing import Literal

from pyvesync import VeSync
from pyvesync.const import PurifierModes
from pyvesync.base_devices import VeSyncBaseToggleDevice
from pyvesync.device_container import DeviceContainer


_T_DEVS = Literal["bulbs", "switchs", "outlets", "humidifiers", "air_purifiers", "fans"]


# Manually configure script arguments
USERNAME: str | None = None
PASSWORD: str | None = None
TEST_DEVICES: bool | None = None
TEST_TIMERS: bool | None = None
OUTPUT_FILE: str | None = None
TEST_DEV_TYPE: _T_DEVS | None = None
# Set to a specific device type to test, e.g., "vesyncbulb", "vesyncswitch", etc.


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.info("Starting VeSync device test...")
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
logger.propagate = False


_SEP = "-" * 18
# Logging messages
_LOG_DEVICE_START = _SEP + " Testing %s %s " + _SEP
_LOG_DEVICE_END = _SEP + " Finished testing %s %s " + _SEP


async def _random_await() -> None:
    await asyncio.sleep(random.randrange(10, 30) / 10)
    logger.info("Random await finished")


async def vesync_test(
    username: str, password: str, output_file: str, test_devices: bool = False,
    test_timers: bool = False, test_dev_type: _T_DEVS | None = None
) -> None:
    """Main function to test VeSync devices.

    Note:
        This will attempt to return the device to the original state,
        but it is not guaranteed. Timers may be cleared as well.

    Args:
        username (str): VeSync account email.
        password (str): VeSync account password.
        output_file (str): Path to the output file for logging.
        test_devices (bool): If True, run tests on devices.
        test_timers (bool): If True, run tests on timers.
        test_dev_type (_T_DEVS | None): Specific device type to test.

    """
    output_path = Path(output_file).resolve()
    if not output_path.parent.exists():
        logger.error("Output directory %s does not exist.", output_path.parent)
        return
    file_handler = logging.FileHandler(output_path)
    logger.addHandler(file_handler)

    # Instantiate VeSync object
    vs = await VeSync(username, password).__aenter__()
    # vs.debug = True  # Enable debug mode
    vs.verbose = True  # Enable verbose mode
    # vs.redact = True  # Redact sensitive information in logs
    vs.log_to_file(str(output_path), std_out=False)  # Log to specified file
    logger.info("VeSync instance created, logging to %s", output_path)
    # Login to VeSync account and check for success
    logger.info("Logging in to VeSync account...")
    success = await vs.login()
    if not success:
        logger.error("Login failed.")
        return
    logger.info("Login successful, pulling device list...")
    await _random_await()

    # Pull device list and update all devices
    await vs.update()
    await _random_await()
    logger.info("Device list pulled successfully.")

    # Run tests for outlets
    if vs.devices.outlets and (test_devices is True or test_dev_type == "outlets"):
        await outlets(vs, update=False)

    # Run tests for air purifiers
    if vs.devices.air_purifiers and (
        test_devices is True or test_dev_type == "air_purifiers"
    ):
        await air_purifiers(vs, update=False)

    # Run tests for humidifiers
    if vs.devices.humidifiers and (
        test_devices is True or test_dev_type == "humidifiers"
    ):
        await humidifiers(vs, update=False)

    # Run tests for bulbs
    if vs.devices.bulbs and (test_devices is True or test_dev_type == "bulbs"):
        await bulbs(vs, update=False)

    # Run tests for switches
    if vs.devices.switches and (test_devices is True or test_dev_type == "switches"):
        await switches(vs, update=False)

    # Test timers if requested
    if test_timers is True:
        await device_timers(vs.devices, update=False)

    await vs.__aexit__(None, None, None)  # Clean up VeSync instance
    logger.info("Finished testing VeSync devices, results logged to %s", output_path)


async def common_tests(
    device: VeSyncBaseToggleDevice, update: bool = False
) -> bool | None:
    """Run common tests for a VeSync device."""
    logger.info(_LOG_DEVICE_START, device.device_type, device.device_name)
    logger.info(device)

    if update is True:
        await device.update()
        await _random_await()

    if device.state.connection_status == "offline":
        logger.info("%s is offline, skipping", device.device_name)
        return None

    logger.info("Current device state: %s", device.state.to_json(indent=True))

    if device.state.device_status == "off":
        logger.info("Initial state is off, turning on device")
        await device.turn_on()
        logger.info(device.state.device_status)
        await _random_await()
        return False

    logger.info("Initial state is on, turning off device")
    await device.turn_off()
    logger.info(device.state.device_status)
    await _random_await()

    logger.info("Turning on device")
    await device.turn_on()
    logger.info(device.state.device_status)
    await _random_await()
    return True


async def device_timers(dev_list: DeviceContainer, update: bool = False) -> None:
    """Test timers for all devices in the device list."""
    # Get dev types from device list to not repeat tests
    dev_types = [dev.device_type for dev in dev_list]
    dev_set = set(dev_types)

    for dev in dev_list:
        logger.info(
            "%s Testing timer for %s %s %s", _SEP, dev.device_type, dev.device_name, _SEP
        )

        if dev.device_type not in dev_set:
            continue
        dev_set.remove(dev.device_type)

        if update is True:
            await dev.update()
            await _random_await()

        await dev.get_timer()
        logger.info("Current timer state: %s", dev.state.timer)
        await _random_await()

        if dev.state.timer is None:
            logger.info("Setting timer for 1 hour to turn on device")
            await dev.set_timer(3600, 'on')
            logger.info("Current timer state: %s", dev.state.timer)
            await _random_await()

        logger.info("Updating device state after setting timer")
        await dev.update()
        logger.info("Current timer state: %s", dev.state.timer)
        await _random_await()

        logger.info("Getting current active timer via API")
        await dev.get_timer()
        logger.info("Current timer state: %s", dev.state.timer)
        await _random_await()

        logger.info("Clearing timer")
        await dev.clear_timer()
        logger.info("Current timer state: %s", dev.state.timer)
        await _random_await()

        logger.info(
            "%s Finished testing timer for %s %s %s",
            _SEP,
            dev.device_type,
            dev.device_name,
            _SEP,
        )


async def humidifiers(manager: VeSync, update: bool = False) -> None:
    """Test humidifiers in the VeSync device manager."""
    logger.info("%s Testing humidifiers %s", _SEP, _SEP)
    dev_types = set()
    for dev in manager.devices.humidifiers:
        # Ensure the same device type is not tested multiple times
        if dev.device_type in dev_types:
            continue
        dev_types.add(dev.device_type)

        initial_on = await common_tests(dev, update)
        if initial_on is None:
            continue

        logger.info(dev.state.to_json(indent=True))
        initial_state = dev.state.to_dict()
        logger.debug("Initial state: %s", dev.state.to_json(indent=True))

        logger.info("Setting state to auto mode")
        await dev.set_auto_mode()
        logger.debug(dev.state.mode)
        await _random_await()

        logger.info("Setting state to manual mode")
        await dev.set_manual_mode()
        logger.debug(dev.state.mode)
        await _random_await()

        logger.info("Setting mist level to 2")
        await dev.set_mist_level(2)
        logger.debug("mist_level: %s", dev.state.mist_level)
        logger.debug("mist_virtual_level: %s", dev.state.mist_virtual_level)
        await _random_await()

        logger.info("Setting sleep mode")
        await dev.set_sleep_mode()
        logger.debug(dev.state.mode)
        await _random_await()

        logger.info("Setting target humidity to 50%")
        await dev.set_humidity(50)
        logger.debug(dev.state.target_humidity)
        await _random_await()

        if initial_on is True:
            logger.info("Returning to initial state")
            await dev.set_mist_level(initial_state['mist_level'])
            await dev.set_mode(initial_state['mode'])
            await dev.set_humidity(initial_state['target_humidity'])
        else:
            await dev.turn_off()
        await _random_await()


async def bulbs(manager: VeSync, update: bool = False) -> None:
    """Test bulbs in the VeSync device manager."""
    logger.info("%s Testing bulbs %s", _SEP, _SEP)
    dev_types = set()
    for dev in manager.devices.bulbs:
        if dev.device_type in dev_types:
            continue
        dev_types.add(dev.device_type)

        initial_on = await common_tests(dev, update)
        if initial_on is None:
            continue

        initial_state = dev.state.to_dict()
        logger.info(dev.state.to_json(indent=True))

        # Print the current state of the device
        if dev.supports_brightness:
            logger.info("Setting brightness to 30%")
            await dev.set_brightness(30)
            logger.debug("Brightness: %s", dev.state.brightness)
            await _random_await()

        if dev.supports_color_temp:
            logger.info("Setting color temperature to 10")
            await dev.set_color_temp(10)
            logger.debug("Color Temperature: %s", dev.state.color_temp)
            await _random_await()

        if dev.supports_multicolor:
            logger.info("Setting RGB color to (255, 40, 30)")
            await dev.set_rgb(255, 40, 30)
            logger.debug("Color: %s", dev.state.rgb)
            await _random_await()

        logger.info("Returning to initial state")
        if initial_on is False:
            await dev.turn_off()
            await _random_await()
            return

        if initial_state['color_temp'] is not None:
            await dev.set_color_temp(initial_state['color_temp'])
        if initial_state['brightness'] is not None:
            await dev.set_brightness(initial_state['brightness'])
        if initial_state['rgb'] is not None:
            await dev.set_rgb(
                initial_state["rgb"][0],
                initial_state["rgb"][1],
                initial_state["rgb"][2],
            )

        await _random_await()


async def switches(manager: VeSync, update: bool = False) -> None:
    """Test switches in the VeSync device manager."""
    logger.info("%s Testing switches %s", _SEP, _SEP)
    dev_types = set()
    for dev in manager.devices.switches:
        if dev.device_type in dev_types:
            continue
        dev_types.add(dev.device_type)

        initial_on = await common_tests(dev, update)
        if initial_on is None:
            continue

        logger.debug(dev.state.to_json(indent=True))
        initial_state = dev.state.to_dict()

        if dev.supports_dimmable:
            logger.debug("Setting brightness to 100%")
            await dev.set_brightness(100)
            logger.debug(dev.state.brightness)
            await _random_await()

        if dev.supports_indicator_light:
            if initial_state['indicator_status'] == "on":
                logger.debug("Initial state is on, turning off indicator light")
                await dev.turn_off_indicator_light()
                logger.debug("indicator_status: %s", dev.state.indicator_status)
                await _random_await()
                await dev.turn_on_indicator_light()
                logger.debug("indicator_status: %s", dev.state.indicator_status)
                await _random_await()
            else:
                logger.debug("Initial state is off, turning on indicator light")
                await dev.turn_on_indicator_light()
                logger.debug("indicator_status: %s", dev.state.indicator_status)
                await _random_await()
                await dev.turn_off_indicator_light()
                logger.debug("indicator_status: %s", dev.state.indicator_status)
                await _random_await()

        if dev.supports_backlight_color:
            if initial_state['backlight_status'] == "on":
                logger.debug("Initial state is on, turning off RGB backlight")
                await dev.turn_off_rgb_backlight()
                logger.debug("backlight_status: %s", dev.state.backlight_status)
                await _random_await()
            logger.debug("Turrning on RGB backlight")
            await dev.turn_on_rgb_backlight()
            logger.debug("backlight_status: %s", dev.state.backlight_status)
            await _random_await()

            logger.debug("Setting backlight color to (50, 30, 15)")
            await dev.set_backlight_color(50, 30, 15)
            logger.debug("backlight_color: %s", dev.state.backlight_color)
            await _random_await()

            if initial_state["backlight_status"] == "off":
                await dev.turn_off_rgb_backlight()
                await _random_await()
            else:
                await dev.set_backlight_color(
                    initial_state["backlight_color"][0],
                    initial_state["backlight_color"][1],
                    initial_state["backlight_color"][2],
                )
            await _random_await()

        if initial_state['brightness'] is not None:
            await dev.set_brightness(initial_state['brightness'])
            await _random_await()


async def air_purifiers(manager: VeSync, update: bool = False) -> None:
    """Test air purifiers in the VeSync device manager."""
    logger.info("%s Testing air purifiers %s", _SEP, _SEP)
    dev_types = set()
    for dev in manager.devices.air_purifiers:
        if dev.device_type in dev_types:
            continue
        dev_types.add(dev.device_type)

        initial_on = await common_tests(dev, update)
        if initial_on is None:
            continue

        logger.info(dev.state.to_json(indent=True))
        initial_state = dev.state.to_dict()

        if initial_state['display_set_state'] is True:
            logger.info("Turning off display")
            await dev.turn_off_display()
            logger.info("display_set_state: %s", dev.state.display_set_state)
            logger.info("display_status: %s", dev.state.display_status)
            await _random_await()
            logger.info("Turning on display")
            await dev.turn_on_display()
            logger.info("display_set_state: %s", dev.state.display_set_state)
            logger.info("display_status: %s", dev.state.display_status)
            await _random_await()
        else:
            logger.info("Display is off, turning on display")
            await dev.turn_on_display()
            logger.info("display_set_state: %s", dev.state.display_set_state)
            logger.info("display_status: %s", dev.state.display_status)
            await _random_await()
            logger.info("Turning off display")
            await dev.turn_off_display()
            logger.info("display_set_state: %s", dev.state.display_set_state)
            logger.info("display_status: %s", dev.state.display_status)
            await _random_await()

        if PurifierModes.AUTO in dev.modes:
            logger.info("Setting auto mode")
            await dev.set_auto_mode()
            logger.info("mode: %s", dev.state.mode)
            await _random_await()
        if PurifierModes.SLEEP in dev.modes:
            logger.info("Setting sleep mode")
            await dev.set_sleep_mode()
            logger.info("mode: %s", dev.state.mode)
            await _random_await()
        if PurifierModes.MANUAL in dev.modes:
            logger.info("Setting manual mode")
            await dev.set_manual_mode()
            logger.info("mode: %s", dev.state.mode)
            await _random_await()

        logger.info("Setting fan speed to 1")
        await dev.set_fan_speed(1)
        logger.info("fan_level: %s", dev.state.fan_level)
        await dev.set_fan_speed(initial_state['fan_level'])

        if initial_state['child_lock'] is True:
            logger.info("Turning off child lock")
            await dev.turn_off_child_lock()
            logger.info("child_lock: %s", dev.state.child_lock)
            await _random_await()
            await dev.turn_on_child_lock()
            await _random_await()
        else:
            logger.info("Turning on child lock")
            await dev.turn_on_child_lock()
            logger.info("child_lock: %s", dev.state.child_lock)
            await _random_await()
            await dev.turn_off_child_lock()
            await _random_await()

        if initial_on is False:
            logger.info("Turning off device")
            await dev.turn_off()
            await _random_await()
            return
        if initial_state['mode'] is not PurifierModes.MANUAL:
            await dev.set_mode(initial_state['mode'])
            await _random_await()


async def outlets(manager: VeSync, update: bool = False) -> None:
    """Test outlets in the VeSync device manager."""
    logger.info("%s Testing outlets %s", _SEP, _SEP)
    dev_types = set()
    for dev in manager.devices.outlets:
        if dev.device_type in dev_types:
            continue
        dev_types.add(dev.device_type)
        initial_on = await common_tests(dev, update)
        if initial_on is None:
            continue
        logger.info(dev.state.to_json(indent=True))
        initial_state = dev.state.to_dict()

        if dev.supports_nightlight:
            if initial_state['nightlight_status'] == "on":
                logger.info("Turning off nightlight")
                await dev.turn_off_nightlight()
                logger.info("nightlight_status: %s", dev.state.nightlight_status)
                await _random_await()
                await dev.turn_on_nightlight()
            else:
                logger.info("Turning on nightlight")
                await dev.turn_on_nightlight()
                logger.info("nightlight_status: %s", dev.state.nightlight_status)
                await _random_await()
                await dev.turn_off_nightlight()

        if dev.supports_energy:
            logger.info("Getting energy data")
            await dev.get_monthly_energy()
            await dev.get_weekly_energy()
            await dev.get_yearly_energy()
            logger.info("Energy usage: %s", dev.state.energy)
            logger.info("Power: %s", dev.state.power)
            logger.info("Voltage: %s", dev.state.voltage)
            if dev.state.monthly_history:
                logger.info("Monthly history: %s", dev.state.monthly_history.to_json())
            if dev.state.weekly_history:
                logger.info("Weekly history: %s", dev.state.weekly_history.to_json())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test pyvesync library and devices.",
        epilog="Run script with --help for more information.",
    )
    parser.add_argument("--email", default=USERNAME, help="Email for VeSync account")
    parser.add_argument(
        "--password", default=PASSWORD, help="Password for VeSync account"
    )
    parser.add_argument(
        "--test_devices",
        action="store_true",
        default=TEST_DEVICES,
        help="Include devices in test, default: False",
    )
    parser.add_argument(
        "--test_timers",
        action="store_true",
        default=TEST_TIMERS,
        help="Run tests on timers, default: False",
    )
    parser.add_argument(
        "--output-file",
        default="vesync.log",
        help="Relative or absolute path to output file",
    )
    parser.add_argument(
        "--test_dev_type",
        choices=[
            "bulbs", "switches", "outlets", "humidifiers", "air_purifiers", "fans"
        ],
        default=TEST_DEV_TYPE,
        help="Specific device type to test, e.g., 'bulbs', 'switches', etc.",
    )
    args = parser.parse_args()

    if args.email is None or args.password is None:
        logger.error(
            "Username and password must be provided"
            "via command line arguments or script variables."
        )
        sys.exit(1)

    asyncio.run(
        vesync_test(
            args.email,
            args.password,
            args.output_file,
            args.test_devices,
            args.test_timers,
            args.test_dev_type,
        )
    )
