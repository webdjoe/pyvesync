# pyvesync [![build status](https://img.shields.io/pypi/v/pyvesync.svg)](https://pypi.python.org/pypi/pyvesync) [![Build Status](https://dev.azure.com/webdjoe/pyvesync/_apis/build/status/webdjoe.pyvesync?branchName=master)](https://dev.azure.com/webdjoe/pyvesync/_build/latest?definitionId=4&branchName=master) [![Open Source? Yes!](https://badgen.net/badge/Open%20Source%20%3F/Yes%21/blue?icon=github)](https://github.com/Naereen/badges/) [![PyPI license](https://img.shields.io/pypi/l/ansicolortags.svg)](https://pypi.python.org/pypi/ansicolortags/) <!-- omit in toc -->

pyvesync is a library to manage VeSync compatible [smart home devices](#supported-devices)

<a href="https://webdjoe.github.io/pyvesync/latest"><svg width="220" height="40" viewBox="0 0 247 48" fill="none" xmlns="http://www.w3.org/2000/svg">
<rect width="247" height="48" rx="4" fill="#009FFF"/>
<path d="M33.75 14.25C30.5808 14.2636 28.2248 14.7 26.52 15.4542C25.2478 16.0167 24.75 16.4423 24.75 17.8842V33C26.6986 31.2422 28.4278 30.75 35.25 30.75V14.25H33.75ZM14.25 14.25C17.4192 14.2636 19.7752 14.7 21.48 15.4542C22.7522 16.0167 23.25 16.4423 23.25 17.8842V33C21.3014 31.2422 19.5722 30.75 12.75 30.75V14.25H14.25Z" fill="white"/>
<path d="M57.248 15.3195C59.024 15.3195 60.576 15.6635 61.904 16.3515C63.248 17.0235 64.28 17.9995 65 19.2795C65.736 20.5435 66.104 22.0235 66.104 23.7195C66.104 25.4155 65.736 26.8875 65 28.1355C64.28 29.3835 63.248 30.3435 61.904 31.0155C60.576 31.6715 59.024 31.9995 57.248 31.9995H51.8V15.3195H57.248ZM57.248 29.7675C59.2 29.7675 60.696 29.2395 61.736 28.1835C62.776 27.1275 63.296 25.6395 63.296 23.7195C63.296 21.7835 62.776 20.2715 61.736 19.1835C60.696 18.0955 59.2 17.5515 57.248 17.5515H54.536V29.7675H57.248ZM74.5516 32.2155C73.3036 32.2155 72.1756 31.9355 71.1676 31.3755C70.1596 30.7995 69.3676 29.9995 68.7916 28.9755C68.2156 27.9355 67.9276 26.7355 67.9276 25.3755C67.9276 24.0315 68.2236 22.8395 68.8156 21.7995C69.4076 20.7595 70.2156 19.9595 71.2396 19.3995C72.2636 18.8395 73.4076 18.5595 74.6716 18.5595C75.9356 18.5595 77.0796 18.8395 78.1036 19.3995C79.1276 19.9595 79.9356 20.7595 80.5276 21.7995C81.1196 22.8395 81.4156 24.0315 81.4156 25.3755C81.4156 26.7195 81.1116 27.9115 80.5036 28.9515C79.8956 29.9915 79.0636 30.7995 78.0076 31.3755C76.9676 31.9355 75.8156 32.2155 74.5516 32.2155ZM74.5516 29.8395C75.2556 29.8395 75.9116 29.6715 76.5196 29.3355C77.1436 28.9995 77.6476 28.4955 78.0316 27.8235C78.4156 27.1515 78.6076 26.3355 78.6076 25.3755C78.6076 24.4155 78.4236 23.6075 78.0556 22.9515C77.6876 22.2795 77.1996 21.7755 76.5916 21.4395C75.9836 21.1035 75.3276 20.9355 74.6236 20.9355C73.9196 20.9355 73.2636 21.1035 72.6556 21.4395C72.0636 21.7755 71.5916 22.2795 71.2396 22.9515C70.8876 23.6075 70.7116 24.4155 70.7116 25.3755C70.7116 26.7995 71.0716 27.9035 71.7916 28.6875C72.5276 29.4555 73.4476 29.8395 74.5516 29.8395ZM83.2083 25.3755C83.2083 24.0155 83.4803 22.8235 84.0243 21.7995C84.5843 20.7595 85.3523 19.9595 86.3283 19.3995C87.3043 18.8395 88.4243 18.5595 89.6883 18.5595C91.2883 18.5595 92.6083 18.9435 93.6483 19.7115C94.7043 20.4635 95.4163 21.5435 95.7843 22.9515H92.8323C92.5923 22.2955 92.2083 21.7835 91.6803 21.4155C91.1523 21.0475 90.4883 20.8635 89.6883 20.8635C88.5683 20.8635 87.6723 21.2635 87.0003 22.0635C86.3443 22.8475 86.0163 23.9515 86.0163 25.3755C86.0163 26.7995 86.3443 27.9115 87.0003 28.7115C87.6723 29.5115 88.5683 29.9115 89.6883 29.9115C91.2723 29.9115 92.3203 29.2155 92.8323 27.8235H95.7843C95.4003 29.1675 94.6803 30.2395 93.6243 31.0395C92.5683 31.8235 91.2563 32.2155 89.6883 32.2155C88.4243 32.2155 87.3043 31.9355 86.3283 31.3755C85.3523 30.7995 84.5843 29.9995 84.0243 28.9755C83.4803 27.9355 83.2083 26.7355 83.2083 25.3755ZM110.487 18.7755V31.9995H107.751V30.4395C107.319 30.9835 106.751 31.4155 106.047 31.7355C105.359 32.0395 104.623 32.1915 103.839 32.1915C102.799 32.1915 101.863 31.9755 101.031 31.5435C100.215 31.1115 99.5669 30.4715 99.0869 29.6235C98.6229 28.7755 98.3909 27.7515 98.3909 26.5515V18.7755H101.103V26.1435C101.103 27.3275 101.399 28.2395 101.991 28.8795C102.583 29.5035 103.391 29.8155 104.415 29.8155C105.439 29.8155 106.247 29.5035 106.839 28.8795C107.447 28.2395 107.751 27.3275 107.751 26.1435V18.7755H110.487ZM130.105 18.5595C131.145 18.5595 132.073 18.7755 132.889 19.2075C133.721 19.6395 134.369 20.2795 134.833 21.1275C135.313 21.9755 135.553 22.9995 135.553 24.1995V31.9995H132.841V24.6075C132.841 23.4235 132.545 22.5195 131.953 21.8955C131.361 21.2555 130.553 20.9355 129.529 20.9355C128.505 20.9355 127.689 21.2555 127.081 21.8955C126.489 22.5195 126.193 23.4235 126.193 24.6075V31.9995H123.481V24.6075C123.481 23.4235 123.185 22.5195 122.593 21.8955C122.001 21.2555 121.193 20.9355 120.169 20.9355C119.145 20.9355 118.329 21.2555 117.721 21.8955C117.129 22.5195 116.833 23.4235 116.833 24.6075V31.9995H114.097V18.7755H116.833V20.2875C117.281 19.7435 117.849 19.3195 118.537 19.0155C119.225 18.7115 119.961 18.5595 120.745 18.5595C121.801 18.5595 122.745 18.7835 123.577 19.2315C124.409 19.6795 125.049 20.3275 125.497 21.1755C125.897 20.3755 126.521 19.7435 127.369 19.2795C128.217 18.7995 129.129 18.5595 130.105 18.5595ZM151.154 25.0635C151.154 25.5595 151.122 26.0075 151.058 26.4075H140.954C141.034 27.4635 141.426 28.3115 142.13 28.9515C142.834 29.5915 143.698 29.9115 144.722 29.9115C146.194 29.9115 147.234 29.2955 147.842 28.0635H150.794C150.394 29.2795 149.666 30.2795 148.61 31.0635C147.57 31.8315 146.274 32.2155 144.722 32.2155C143.458 32.2155 142.322 31.9355 141.314 31.3755C140.322 30.7995 139.538 29.9995 138.962 28.9755C138.402 27.9355 138.122 26.7355 138.122 25.3755C138.122 24.0155 138.394 22.8235 138.938 21.7995C139.498 20.7595 140.274 19.9595 141.266 19.3995C142.274 18.8395 143.426 18.5595 144.722 18.5595C145.97 18.5595 147.082 18.8315 148.058 19.3755C149.034 19.9195 149.794 20.6875 150.338 21.6795C150.882 22.6555 151.154 23.7835 151.154 25.0635ZM148.298 24.1995C148.282 23.1915 147.922 22.3835 147.218 21.7755C146.514 21.1675 145.642 20.8635 144.602 20.8635C143.658 20.8635 142.85 21.1675 142.178 21.7755C141.506 22.3675 141.106 23.1755 140.978 24.1995H148.298ZM160.519 18.5595C161.559 18.5595 162.487 18.7755 163.303 19.2075C164.135 19.6395 164.783 20.2795 165.247 21.1275C165.711 21.9755 165.943 22.9995 165.943 24.1995V31.9995H163.231V24.6075C163.231 23.4235 162.935 22.5195 162.343 21.8955C161.751 21.2555 160.943 20.9355 159.919 20.9355C158.895 20.9355 158.079 21.2555 157.471 21.8955C156.879 22.5195 156.583 23.4235 156.583 24.6075V31.9995H153.847V18.7755H156.583V20.2875C157.031 19.7435 157.599 19.3195 158.287 19.0155C158.991 18.7115 159.735 18.5595 160.519 18.5595ZM172.625 21.0075V28.3275C172.625 28.8235 172.737 29.1835 172.961 29.4075C173.201 29.6155 173.601 29.7195 174.161 29.7195H175.841V31.9995H173.681C172.449 31.9995 171.505 31.7115 170.849 31.1355C170.193 30.5595 169.865 29.6235 169.865 28.3275V21.0075H168.305V18.7755H169.865V15.4875H172.625V18.7755H175.841V21.0075H172.625ZM177.451 25.3275C177.451 23.9995 177.723 22.8235 178.267 21.7995C178.827 20.7755 179.579 19.9835 180.523 19.4235C181.483 18.8475 182.539 18.5595 183.691 18.5595C184.731 18.5595 185.635 18.7675 186.403 19.1835C187.187 19.5835 187.811 20.0875 188.275 20.6955V18.7755H191.035V31.9995H188.275V30.0315C187.811 30.6555 187.179 31.1755 186.379 31.5915C185.579 32.0075 184.667 32.2155 183.643 32.2155C182.507 32.2155 181.467 31.9275 180.523 31.3515C179.579 30.7595 178.827 29.9435 178.267 28.9035C177.723 27.8475 177.451 26.6555 177.451 25.3275ZM188.275 25.3755C188.275 24.4635 188.083 23.6715 187.699 22.9995C187.331 22.3275 186.843 21.8155 186.235 21.4635C185.627 21.1115 184.971 20.9355 184.267 20.9355C183.563 20.9355 182.907 21.1115 182.299 21.4635C181.691 21.7995 181.195 22.3035 180.811 22.9755C180.443 23.6315 180.259 24.4155 180.259 25.3275C180.259 26.2395 180.443 27.0395 180.811 27.7275C181.195 28.4155 181.691 28.9435 182.299 29.3115C182.923 29.6635 183.579 29.8395 184.267 29.8395C184.971 29.8395 185.627 29.6635 186.235 29.3115C186.843 28.9595 187.331 28.4475 187.699 27.7755C188.083 27.0875 188.275 26.2875 188.275 25.3755ZM197.82 21.0075V28.3275C197.82 28.8235 197.932 29.1835 198.156 29.4075C198.396 29.6155 198.796 29.7195 199.356 29.7195H201.036V31.9995H198.876C197.644 31.9995 196.7 31.7115 196.044 31.1355C195.388 30.5595 195.06 29.6235 195.06 28.3275V21.0075H193.5V18.7755H195.06V15.4875H197.82V18.7755H201.036V21.0075H197.82ZM204.95 17.0235C204.454 17.0235 204.038 16.8555 203.702 16.5195C203.366 16.1835 203.198 15.7675 203.198 15.2715C203.198 14.7755 203.366 14.3595 203.702 14.0235C204.038 13.6875 204.454 13.5195 204.95 13.5195C205.43 13.5195 205.838 13.6875 206.174 14.0235C206.51 14.3595 206.678 14.7755 206.678 15.2715C206.678 15.7675 206.51 16.1835 206.174 16.5195C205.838 16.8555 205.43 17.0235 204.95 17.0235ZM206.294 18.7755V31.9995H203.558V18.7755H206.294ZM215.622 32.2155C214.374 32.2155 213.246 31.9355 212.238 31.3755C211.23 30.7995 210.438 29.9995 209.862 28.9755C209.286 27.9355 208.998 26.7355 208.998 25.3755C208.998 24.0315 209.294 22.8395 209.886 21.7995C210.478 20.7595 211.286 19.9595 212.31 19.3995C213.334 18.8395 214.478 18.5595 215.742 18.5595C217.006 18.5595 218.15 18.8395 219.174 19.3995C220.198 19.9595 221.006 20.7595 221.598 21.7995C222.19 22.8395 222.486 24.0315 222.486 25.3755C222.486 26.7195 222.182 27.9115 221.574 28.9515C220.966 29.9915 220.134 30.7995 219.078 31.3755C218.038 31.9355 216.886 32.2155 215.622 32.2155ZM215.622 29.8395C216.326 29.8395 216.982 29.6715 217.59 29.3355C218.214 28.9995 218.718 28.4955 219.102 27.8235C219.486 27.1515 219.678 26.3355 219.678 25.3755C219.678 24.4155 219.494 23.6075 219.126 22.9515C218.758 22.2795 218.27 21.7755 217.662 21.4395C217.054 21.1035 216.398 20.9355 215.694 20.9355C214.99 20.9355 214.334 21.1035 213.726 21.4395C213.134 21.7755 212.662 22.2795 212.31 22.9515C211.958 23.6075 211.782 24.4155 211.782 25.3755C211.782 26.7995 212.142 27.9035 212.862 28.6875C213.598 29.4555 214.518 29.8395 215.622 29.8395ZM231.863 18.5595C232.903 18.5595 233.831 18.7755 234.647 19.2075C235.479 19.6395 236.127 20.2795 236.591 21.1275C237.055 21.9755 237.287 22.9995 237.287 24.1995V31.9995H234.575V24.6075C234.575 23.4235 234.279 22.5195 233.687 21.8955C233.095 21.2555 232.287 20.9355 231.263 20.9355C230.239 20.9355 229.423 21.2555 228.815 21.8955C228.223 22.5195 227.927 23.4235 227.927 24.6075V31.9995H225.191V18.7755H227.927V20.2875C228.375 19.7435 228.943 19.3195 229.631 19.0155C230.335 18.7115 231.079 18.5595 231.863 18.5595Z" fill="white"/>
<rect x="50" y="35.9995" width="108" height="0.001" fill="white"/>
</svg></a>
**Check out the new [pyvesync documentation](https://webdjoe.github.io/pyvesync/) for usage and full API details.**

## Supported Product Types

1. Outlets
2. Switches
3. Fans
4. Air Purifiers
5. Humidifiers
6. Bulbs
7. Air Fryers
8. Thermostats

See the [supported devices](https://webdjoe.github.io/pyvesync/latest/supported_devices/) page for a complete list of supported devices and device types.

## What's new in pyvesync 3.0

**BREAKING CHANGES** - The release of pyvesync 3.0 comes with many improvements and new features, but as a result there are many breaking changes. The structure has been completely refactored, so please read through the README and thoroughly test before deploying.

The goal is to standardize the library across all devices to allow easier and consistent maintainability moving forward. The original library was created 8 years ago for supporting only a few outlets, it was not designed for supporting 20+ different devices.

Some of the changes are:

- Asynchronous network requests with aiohttp.
- Strong typing of all network requests and responses.
- Created base classes for all devices for easier `isinstance` checks.
- Separated the instantiated devices to a `DeviceContainer` class that acts as a mutable set with convenience methods.
- Standardized the API for all device to follow a common naming convention. No more devices with different names for the same functionality.
- Implemented custom exceptions and error (code) handling for API responses.
- `const` module to hold all library constants
- Built the `DeviceMap` class to hold the mapping and features of devices.
- COMING SOON: Use API to pull device modes and operating features.

See [pyvesync V3](https://webdjoe.github.io/pyvesync/latest/pyvesync3/) for more information on the changes.

### Asynchronous operation

Library is now asynchronous, using aiohttp as a replacement for requests. The `pyvesync.VeSync` class is an asynchronous context manager. A `aiohttp.ClientSession` can be passed or created internally.

```python
import asyncio
import aiohttp
from pyvesync.vesync import VeSync

async def main():
    async with VeSync("user", "password") as manager:
        await manager.login()  # Still returns true
        if not manager.enabled:
            print("Not logged in.")
            return
        await manager.get_devices() # Instantiates supported devices in device list
        await manager.update() # Updates the state of all devices

        # manager.devices is a DeviceContainer object
        # manager.devices.outlets is a list of VeSyncOutlet objects
        # manager.devices.switches is a list of VeSyncSwitch objects
        # manager.devices.fans is a list of VeSyncFan objects
        # manager.devices.bulbs is a list of VeSyncBulb objects
        # manager.devices.humidifiers is a list of VeSyncHumid objects
        # manager.devices.air_purifiers is a list of VeSyncAir objects
        # manager.devices.air_fryers is a list of VeSyncAirFryer objects
        # manager.devices.thermostats is a list of VeSyncThermostat objects

        for outlet in manager.devices.outlets:
            # The outlet object contain all action methods and static device attributes
            await outlet.update()
            await outlet.turn_off()
            outlet.display() # Print static device information, name, type, CID, etc.

            # State of object held in `device.state` attribute
            print(outlet.state)
            state_json = outlet.dumps() # Returns JSON string of device state
            state_bytes = orjson.dumps(outlet.state) # Returns bytes of device state

            # to view the response information of the last API call
            print(outlet.last_response)
            # Prints a ResponseInfo object containing error code,
            # and other response information


# Or use your own session
session = aiohttp.ClientSession()

async def main():
    async with VeSync("user", "password", session=session):
        await manager.login()
        await manager.update()



if __name__ == "__main__":
    asyncio.run(main())
```

If using `async with` is not ideal, the `__aenter__()` and `__aexit__()` methods need to be called manually:

```python
manager = VeSync(user, password)

await manager.__aenter__()

...

await manager.__aexit__(None, None, None)
```

pvesync will close the `ClientSession` that was created by the library on `__aexit__`. If a session is passed in as an argument, the library does not close it. If a session is passed in and not closed, aiohttp will generate an error on exit:

```text
2025-02-16 14:41:07 - ERROR - asyncio - Unclosed client session
2025-02-16 14:41:07 - ERROR - asyncio - Unclosed connector
```

### VeSync Class Signature

The VeSync signature is:

```python
VeSync(
    username: str,
    password: str,
    session: ClientSession | None = None,
    time_zone: str = DEFAULT_TZ  # America/New_York
    )
```

The VeSync class no longer accepts a `debug` or `redact` argument. To set debug the library set `manager.debug = True` to the instance and `manager.redact = True`.

### Product Types

There is a new nomenclature for product types that defines the device class. The
`device.product_type` attribute defines the product type based on the VeSync API. The product type is used to determine the device class and module. The currently supported product types are:

1. `outlet` - Outlet devices
2. `switch` - Wall switches
3. `fan` - Fans (not air purifiers or humidifiers)
4. `purifier` - Air purifiers (not humidifiers)
5. `humidifier` - Humidifiers (not air purifiers)
6. `bulb` - Light bulbs (not dimmers or switches)
7. `airfryer` - Air fryers

See [Supported Devices](#supported-devices) for a complete list of supported devices and models.

### Custom Exceptions

Exceptions are no longer caught by the library and must be handled by the user. Exceptions are raised by server errors and aiohttp connection errors.

Errors that occur at the aiohttp level are raised automatically and propogated to the user. That means exceptions raised by aiohttp that inherit from `aiohttp.ClientError` are propogated.

When the connection to the VeSync API succeeds but returns an error code that prevents the library from functioning a custom exception inherrited from `pyvesync.logs.VeSyncError` is raised.

Custom Exceptions raised by all API calls:

- `pyvesync.logs.VeSyncServerError` - The API connected and returned a code indicated there is a server-side error.
- `pyvesync.logs.VeSyncRateLimitError` - The API's rate limit has been exceeded.
- `pyvesync.logs.VeSyncAPIStatusCodeError` - The API returned a non-200 status code.
- `pyvesync.logs.VeSyncAPIResponseError` - The response from the API was not in an expected format.

Login API Exceptions

- `pyvesync.logs.VeSyncLoginError` - The username or password is incorrect.

See [errors](https://webdjoe.github.io/pyvesync/latest/development/utils/errors) documentation for a complete list of error codes and exceptions.

The [raise_api_errors()](https://webdjoe.github.io/pyvesync/latest/development/utils/errors/#pyvesync.utils.errors.raise_api_errors) function is called for every API call and checks for general response errors. It can raise the following exceptions:

- `VeSyncServerError` - The API connected and returned a code indicated there is a server-side error.
- `VeSyncRateLimitError` - The API's rate limit has been exceeded.
- `VeSyncAPIStatusCodeError` - The API returned a non-200 status code.
- `VeSyncTokenError` - The API returned a token error and requires `login()` to be called again.
- `VeSyncLoginError` - The user name or password is incorrect.

## Installation

Install the latest version from pip:

```bash
pip install pyvesync
```

<!--SUPPORTED DEVICES START-->

## Supported Devices

<!--SUPPORTED OUTLETS START-->

### Etekcity Outlets

1. Voltson Smart WiFi Outlet- Round (7A model ESW01-USA)
2. Voltson Smart WiFi Outlet - Round (10A model ESW01-EU)
3. Voltson Smart Wifi Outlet - Round (10A model ESW03-USA)
4. Voltson Smart Wifi Outlet - Round (10A model ESW10-USA)
5. Voltson Smart WiFi Outlet - Rectangle (15A model ESW15-USA)
6. Two Plug Outdoor Outlet (ESO15-TB) (Each plug is a separate `VeSyncOutlet` object, energy readings are for both plugs combined)

<!--SUPPORTED OUTLETS END-->

<!--SUPPORTED SWITCHES START-->

### Wall Switches

1. Etekcity Smart WiFi Light Switch (model ESWL01)
2. Etekcity Wifi Dimmer Switch (ESD16)

<!--SUPPORTED SWITCHES END-->

### Levoit Air Purifiers

1. LV-PUR131S
2. Core 200S
3. Core 300S
4. Core 400S
5. Core 600S
6. Vital 100S
7. Vital 200S
8. Everest Air

### Etekcity Bulbs

1. Soft White Dimmable Smart Bulb (ESL100)
2. Cool to Soft White Tunable Dimmable Bulb (ESL100CW)

### Valceno Bulbs

1. Valceno Multicolor Bulb (XYD0001)

### Levoit Humidifiers

1. Dual 200S
2. Classic 300S
3. LV600S
4. OasisMist 450S
5. OasisMist 600S
6. OasisMist 1000S

### Cosori Air Fryer

1. Cosori 3.7 and 5.8 Quart Air Fryer

### Fans

1. 42 in. Tower Fan

<!--SUPPORTED DEVICES END-->

## Usage

```python
import asyncio
from pyvesync import VeSync
from pyvesync.logs import VeSyncLoginError

# VeSync is an asynchronous context manager
# VeSync(username, password, debug=False, redact=True, session=None)

async def main():
    async with VeSync("user", "password") as manager:
        await manager.login()  # Still returns true
        await manager.update()

        # Acts as a set of device instances
        device_container = manager.devices

        outlets = device_container.outlets # List of outlet instances
        outlet = outlets[0]
        await outlet.update()
        await outlet.turn_off()
        outlet.display()

        # Iterate of entire device list
        for devices in device_container:
            device.display()


if __name__ == "__main__":
    asyncio.run(main())
```

Devices are stored in the respective lists in the instantiated `VeSync` class:

```python
await manager.login()  # Asynchronous
await manager.update()  # Asynchronous


# Acts as set with properties that return product type lists
manager.devices = DeviceContainer instance

manager.devices.outlets = [VeSyncOutletInstances]
manager.devices.switches = [VeSyncSwitchInstances]
manager.devices.fans = [VeSyncFanInstances]
manager.devices.bulbs = [VeSyncBulbInstances]
manager.devices.purifiers = [VeSyncPurifierInstances]
manager.devices.humidifiers = [VeSyncHumidifierInstances]
manager.devices.air_fryers = [VeSyncAirFryerInstances]
managers.devices.thermostats = [VeSyncThermostatInstances]

# Get device by device name
dev_name = "My Device"
for device in manager.devices:
  if device.device_name == dev_name:
    my_device = device
    device.display()

# Turn on switch by switch name
switch_name = "My Switch"
for switch in manager.devices.switches:
  if switch.device_name == switch_name:
    await switch.turn_on()   # Asynchronous
```

See the [device documentation](https://webdjoe.github.io/pyvesync/latest/devices/) for more information on the device classes and their methods/states.

## Debug mode and redact

To make it easier to debug, there is a `debug` argument in the `VeSync` method. This prints out your device list and any other debug log messages.

The `redact` argument removes any tokens and account identifiers from the output to allow for easier sharing. The `redact` argument has no impact if `debug` is not `True`.

```python
import asyncio
import aiohttp
from pyvesync.vesync import VeSync

async def main():
    async with VeSync("user", "password") as manager:
        manager.debug = True
        manager.redact = True  # True by default
        await manager.login()  # Still returns true
        await manager.update()

        outlet = manager.outlets[0]
        await outlet.update()
        await outlet.turn_off()
        outlet.display()


if __name__ == "__main__":
    asyncio.run(main())
```

## Feature Requests

Before filing an issue to request a new feature or device, please ensure that you will take the time to test the feature throuroughly. New features cannot be simply tested on Home Assistant. A separate integration must be created which is not part of this library. In order to test a new feature, clone the branch and install into a new virtual environment.

```bash
mkdir python_test && cd python_test

# Check Python version is 3.11 or higher
python3 --version # or python --version or python3.8 --version
# Create a new venv
python3 -m venv pyvesync-venv
# Activate the venv on linux
source pyvesync-venv/bin/activate
# or ....
pyvesync-venv\Scripts\activate.ps1 # on powershell
pyvesync-venv\Scripts\activate.bat # on command prompt

# Install branch to be tested into new virtual environment:
pip install git+https://github.com/webdjoe/pyvesync.git@BRANCHNAME

# Install a PR that has not been merged:
pip install git+https://github.com/webdjoe/pyvesync.git@refs/pull/PR_NUMBER/head
```

Test functionality with a script, please adjust methods and logging statements to the device you are testing.

`test.py`

```python
import asyncio
import sys
import logging
import json
from functool import chain
from pyvesync import VeSync

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

USERNAME = "YOUR USERNAME"
PASSWORD = "YOUR PASSWORD"

DEVICE_NAME = "Device" # Device to test

async def test_device():
    # Instantiate VeSync class and login
  async with VeSync(USERNAME, PASSWORD, debug=True, redact=True) as manager:
      login = await manager.login()

      # Pull and update devices
      await manager.update()

      for dev in manager.devices:
          # Print all device info
          logger.debug(dev.device_name + "\n")
          logger.debug(dev.display())

          # Find correct device
          if dev.device_name.lower() != DEVICE_NAME.lower():
              logger.debug("%s is not %s, continuing", self.device_name, DEVICE_NAME)
              continue

          logger.debug('--------------%s-----------------' % dev.device_name)
          logger.debug(dev.display())
          logger.debug(dev.displayJSON())
          # Test all device methods and functionality
          # Test Properties
          logger.debug("Fan is on - %s", dev.is_on)
          logger.debug("Modes - %s", dev.modes)
          logger.debug("Fan Level - %s", dev.fan_level)
          logger.debug("Fan Air Quality - %s", dev.air_quality)
          logger.debug("Screen Status - %s", dev.screen_status)

          logger.debug("Turning on")
          await fan.turn_on()
          logger.debug("Device is on %s", dev.is_on)

          logger.debug("Turning off")
          await fan.turn_off()
          logger.debug("Device is on %s", dev.is_on)

          logger.debug("Sleep mode")
          fan.sleep_mode()
          logger.debug("Current mode - %s", dev.details['mode'])

          fan.auto_mode()

          logger.debug("Set Fan Speed - %s", dev.set_fan_speed)
          logger.debug("Current Fan Level - %s", dev.fan_level)
          logger.debug("Current mode - %s", dev.mode)

          # Display all device info
          logger.debug(dev.display(state=True))
          logger.debug(dev.to_json(state=True, indent=True))
          dev_dict = dev.to_dict(state=True)

if __name__ == "__main__":
    logger.debug("Testing device")
    asyncio.run(test_device())
...

```

## Device Requests

SSL pinning makes capturing packets much harder. In order to be able to capture packets, SSL pinning needs to be disabled before running an SSL proxy. Use an Android emulator such as Android Studio, which is available for Windows and Linux for free. Download the APK from APKPure or a similiar site and use [Objection](https://github.com/sensepost/objection) or [Frida](https://frida.re/docs/gadget/). Followed by capturing the packets with Charles Proxy or another SSL proxy application.

Be sure to capture all packets from the device list and each of the possible device menus and actions. Please redact the `accountid` and `token` from the captured packets. If you feel you must redact other keys, please do not delete them entirely. Replace letters with "A" and numbers with "1", leave all punctuation intact and maintain length.

For example:

Before:

```json
{
  "tk": "abc123abc123==3rf",
  "accountId": "123456789",
  "cid": "abcdef12-3gh-ij"
}
```

After:

```json
{
  "tk": "AAA111AAA111==1AA",
  "accountId": "111111111",
  "cid": "AAAAAA11-1AA-AA"
}
```

## Contributing

All [contributions](CONTRIBUTING.md) are welcome.

This project is licensed under [MIT](LICENSE).
