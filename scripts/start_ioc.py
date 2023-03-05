import asyncio
import lakeshore as ls
import numpy as np
import os
import socket
import time

from softioc import alarm, asyncio_dispatcher, builder, softioc


# Get LakeShore IP
ip = socket.gethostbyname('2idlakeshore336.xray.aps.anl.gov')

# Connect to LakeShore
ls336 = ls.Model336(ip_address=ip)

# Some useful constants
heater_off = ls.model_336.Model336HeaterVoltageRange(0)
heater_on = ls.model_336.Model336HeaterVoltageRange(1)
mode_off = ls.model_336.Model336HeaterOutputMode.OFF
mode_open = ls.model_336.Model336HeaterOutputMode.OPEN_LOOP
mode_closed = ls.model_336.Model336HeaterOutputMode.CLOSED_LOOP
input_a = ls.model_336.Model336InputChannel.CHANNEL_A
input_b = ls.model_336.Model336InputChannel.CHANNEL_B
input_c = ls.model_336.Model336InputChannel.CHANNEL_C
input_d = ls.model_336.Model336InputChannel.CHANNEL_D

# Create an asyncio dispatcher, the event loop is now running
dispatcher = asyncio_dispatcher.AsyncioDispatcher()

# Record prefix
builder.SetDeviceName('LS336:XEOL')

# Set blocking
builder.SetBlocking(True)

# Create some records
# Sample temperature
rbv_sampleT = builder.aIn(
                          'TSAMPLE_RBV',
                          initial_value=ls336.get_celsius_reading('A')
                          )

# Cell temperature
rbv_cellT = builder.aIn(
                        'TCELL_RBV',
                        initial_value=ls336.get_celsius_reading('B')
                        )

# Set point temperature
rbv_setT = builder.aIn(
                       'TSET_RBV',
                       initial_value=ls336.get_control_setpoint(3)
                       )
rec_setT = builder.aOut(
                        'TSET',
                        initial_value=ls336.get_control_setpoint(3),
                        on_update=lambda v: ls336.set_control_setpoint(3, v)
                        DRVL=15,
                        DRVH=110,
                        )

# Heater status
rbv_status = builder.boolIn(
                            'STATUS_RBV',
                            initial_value=ls336.get_heater_range(3).value
                            )
rec_status = builder.boolIn(
                            'STATUS',
                            initial_value=False,
                            on_update=lambda v: set_heater(v)
                            )

# Heater mode
rec_mode = builder.stringOut(
                             'MODE',
                             initial_value='OFF',
                             on_update=lambda v: set_output(v)
                             )

# Setpoint ramp rate
rbv_ramp = builder.aIn(
                       'RAMP_RBV',
                       initial_value=ls336.get_setpoint_ramp_parameter(3)[
                                     'rate_value'
                                     ]
                       )
rec_ramp = builder.aOut(
                        'RAMP',
                        initial_value=0,
                        on_update=lambda v: ls336.set_setpoint_ramp_parameter(
                                            3, True, v
                                            )
                        )

# P value
rbv_p = builder.aIn(
                    'P_RBV'
                    initial_value=ls336.get_heater_pid(3)['gain']
                    )
rec_p = builder.aOut(
                     'P',
                     initial_value=0,
                     on_update=lambda v: set_pid(v, 'P')
                     )

# I value
rbv_i = builder.aIn(
                    'I_RBV'
                    initial_value=ls336.get_heater_pid(3)['integral']
                    )
rec_i = builder.aOut(
                     'I',
                     initial_value=0,
                     on_update=lambda v: set_pid(v, 'I')
                     )

# D value
rbv_d = builder.aIn(
                    'D_RBV'
                    initial_value=ls336.get_heater_pid(3)['derivative']
                    )
rec_d = builder.aOut(
                     'D',
                     initial_value=0,
                     on_update=lambda v: set_pid(v, 'D')
                     )

# Boilerplate get the IOC started
builder.LoadDatabase()
softioc.iocInit(dispatcher)

# Status update
async def update_status():
    while True:
        rbv_sampleT.set(ls336.get_celsius_reading('A'))
        rbv_cellT.set(ls336.get_celsius_reading('B'))
        rbv_setT.set(ls336.get_control_setpoint(3))
        rbv_status.set(ls336.get_heater_range(3).value)
        rbv_ramp.set(ls336.get_setpoint_ramp_parameter(3)['rate_value'])
        rbv_p.set(ls336.get_header_pid(3)['gain'])
        rbv_i.set(ls336.get_header_pid(3)['integral'])
        rbv_d.set(ls336.get_header_pid(3)['derivative'])
        await asyncio.sleep(0.5)


def set_heater(v):
    if v == 0:
        ls336.set_heater_range(3, heater_off)
    else:
        ls336.set_heater_range(3, heater_on)


def set_output(v):
    if v == 'OFF':
        ls336.set_heater_output_mode(3, mode_off)
    elif v == 'OPEN LOOP':
        ls336.set_heater_output_mode(3, mode_on)
    elif v == 'CLOSED LOOP':
        ls336.set_heater_output_mode(3, mode_closed, input_a)


def set_pid(v, mode):
    pid = ls336.get_heater_pid(3)

    if mode == 'P':
        ls336.set_heater_pid(3, v, pid['integral'], pid['derivative'])
    elif mode == 'I':
        ls336.set_heater_pid(3, pid['gain'], v, pid['derivative'])
    elif mode == 'D':
        ls336.set_heater_pid(3, pid['gain'], pid['integral'], v)


dispatcher(update_status)

# Finally leave the IOC running with an interactive shell
softioc.interactive_ioc(globals())
