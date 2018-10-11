import sys
import io
import logging
import csv
import pdb
import pandas as pd
import numpy as np
import friendlysam as fs
import matplotlib.pyplot as plt
from copy import deepcopy   
import numpy

def get_temperature_data(time_unit):
    temperature_data = pd.read_csv(
        'C:/Users/lovisaax/Desktop/temperature_data_Bergamo_modified.csv',
            encoding='utf-8',
            index_col='Data-Ora',
            parse_dates=True,
            squeeze=True)
    return temperature_data.resample(time_unit).sum()

def get_irradiation_data( time_unit):
    irradiation_data = pd.read_csv(
        'C:/Users/lovisaax/Desktop/irradiation_data_Bergamo_modified.csv',
            encoding='utf-8',
            index_col='Data-Ora',
            parse_dates=True,
            squeeze=True)
    return irradiation_data.resample(time_unit).sum()

def get_heat_history( time_unit):
    heat_history = pd.read_csv(
        'C:/Users/lovisaax/Desktop/data.csv',
            encoding='utf-8',
            index_col='Time (UTC)',
            parse_dates=True,
            squeeze=True)
    return heat_history.resample(time_unit).sum()

def get_power_demand(time_unit):
    power_demand = pd.read_csv(
        'C:/Users/lovisaax/Desktop/test_power_demand.csv',
            encoding='utf-8',
            index_col='Time (UTC)',
            parse_dates=True,
            squeeze=True)
    return power_demand.resample(time_unit).sum()

time_unit= pd.Timedelta('1h')
temperature = get_temperature_data(time_unit)
temperature = temperature['Media']
temperature = temperature.rename('temperature')

medel = numpy.mean(temperature)
count = 0
for item in temperature:

    if item == -999.0:
        count = count + 1
        print(count)

irradiation = get_irradiation_data(time_unit)
irradiation = irradiation['Media']
irradiation = irradiation.rename('irradiation')
pdb.set_trace()
count_2 = 0
for item in irradiation:

    if item == -999.0:
        count_2 = count_2 + 1
        print(count_2)

solar_data = temperature.to_frame().join(irradiation.to_frame())

data = get_heat_history(time_unit)
test_index=pd.date_range(start='2016-01-01', end='2016-12-31', freq='H' )
heat_history = pd.DataFrame({'Time (UTC)':test_index, 'DH':data['DH'], 'Other':data['Other']})
heat_history = heat_history.set_index('Time (UTC)')

power_demand = get_power_demand(time_unit)
power_demand = pd.DataFrame({'Time (UTC)': test_index, 'Power demand': power_demand})
power_demand = power_demand.set_index('Time (UTC)')

temperature.to_csv('C:/Users/lovisaax/Desktop/data/temperature_data.csv', index_label = 'Time (UTC)', header = 'temperature')
solar_data.to_csv('C:/Users/lovisaax/Desktop/data/solar_data.csv', index_label = 'Time (UTC)')
heat_history.to_csv('C:/Users/lovisaax/Desktop/data/test_heat_history.csv', index_label = 'Time (UTC)')
power_demand.to_csv('C:/Users/lovisaax/Desktop/data/test_power_demand.csv', index_label = 'Time (UTC)')

"""
#myFile = open('C:/Users/lovisaax/Desktop/temperature_data_2017.csv', 'w')
#with myFile:
#    writer=csv.writer(myFile)
#    writer.writerows(temperature)
#temperature = pd.write_csv('C:/Users/lovisaax/Desktop/temperature_data_2017.csv')
"""