pyvesync [![build status](https://img.shields.io/pypi/v/pyvesync.svg)](https://pypi.python.org/pypi/pyvesync)
========


pyvesync is a library to manage Etekcity Switches.


Installation
------------

Install the latest version from pip:

```python
pip install pyvesync
```


Usage
-----

To start with the module:

```python
from pyvesync.vesync import VeSync

manager = VeSync("USERNAME", "PASSWORD")
manager.login()
manager.update()

for switch in manager.devices:
    print("Turning on switch '%s'" % (switch.device_name))
    switch.turn_on()
```


Notes
-----

VeSync switches controlled through the Etekcity api do not always respond to the initial request for turn_on() and turn_off(). Retrying once or twice as needed often works.
