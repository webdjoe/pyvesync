# pyvesync testing script

This script can be used to test the function of the `pyvesync` library and log output to a file for better support with issues. It supports testing the library's functionality with various devices and configurations.

## Setup and Installation

### From Repository

1. Clone the repo branch `dev-2.0`:

```bash
git clone -b dev-2.0 --single-branch https://github.com/webdjoe/pyvesync.git
```

2. Navigate to the repository directory: `cd pyvesync`

Optionally create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Powershell use `venv\Scripts\activate.ps1`
   ```

3. Install the current branch:

   ```bash
   pip install -e .
   ```

4. Run the testing script:

   ```bash
   python testing_scripts/vs_console_script.py --email <your_email> --password <your_password> [optional arguments]
    ```

### Just the script

1. Create a directory and navigate to it:

   ```bash
   mkdir pyvesync_testing
   cd pyvesync_testing
   ```

2. Create a virtual environment:

   ```bash
    python -m venv venv
    source venv/bin/activate  # On Powershell use `venv\Scripts\activate.ps1`
    ```

3. Install the `pyvesync` library branch `dev-2.0`:

   ```bash
   pip install git+https://github.com/webdjoe/pyvesync.git@dev-2.0
   ```

4. Download the `vs_console_script.py` file from the `testing_scripts` directory of the repository and place it in your current directory using a browser or `wget`/`curl` command:

   ```bash
   wget https://raw.githubusercontent.com/webdjoe/pyvesync/dev-2.0/testing_scripts/vs_console_script.py
   ```

5. Run the testing script:

   ```bash
    python vs_console_script.py --email <your_email> --password <your_password> [optional arguments]
    ```

### Running in VS Code or other IDE's

The script can be run directly in an IDE like Visual Studio Code. Open the `vs_console_script.py` file and edit the `USERNAME` and `PASSWORD` variables at the top of the file with your VeSync account credentials, along with any other . Then run the script using the IDE's debug command.

## Configuration

**WARNING**: The script will try to return the device to original state after testing, but it is not guaranteed to restore all states.

You can configure the script by modifying the following variables in the `vs_console_script.py` file:

- `USERNAME`: Your VeSync account email.
- `PASSWORD`: Your VeSync account password.
- `TEST_DEVICES`: Set to `True` to test device functionality.
- `TEST_TIMERS`: Set to `True` to test timer functionality.
- `OUTPUT_FILE`: Path to the output file for logging.
- `TEST_DEV_TYPE`: Specific device type to test (Options are  "bulbs", "switchs", "outlets", "humidifiers", "air_purifiers", "fans").

CONFIGURING VIA COMMAND LINE:

You can also configure the script via command line arguments:

```bash
python vs_console_script.py --email <your_email> --password <your_password> [optional arguments]
```

## Logging

The script logs output to both the console and a file specified by the `OUTPUT_FILE` variable.
