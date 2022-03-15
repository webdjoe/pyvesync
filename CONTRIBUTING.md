# Setting up the Development Environment

1. Git clone the repository

```
git clone https://github.com/webdjoe/pyvesync
```

2. Create and activate a separate python virtual environment for pyvesync

```
# Create a new venv
python3 -m venv pyvesync-venv
# Activate the venv
source pyvesync-venv/bin/activate
```

3. Install pyvesync in the venv

```
pip3 install -e pyvesync/
```

If the above steps were executed successfully, you should now have:

- Code directory `pyvesync`(which we cloned from github)
- Python venv directory `pyvesync` (all the dependencies/libraries are contained here)

Any change in the code will now be directly reflected and can be tested. To deactivate the python venv, simply
run `deactivate`.

# Testing Python with Tox

Install tox, navigate to the pyvesync repository which contains the tox.ini file, and run tox as follows:

```
pip install tox
cd pyvesync
tox
```

