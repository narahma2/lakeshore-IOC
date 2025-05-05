# lakeshore-IOC
EPICS soft IOC implementation for the LakeShore 336 temperature controller, tailored towards the in situ solar cell chamber created for the In Situ Nanoprobe (ISN) 19-ID beamline in the Advanced Photon Source (APS).

# Quick-Start
This installation requires a python environment, with setup done below using conda.

```shell
conda env create --file=environment.yml
conda activate lakeshore
```

To start up the IOC, run the python script:

```shell
python ./scripts/start_ioc.py
```

A .ui file (pictured above) is provided which can be integrated into your typical EPICS setup for interactive control of the associated PVs.

# PV List
The PVs served by this IOC follow a `LS336:XEOL:*`/`LS336:XEOL:*-RBV` template, where LS336:XEOL:* is the PV you can update with caput and LS336:XEOL:*-RBV is the current device setting that you can readback with caget.

A list of the relevant PVs is below (edit `start_ioc.py` to change the names as desired):

- `TSAMPLE_RBV` / `TCELL_RBV` / `TMOUNT_RBV`: Temperature of sample, cell, and mount sensors (read only)
- `TSET` / `TSET_RBV`: Setpoint temperature
- `STATUS` / `STATUS_RBV`: Heater setting
    - `True` (on) or `False` (off)
- `MODE` / `MODE_RBV`: Heater mode
    - `OFF`, `OPEN_LOOP`, `CLOSED_LOOP`
- `LOAD_RBV`: Heater load in closed loop operation
- `MANUAL_LOAD` / `MANUAL_LOAD_RBV`: Heater load in open loop operation
- `RAMP` / `RAMP_RBV`: Setpoint ramp rate
- `P` / `P_RBV`: Proportional value in PID setup
- `I` / `I_RBV`: Integral value in PID setup
- `D` / `D_RBV`: Derivative value in PID setup

# Script Configuration
Edit `start_ioc.py` as needed for your setup, most likely the following lines:

Line 12: update the IP address to what your LakeShore is set to
```python
ip = socket.gethostbyname('2idlakeshore336.xray.aps.anl.gov')
```

Line 17-18: update the output if your heater is not attached to output 3
```python
# Let's stick to output 3
output = 3
```

Line 55-56: update prefix if desired
```python
# Record prefix
builder.SetDeviceName('LS336:XEOL')
```

# Calibration Data
Calibration data for temperature sensors can be manually setup through the LakeShore front panel, however as that is tedious a python script is available to make this process much easier. This should only need to be run once:

```shell
python ./scripts/setup_lakeshore.py
```

The script may need to be updated based on your configuration.

Line 7: LakeShore IP address (if querying through the local network)
```python
ip = socket.gethostbyname('2idlakeshore336.xray.aps.anl.gov')
```

Lines 18-20: sensor input names (this is tailored towards the 19-ID in situ experiments):
```python
ls336.set_sensor_name('A', 'Sample Temp')
ls336.set_sensor_name('B', 'Cell Temp')
ls336.set_sensor_name('C', 'Mount Temp')
```

The calibration data is taken from the `data/TH100PT_curve.txt` file, change that as needed for your particular sensor.
