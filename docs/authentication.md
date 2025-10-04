# VeSync Authentication Module

The VeSync Authentication Module provides a clean separation of authentication logic from the main VeSync class, offering improved maintainability, better error handling, and additional features like token persistence.

## Features

- **Flexible Authentication**: Support for both username/password and token-based authentication
- **Token Persistence**: Automatic saving and loading of authentication tokens to/from disk
- **Improved Error Handling**: More granular and descriptive error messages
- **Better Security**: Secure file permissions for token storage
- **Graceful Token Validation**: Automatic validation of existing tokens before use
- **Cross-Region Support**: Automatic handling of region changes during authentication

## Usage

### Basic Username/Password Authentication

```python
import asyncio
from pyvesync import VeSync

async def main():
    manager = VeSync(
        username="your_email@example.com",
        password="your_password",
        country_code="US"
    )

    # Login
    success = await manager.login()
    if success:
        print("Login successful!")
        # Use manager for device operations
        await manager.get_devices()
        await manager.update_all_devices()

    await manager.__aexit__()

asyncio.run(main())
```

### Token-Based Authentication

```python
import asyncio
from pyvesync import VeSync

async def main():
    # Use existing token (e.g., from previous login)
    manager = VeSync(
        token="your_existing_token",
        account_id="your_account_id",
        country_code="US"
    )

    # Login with token
    success = await manager.login()
    if success:
        print("Token authentication successful!")

    await manager.__aexit__()

asyncio.run(main())
```

### Persistent Token Storage

```python
import asyncio
from pathlib import Path
from pyvesync import VeSync

async def main():
    token_file = Path.home() / ".vesync_token"

    manager = VeSync(
        username="your_email@example.com",
        password="your_password",
        token_file_path=token_file
    )

    # First login saves token to file
    success = await manager.login()
    if success:
        print("Login successful! Token saved for future use.")

    # Subsequent runs will automatically load the saved token
    # and validate it before falling back to username/password

    await manager.__aexit__()

asyncio.run(main())
```

### Direct Authentication Management

```python
from pyvesync import VeSync

# Create manager without initial credentials
manager = VeSync()

# Set credentials programmatically
manager.auth.set_credentials(
    username="your_email@example.com",
    password="your_password"
)

# Check authentication state
print(f"Is authenticated: {manager.auth.is_authenticated}")
print(f"Username: {manager.auth.username}")

# Clear credentials
manager.auth.clear_credentials()
```

## Authentication Flow

The authentication process follows these steps:

1. **Token Validation**: If a token exists, validate it first
2. **Username/Password Login**: If no valid token, use credentials
3. **Authorization Code Exchange**: Get auth code, then exchange for token
4. **Cross-Region Handling**: Automatically handle region changes
5. **Token Persistence**: Save token to file if path is provided

## VeSyncAuth Class

The `VeSyncAuth` class handles all authentication logic:

### Properties

- `token`: Authentication token
- `account_id`: VeSync account ID
- `country_code`: Country code for the account
- `username`: Account username (read-only)
- `password`: Account password (read-only)
- `is_authenticated`: Boolean indicating if user is authenticated

### Methods

- `login()`: Perform authentication
- `set_credentials()`: Set authentication credentials
- `clear_credentials()`: Clear all stored credentials
- `get_auth_headers()`: Get headers for authenticated API requests
- `to_dict()`: Get authentication state as dictionary

## Migration from Old VeSync Class

The new authentication module is fully backward compatible. Existing code will continue to work:

```python
# Old way (still works)
manager = VeSync("user@example.com", "password")
await manager.login()

# New way (recommended)
manager = VeSync(
    username="user@example.com",
    password="password",
    token_file_path="~/.vesync_token"
)
await manager.login()
```

## Advanced Features

### Custom Token File Location

```python
from pathlib import Path

# Custom location
token_file = Path("/secure/location/vesync_token.json")
manager = VeSync(
    username="user@example.com",
    password="password",
    token_file_path=token_file
)
```

### Token-Only Authentication

```python
# For applications that manage tokens externally
manager = VeSync(
    token="externally_managed_token",
    account_id="known_account_id"
)
```

### Error Handling

```python
from pyvesync.utils.errors import VeSyncLoginError, VeSyncAPIResponseError

try:
    success = await manager.login()
except VeSyncLoginError as e:
    print(f"Login failed: {e}")
except VeSyncAPIResponseError as e:
    print(f"API error: {e}")
```

## Security Considerations

- Token files are created with restrictive permissions (0o600)
- Sensitive information is not included in string representations
- Credentials are cleared from memory when `clear_credentials()` is called
- Token validation prevents use of expired tokens

## Thread Safety

The authentication module is designed for use with asyncio and is not thread-safe. Use appropriate synchronization if accessing from multiple threads.