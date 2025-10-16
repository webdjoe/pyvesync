# VeSync Authentication Module

The VeSync Authentication Module provides a clean separation of authentication logic from the main VeSync class, offering improved maintainability, better error handling, and additional features like token persistence.

## Usage

Username and password must still be provided when instantiating the `VeSync` class, but a token can be loaded instead of logging in. If the loaded token is not valid, the `login()` method will be automatically called.

### Basic Username/Password Authentication

```python
import asyncio
from pyvesync import VeSync

async def main():
    with VeSync(username="example@mail.com", password="password") as manager:
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

The credentials needed are: `token`, `account_id`, `country_code`, and `region`.

```python
import asyncio
from pyvesync import VeSync

async def main():
    with VeSync(username="example@mail.com", password="password") as manager:
        # Load credentials from a dictionary
        credentials = {
            "token": "your_token_here",
            "account_id": "your_account_id_here",
            "country_code": "US",
            "region": "US"
        }
        success = await manager.set_credentials(**credentials)

        # Or load from a file
        await manager.load_credentials_from_file("path/to/credentials.json")

asyncio.run(main())
```

### Credential Storage

Credentials can be saved to a file or output as a json string. If no file path is provided the credentials will be saved to the users home directory as `.vesync_auth`.

The credentials file is a json file that has the keys `token`, `account_id`, `country_code`, and `region`.

```python
import asyncio
from pathlib import Path
from pyvesync import VeSync

async def main():
    token_file = Path.home() / ".vesync_token"

    with VeSync(username="example@mail.com", password="password") as manager:
        # Login and save credentials to file
        success = await manager.login(token_file_path=token_file)
        if success:
            # Save credentials to file
            manager.save_credentials(token_file)

            # Output credentials as json string
            print(manager.output_credentials())

            print("Login successful and credentials saved!")
        else:
            print("Login failed!")

asyncio.run(main())
```

For a full list of methods and attributes, refer to the [auth](development/auth_api.md) and [vesync](development/vesync_api.md) documentation.
