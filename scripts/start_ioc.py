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

# Let's stick to output 3
output = 3

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
                       initial_value=ls336.get_control_setpoint(output)
                       )
rec_setT = builder.aOut(
                        'TSET',
                        initial_value=ls336.get_control_setpoint(output),
                        on_update=lambda v: ls336.set_control_setpoint(output, v),
                        DRVL=15,
                        DRVH=110,
                        )

# Heater status
rbv_status = builder.boolIn(
                            'STATUS_RBV',
                            initial_value=ls336.get_heater_range(output).value
                            )
rec_status = builder.boolOut(
                             'STATUS',
                             initial_value=ls336.get_heater_range(output).value,
                             on_update=lambda v: set_heater(v)
                             )
rbv_statuslbl = builder.stringIn(
                                 'STATUS_LABEL',
                                 initial_value='Heater Off'
                                 )

# Heater mode
rbv_mode = builder.stringIn(
                            'MODE_RBV',
                            initial_value=ls336.get_heater_output_mode(output) \
                                          .name.replace('_', ' '),
                            )
rec_mode = builder.stringOut(
                             'MODE',
                             initial_value=ls336.get_heater_output_mode(output) \
                                           .name.replace('_', ' '),
                             on_update=lambda v: set_mode(v)
                             )

# Heater load
rbv_load = builder.aIn(
                       'LOAD_RBV',
                       initial_value=ls336.get_analog_output_percentage(output),
                       )
rec_load = builder.aOut(
                        'LOAD',
                        initial_value=ls336.get_analog_output_percentage(output),
                        on_update=lambda v:
                                  ls336.set_analog_output_percentage(output, v)
                        )

# Setpoint ramp rate
rbv_ramp = builder.aIn(
                       'RAMP_RBV',
                       initial_value=ls336.get_setpoint_ramp_parameter(output)[
                                     'rate_value'
                                     ]
                       )
rec_ramp = builder.aOut(
                        'RAMP',
                        initial_value=ls336.get_setpoint_ramp_parameter(output)[
                                      'rate_value'
                                      ]
                        initial_value=ls336.get_setpoint_ramp_parameter(output),
                        on_update=lambda v: ls336.set_setpoint_ramp_parameter(
                                            output, True, v
                                            )
                        )

# Setpoint ramp status
rbv_ramp_status = builder.aIn(
                              'RAMP_STATUS_RBV',
                              initial_value=ls336.get_setpoint_ramp_status(output),
                              )
rbv_ramp_statuslbl = builder.stringIn(
                                      'RAMP_STATUS_LABEL',
                                      initial_value=get_ramp()
                                      )

# P value
rbv_p = builder.aIn(
                    'P_RBV',
                    initial_value=ls336.get_heater_pid(output)['gain']
                    )
rec_p = builder.aOut(
                     'P',
                     initial_value=ls336.get_heater_pid(output)['gain'],
                     on_update=lambda v: set_pid(v, 'P')
                     )

# I value
rbv_i = builder.aIn(
                    'I_RBV',
                    initial_value=ls336.get_heater_pid(output)['integral']
                    )
rec_i = builder.aOut(
                     'I',
                     initial_value=ls336.get_heater_pid(output)['integral'],
                     on_update=lambda v: set_pid(v, 'I')
                     )

# D value
rbv_d = builder.aIn(
                    'D_RBV',
                    initial_value=ls336.get_heater_pid(output)['ramp_rate']
                    )
rec_d = builder.aOut(
                     'D',
                     initial_value=ls336.get_heater_pid(output)['ramp_rate'],
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
        rbv_setT.set(ls336.get_control_setpoint(output))
        rbv_load.set(ls336.get_analog_output_percentage(output))
        rbv_ramp.set(ls336.get_setpoint_ramp_parameter(output)['rate_value'])
        rbv_p.set(ls336.get_heater_pid(output)['gain'])
        rbv_i.set(ls336.get_heater_pid(output)['integral'])
        rbv_d.set(ls336.get_heater_pid(output)['ramp_rate'])
        rbv_statuslbl.set(get_heater())
        rbv_ramp_status.set(ls336.get_setpoint_ramp_status(output))
        rbv_ramp_statuslblset(get_ramp())
        rbv_mode.set(ls336.get_heater_output_mode(output) \
                     .name.replace('_', ' '))

        await asyncio.sleep(0.5)


def set_heater(v):
    if v == 0:
        ls336.set_heater_range(output, heater_off)
    else:
        ls336.set_heater_range(output, heater_on)


def get_heater():
    status = ls336.get_heater_range(output).value
    if status:
        return 'Heater On'
    else:
        return 'Heater Off'


def set_mode(v):
    if v == 'OFF':
        ls336.set_heater_output_mode(output, mode_off)
    elif v == 'OPEN LOOP':
        ls336.set_heater_output_mode(output, mode_on)
    elif v == 'CLOSED LOOP':
        ls336.set_heater_output_mode(output, mode_closed, input_a)


def get_ramp():
    if ls336.get_setpoint_ramp_status:
        return 'Setpoint ramping!'
    else:
        return 'Setpoint reached!'


def set_pid(v, mode):
    pid = ls336.get_heater_pid(output)

    if mode == 'P':
        ls336.set_heater_pid(output, v, pid['integral'], pid['ramp_rate'])
    elif mode == 'I':
        ls336.set_heater_pid(output, pid['gain'], v, pid['ramp_rate'])
    elif mode == 'D':
        ls336.set_heater_pid(output, pid['gain'], pid['integral'], v)


dispatcher(update_status)

# Finally leave the IOC running with an interactive shell
softioc.interactive_ioc(globals())
