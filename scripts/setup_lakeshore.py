import lakeshore as ls
import numpy as np
import socket


# Get LakeShore IP
ip = socket.gethostbyname('2idlakeshore336.xray.aps.anl.gov')

# Connect to LakeShore
ls336 = ls.Model336(ip_address=ip)

# Some useful constants
header = ls.model_336.Model336CurveHeader
format = ls.model_336.Model336CurveFormat
coeffs = ls.model_336.Model336CurveTemperatureCoefficients

# Rename inputs
ls336.set_sensor_name('A', 'Sample Temp')
ls336.set_sensor_name('B', 'Cell Temp')

# Set RTD header into curve 21 (first one that can be customized)
rtd_header = header(
                    'RTD',
                    'TH100PT',
                    format.OHMS_PER_KELVIN,
                    273.15+150,
                    coeffs.POSITIVE
                    )
ls336.set_curve_header(21, rtd_header)

# Import calibration data (from ThorLabs)
curve = np.loadtxt('../data/TH100PT_curve.txt', skiprows=1)

# Populate calibration list (can't seem to do it all at once...?)
for i, x in enumerate(curve):
    ls336.set_curve_data_point(21, i, *x)