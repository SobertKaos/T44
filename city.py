# -*- coding: utf-8 -*-

import sys
import io
import logging
import csv
import pdb
import pandas as pd
import numpy as np
import friendlysam as fs
import partlib as pl
import matplotlib.pyplot as plt
from models import DispatchModel
from copy import deepcopy
# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.DEBUG)

print("using pandas version ", pd.__version__)
print("using python version", sys.version)


class CityModel():

    def __init__(self):
        print('Initializing model')
        self.m = None
        self.solution = None
        self._DEFAULT_PARAMETERS = {
            'time_unit': pd.Timedelta('1h'),  # Time unit
            't_start': pd.Timestamp('2015-01-01'),
            't_end': pd.Timestamp('2015-01-02'), 
            'prices': { # €/MWh (LHV)
                pl.Resources.natural_gas: 7777,
                pl.Resources.power: 7777,
                pl.Resources.heat: 7777,
                pl.Resources.heating_oil: 7777,
                pl.Resources.bio_oil: 7777,
                pl.Resources.wood_chips: 7777,
                pl.Resources.wood_pellets: 7777,
                pl.Resources.waste: 7777,
                }
        }

    def RunModel(self):
        print('Running model')
        seed = None
        parameters = self.get_parameters()     
        t_start = parameters['t_start']
        t_end = parameters['t_end']

        print("Making model")
        self.m = self.make_model(parameters, seed=seed)
        #self.m.time= t_start
        #self.m.time_end= t_end
        #self.m.solver = fs.get_solver()
        _start_time = pd.Timestamp.now()
        print("Beginning simulation")
        self.m.solve()
        _end_time = pd.Timestamp.now()
        _elapsed = _end_time-_start_time
        print('Done! Simulation took {0:0.0f} seconds'.format(_elapsed.total_seconds()))
        
        

    def set_heat_history(self, p_heat_history):
        self.heat_history_file = p_heat_history

    def set_power_demand(self, p_power_demand):
        self.power_demand_file = p_power_demand

    def set_power_price(self, p_power_price):
        self.power_price_file = p_power_price

    def set_fixed_price(self, p_fixed_price):
        self.fixed_price_file = p_fixed_price

    def read_csv(self, file_path, index_col = 'Time (UTC)', **kwargs):
        read_file = pd.read_csv(file_path,
                                encoding='utf-8',
                                index_col= index_col,
                                parse_dates=True,
                                **kwargs)
        return read_file

    def get_heat_history(self, time_unit):
        heat_history = self.read_csv('test_data.csv')
        return heat_history.resample(time_unit).sum()

    def get_heat_history_industry(self, time_unit):
        heat_history_industry = self.read_csv('industrial_load_generated.csv')
        return heat_history_industry.resample(time_unit).sum()

    def get_power_demand(self, time_unit):
        power_demand = self.read_csv(self.power_demand_file, squeeze=True)
        return power_demand.resample(time_unit).sum()

    def get_power_price(self, time_unit):
        print(self.power_price_file)
        power_price = self.read_csv(self.power_price_file, squeeze=True)
        return power_price.resample(time_unit).mean()

    def get_parameters(self, **kwargs):
        parameters = deepcopy(self._DEFAULT_PARAMETERS)
        parameters.update(kwargs)
        return parameters

    def make_model(self, parameters, seed=None):
        if seed:
            raise NotImplementedError('Randomizer not yet supported')
        print("building model")
        model = DispatchModel(t_start=parameters['t_start'],
                              t_end=parameters['t_end'],
                              time_unit=parameters['time_unit'])

        parts = self.make_parts(parameters)
        # No explicit distribution channels except for heat.
        for r in pl.Resources:
            if r is not pl.Resources.heat:
                cluster = fs.Cluster(resource=r, name='{} cluster'.format(r))
                for p in parts:
                    if not isinstance(p, fs.parts.FlowNetwork) and (r in p.resources):
                        # FlowNetwork has no attribute ´resources´
                        cluster.add_part(p)
                    else:
                        model.add_part(p)
                cluster.cost = lambda t: 0
                model.add_part(cluster)

        for p in model.descendants_and_self:
            p.time_unit = parameters['time_unit']

        return model

    def make_parts(self, parameters):
        parts = set()
        def make_tax_function(*args, **kwargs):
            def tax_function(*args, **kwargs):
                return 0
            return  tax_function

        #heat_history = self.get_heat_history(parameters['time_unit'])
        #power_demand = self.get_power_demand(parameters['time_unit'])
        #heat_history_industry = self.get_heat_history_industry(parameters['time_unit'])
        taxation = make_tax_function(parameters)

        for r in pl.Resources:
            if r is not pl.Resources.heat:
                parts.add(
                    pl.Import(
                        resource=r,
                        price=parameters['prices'][r],
                        name='Import({})'.format(r)))

        # Conversion factor from hour to model time unit:
        # "hour" is the number of model time steps per hour.
        # So when capacities/consumption/etc per time step in plants below
        # are stated like 600 / hour", then think "600 MWh per hour".
        # Makes sense because larger time unit --> smaller value of "hour" -->
        # larger max output per time step.
        hour = pd.Timedelta('1h') / parameters['time_unit']
        series_reader = lambda series: series.loc.__getitem__

        """ """
        heat_history = self.get_heat_history(parameters['time_unit'])
        
        #test = series_reader(heat_history.sum(axis=1))

        """ """

        city = fs.Node(name='City')
        city.consumption[pl.Resources.heat] = series_reader(heat_history.sum(axis=1)) #lambda t: 14
        city.consumption[pl.Resources.power] = lambda t: 13
        city.cost = lambda t: 0
        city.state_variables = lambda t: ()
        parts.add(city)

        Industry = fs.Node(name='Industry')
        Industry.consumption[pl.Resources.heat] = lambda t: 12
        Industry.cost = lambda t: 0
        Industry.state_variables = lambda t: ()
        parts.add(Industry)

        powerExport = pl.Export(resource = pl.Resources.power,
                             capacity=1000 / hour, # Arbitrarily chosen, assumed higher than combined production
                             price = parameters['prices'][pl.Resources.power]/10)
        parts.add(powerExport)

        parts.add(
            pl.LinearSlowCHP(
                name='CHP A',
                eta=0.776, # was 77.6
                alpha=0.98,
                Fmax=4.27 / hour,  # 449.0 / hour,  # 449 m3/hour
                Fmin=2.33 / hour,  # 245.0 / hour,  # 245 m3/hour
                start_steps=int(np.round(.5 * hour)),
                fuel=pl.Resources.natural_gas,
                taxation=taxation))

        parts.add(
            pl.LinearSlowCHP(
                name='CHP B',
                eta=0.778, #was 77.8
                alpha=0.98,
                Fmax=4.27 / hour,  # 449.0 / hour,  # 449 m3/hour
                Fmin=2.33 / hour,  # 245.0 / hour,  # 245 m3/hour
                start_steps=int(np.round(.5 * hour)),
                fuel=pl.Resources.natural_gas,
                taxation=taxation))

        parts.add(
            pl.Boiler(
                name='Boiler A',
                eta=0.9,
                Fmax=8.84 / hour,  # 930.89 / hour,  # Sm3/hour
                # Fmin=135.52 / hour,#Sm3/hour
                fuel=pl.Resources.natural_gas,
                taxation=taxation))

        parts.add(
            pl.Boiler(
                name='Boiler B',
                eta=0.87,
                Fmax=8.84 / hour,  # 930.89 / hour,  # Sm3/hour
                # Fmin=135.52 / hour,#Sm3/hour
                fuel=pl.Resources.natural_gas,
                taxation=taxation))

        parts.add(
            pl.Boiler(
                name='Boiler C',
                eta=0.89,
                Fmax=8.84 / hour,  # 930.89 / hour,  # Sm3/hour
                # Fmin=465.44 / hour,#Sm3/hour
                fuel=pl.Resources.natural_gas,
                taxation=taxation))

        parts.add(
            pl.Boiler(
                name='Boiler D',
                eta=0.77,
                Fmax=8.84 / hour,  # 930.89 / hour,  # Sm3/hour
                # Fmin=465.44 / hour,#Sm3/hour
                fuel=pl.Resources.natural_gas,
                taxation=taxation))

        parts.add(
            pl.LinearSlowCHP(
                name='Waste Incinerator',
                start_steps=12,
                fuel=pl.Resources.waste,
                alpha=0.46,
                eta=0.81,
                Fmin=10 / hour,
                Fmax=45 /hour, # Update to reflect 25 MW output max according to D4.2 p 32
                taxation=taxation))
        
        parts.add(
            pl.Accumulator(
                resource=pl.Resources.heat,
                max_flow=6/hour,
                max_energy=68,
                loss_factor = 0,
                name='TES'))

        heat_producers = {p for p in parts
                          if ((pl.Resources.heat in p.production) or
                              (pl.Resources.heat in p.accumulation)) and
                          not isinstance(p, fs.Cluster)}
        production_cluster = fs.Cluster(resource=pl.Resources.heat,
                                        name='production cluster')
        production_cluster.cost = lambda t: 0

        for p in heat_producers:
            production_cluster.add_part(p)

        parts.add(production_cluster)

        heat_consumers = {p for p in parts
                          if pl.Resources.heat in p.consumption and
                          not isinstance(p, fs.Cluster)}

        consumption_cluster = fs.Cluster(resource=pl.Resources.heat,
                                         name='consumption cluster')
        consumption_cluster.cost = lambda t: 0
        for p in heat_consumers:
            if not isinstance(p, pl.Accumulator):
                consumption_cluster.add_part(p)
        consumption_cluster.add_part(powerExport)
        parts.add(consumption_cluster)

        
        pipe = fs.FlowNetwork(pl.Resources.heat)
        pipe.cost = lambda t: 0
        pipe.connect(production_cluster, consumption_cluster)
        parts.add(pipe)

        return parts


if __name__ == "__main__":
    print('Running city.py standalone')
    model = CityModel()
    model.RunModel()

