# VeSync Authentication Module

The VeSync Authentication Module provides a clean separation of authentication logic from the main VeSync class, offering improved maintainability, better error handling, and additional features like token persistence.

## Usage

Username and password must still be provided when instantiating the `VeSync` class, but a token can be loaded instead of logging in. Loading a token does not validate it. If an API call is rejected because the token is invalid or expired, the library automatically re-authenticates with the username and password and repeats the call. If the credentials were loaded from a file, the new token is written back to that file. After repeated failed re-authentication attempts, a [`VeSyncTokenError`][pyvesync.utils.errors.VeSyncTokenError] is raised. A rejected username or password raises a [`VeSyncLoginError`][pyvesync.utils.errors.VeSyncLoginError].

### Basic Username/Password Authentication

```python
import asyncio
from pyvesync import VeSync

async def main():
    async with VeSync(username="example@mail.com", password="password") as manager:
        # Login
        success = await manager.login()
        if not success:
            print("Login failed!")
            return

        print("Login successful!")

asyncio.run(main())
```

### Loading authentication data

The authentication data can be provided to arguments of the `set_credentials()` or `load_credentials_from_file()` methods of the instantiated `VeSync` object.

The credentials needed are: `token`, `account_id`, `country_code`, and `region`. When loading from a file, the keys are `token`, `account_id`, `country_code`, and `current_region`. If no file path is passed to `load_credentials_from_file()`, `.vesync_auth` is read from the current working directory, then from the user's home directory.

```python
import asyncio
from pyvesync import VeSync

async def main():
    async with VeSync(username="example@mail.com", password="password") as manager:
        # Load credentials from a dictionary
        credentials = {
            "token": "your_token_here",
            "account_id": "your_account_id_here",
            "country_code": "US",
            "region": "US"
        }
        manager.set_credentials(**credentials)

        # Or load from a file
        await manager.load_credentials_from_file("path/to/credentials.json")

asyncio.run(main())
```

### Credential Storage

Credentials can be saved to a file or output as a json string. `manager.save_credentials()` requires a file path and does nothing if it is `None`. Calling `manager.auth.save_credentials_to_file()` without a path saves to the file the credentials were loaded from, or to `.vesync_auth` in the current working directory if none was loaded.

The credentials file is a json file that has the keys `token`, `account_id`, `country_code`, and `current_region`.

```python
import asyncio
from pathlib import Path
from pyvesync import VeSync

async def main():
    token_file = Path.home() / ".vesync_auth"

    async with VeSync(username="example@mail.com", password="password") as manager:
        # Login and save credentials to file
        success = await manager.login()
        if success:
            # Save credentials to file
            await manager.save_credentials(token_file)

            # Output credentials as json string
            print(manager.output_credentials_json())

            # Output credentials as dictionary
            print(manager.output_credentials_dict())

            print("Login successful and credentials saved!")
        else:
            print("Login failed!")

asyncio.run(main())
```

For a full list of methods and attributes, refer to the [auth](development/auth_api.md) and [vesync](development/vesync_api.md) documentation.
