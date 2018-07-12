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

    def __init__(self, input_data, input_parameters, year=None, scenario=None):
        print('Initializing model')
        self.m = None
        self.solution = None
        self._DEFAULT_PARAMETERS = {
            'time_unit': pd.Timedelta('1h'),  # Time unit
            't_start': pd.Timestamp('2017-01-01'),
            't_end': pd.Timestamp('2017-01-30'), 
            'prices': { # €/MWh (LHV)
                pl.Resources.natural_gas: 7777,
                pl.Resources.power: 7777,
                pl.Resources.heat: 7777,
                pl.Resources.waste: 7777,
                pl.Resources.biomass: 7777,
                pl.Resources.CO2: 0
                },
            'CO2_factor': { # kg/TJ * TJ/MWh --> kg/MWh (only count fossil CO2)
                pl.Resources.natural_gas: 0,
                pl.Resources.power: 0,
                pl.Resources.heat: 0,
                pl.Resources.waste: 0,
                pl.Resources.biomass: 0,
                pl.Resources.CO2: 0
                },
            'interest_rate': 0.01
            }
        
    def RunModel(self):
        print('Running model')
        seed = None
        parameters = self.get_parameters()     
        t_start = parameters['t_start']
        t_end = parameters['t_end']

        print("Making model")
        self.m = self.make_model(parameters, input_data, year, scenario, seed=seed)
        #self.m.time= t_start
        #self.m.time_end= t_end
        #self.m.solver = fs.get_solver()
        _start_time = pd.Timestamp.now()
        print("Beginning simulation")
        self.m.solve()
        _end_time = pd.Timestamp.now()
        _elapsed = _end_time-_start_time
        print('Done! Simulation took {0:0.0f} seconds'.format(_elapsed.total_seconds()))
        
    def read_csv(self, file_path, index_col = 'Time (UTC)', **kwargs):
        read_file = pd.read_csv(file_path,
                                encoding='utf-8',
                                index_col= index_col,
                                parse_dates=True,
                                **kwargs)
        return read_file
    
    def get_heat_history(self, time_unit):
        heat_history = self.read_csv('C:/Users/lovisaax/Desktop/data.csv')
        return heat_history.resample(time_unit).sum()
    
    def get_heat_history_industry(self, time_unit):
        heat_history_industry = self.read_csv('C:/Users/lovisaax/Desktop/industrial_load_generated.csv')
        return heat_history_industry.resample(time_unit).sum()
    
    def get_solar_data(self, time_unit):
        solar_data = pd.read_csv(
            'C:/Users/lovisaax/Desktop/solar_data_2017.csv',
                encoding='utf-8',
                index_col='Time',
                parse_dates=True,
                squeeze=True)
        return solar_data.resample(time_unit).sum()
    
    def get_power_demand(self, time_unit):
        power_demand = self.read_csv('C:/Users/lovisaax/Desktop/power_demand.csv')
        return power_demand.resample(time_unit).sum()
    """
    def get_power_price(self, time_unit):
        print(self.power_price_file)
        power_price = self.read_csv(self.power_price_file, squeeze=True)
        return power_price.resample(time_unit).mean()
    """

    """
    def get_renovation_data(self, time_unit)
        renovation_data = self.read_csv()
        return renovation_data.resample(time_unit).sum())
    """

    def annuity(self, interest_rate, lifespan, investment_cost):
        k = interest_rate/(1-(1+interest_rate)**(-lifespan))
        r = investment_cost*k
        return r

    def get_parameters(self, **kwargs):
        parameters = deepcopy(self._DEFAULT_PARAMETERS)
        parameters.update(kwargs)
        parameters['interest_rate'] = input_parameters['interest_rate']['interest_rate']
        for resource in pl.Resources:
            conversion_factor=0.003600 #To convert CO2 factor from kg/TJ to kg/MWh
            parameters['prices'][resource] = input_parameters['prices'][resource.name]
            parameters['CO2_factor'][resource] = input_parameters['CO2_factor'][resource.name]*conversion_factor
        return parameters
    def make_model(self, parameters, input_data, year=None, scenario=None, seed=None):
        if seed:
            raise NotImplementedError('Randomizer not yet supported')
        print("building model")

        parts, timeindependent_constraint = self.make_parts(parameters)

        model = DispatchModel(t_start=parameters['t_start'],
                              t_end=parameters['t_end'],
                              time_unit=parameters['time_unit'],
                              timeindependent_constraint = timeindependent_constraint)


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

        heat_history = self.get_heat_history(parameters['time_unit'])
        power_demand = self.get_power_demand(parameters['time_unit'])
        heat_history_industry = self.get_heat_history(parameters['time_unit'])*(2/3) #self.get_heat_history_industry(parameters['time_unit'])

        heat_history = round(heat_history)
        power_demand = round(power_demand)
        heat_history_industry = round(heat_history_industry)

        taxation = make_tax_function(parameters)
        for r in pl.Resources:
            if r is not pl.Resources.heat:
                if r is not pl.Resources.CO2:
                    parts.add(
                        pl.Import(
                            resource=r,
                            price=parameters['prices'][r],
                            name='Import({})'.format(r),
                            CO2_factor=parameters['CO2_factor'][r]))

        # Conversion factor from hour to model time unit:
        # "hour" is the number of model time steps per hour.
        # So when capacities/consumption/etc per time step in plants below
        # are stated like 600 / hour", then think "600 MWh per hour".
        # Makes sense because larger time unit --> smaller value of "hour" -->
        # larger max output per time step.
        
        hour = pd.Timedelta('1h') / parameters['time_unit']
        
        renovation_data_1 = self.get_heat_history(parameters['time_unit'])*0.01 #change to renovation data when available
        renovation_data_15 =self.get_heat_history(parameters['time_unit'])*0.015 #change to renovation data when available

        if not 'Trade_off' in scenario:
            renovation = fs.Node(name = input_data['Renovation']['name'])
            renovation.consumption[pl.Resources.heat]= lambda t: - renovation_data_1['DH'][t]
            renovation.state_variables = lambda t: ()
            renovation.cost = lambda t: 0
            parts.add(renovation)

        else:
            renovation = fs.Node(name = input_data['Renovation']['name'])
            inv_1 = fs.Variable(domain = fs.Domain.binary)
            inv_0 = fs.Variable(domain = fs.Domain.binary)
            renovation.test = {'investment_cost' : self.annuity(parameters['interest_rate'],input_data['Renovation']['lifespan'],input_data['Renovation']['investment_cost']), 'renovation level': input_data['Renovation']['capacity']}
            renovation.state_variables = lambda t: ()
            renovation.static_variables = {inv_1, inv_0}

            renovation.consumption[pl.Resources.heat]= lambda t: - renovation_data_1['Other'][t]*inv_1 - 0*inv_0

            renovation.investment_cost =  self.annuity(parameters['interest_rate'],input_data['Renovation']['lifespan'],input_data['Renovation']['investment_cost']) * inv_1 + 0 * inv_0
            renovation.cost = lambda t:0
            parts.add(renovation)

            renovation_15 = fs.Node(name = input_data['Renovation_15']['name'])
            inv_15 = fs.Variable(domain = fs.Domain.binary)
            inv_2 = fs.Variable(domain = fs.Domain.binary)
            renovation_15.test = {'investment_cost' : self.annuity(parameters['interest_rate'],input_data['Renovation_15']['lifespan'],input_data['Renovation_15']['investment_cost']), 'renovation level': input_data['Renovation_15']['capacity']}
            renovation_15.state_variables = lambda t: ()
            renovation_15.static_variables ={inv_15, inv_2}

            renovation_15.consumption[pl.Resources.heat]= lambda t: - renovation_data_15['DH'][t]*inv_15 - 0*inv_2

            renovation_15.investment_cost =  self.annuity(parameters['interest_rate'],input_data['Renovation_15']['lifespan'],input_data['Renovation_15']['investment_cost']) * inv_15 + 0 * inv_2
            renovation_15.cost = lambda t:0
            parts.add(renovation_15)

            renovation_const = fs.Eq(inv_0 + inv_1, 1)
            renovation_const_2 = fs.Eq(inv_1 + inv_2 + inv_15, 1)

        city = fs.Node(name='City')
        city.consumption[pl.Resources.heat] =  lambda t: heat_history['DH'][t]
        city.consumption[pl.Resources.power] = lambda t: power_demand['Power demand'][t]
        city.cost = lambda t: 0
        city.state_variables = lambda t: ()
        parts.add(city)

        Industry = fs.Node(name='Industry')
        Industry.consumption[pl.Resources.heat] = lambda t: heat_history_industry['DH'][t] #heat_history_industry['Industrial'][t] 
        Industry.cost = lambda t: 0
        Industry.state_variables = lambda t: ()
        parts.add(Industry)

        powerExport = pl.Export(resource = pl.Resources.power,
                             capacity=1000 / hour, # Arbitrarily chosen, assumed higher than combined production
                             price = parameters['prices'][pl.Resources.power]/10,
                             name='power export')
        
        "Timeindependent constraint on maximum power export during the whole timeperiod"
        t_start= parameters['t_start']
        t_end = parameters['t_end']
        powerExport.time_unit = pd.Timedelta('1h')
        times = powerExport.times_between(t_start, t_end)
        power = fs.Sum(powerExport.consumption[pl.Resources.power](t) for t in times)
        power_maximum = fs.LessEqual(power, 60000)

        parts.add(powerExport)

        CO2 = fs.Node(name = 'CO2_emissions')
        capacity=50000/hour
        quantity = fs.VariableCollection(lb=0, ub=capacity)
        CO2.consumption[pl.Resources.CO2] = lambda t: quantity(t)
        CO2.cost = lambda t: 0
        CO2.state_variables = lambda t: {quantity(t)}

        "Timeindependent constraint on maximum CO2 emissions during the whole timeperiod"
        CO2.time_unit = pd.Timedelta('1h')
        times = CO2.times_between(parameters['t_start'], parameters['t_end'])
        emissions = fs.Sum(CO2.consumption[pl.Resources.CO2](t) for t in times)
        CO2_maximum = fs.LessEqual(emissions, 100000000) #below 24 069 146 limit the CO2 emissions
        
        parts.add(CO2)

        CHP_A = pl.LinearSlowCHP(
                name='Existing CHP A',
                eta=0.776, # was 77.6
                alpha=0.98,
                Fmax= 4.27 / hour,  # 449.0 / hour,  # 449 m3/hour
                Fmin= 2.33 / hour,  # 245.0 / hour,  # 245 m3/hour
                #start_steps=int(np.round(.5 * hour)),
                fuel=pl.Resources.natural_gas,
                taxation=taxation)
        CHP_A.time_unit = pd.Timedelta('1h')
        times = CHP_A.times_between(parameters['t_start'],parameters['t_end'])
        production_CHP_A=fs.Sum(CHP_A.production[pl.Resources.heat](t) for t in times)
        parts.add(CHP_A)        

        CHP_B =pl.LinearSlowCHP(
                name='Existing CHP B',
                eta=0.778, #was 77.8
                alpha=0.98,
                Fmax= 4.27 /hour, # 449.0 / hour,  # 449 m3/hour
                Fmin=2.33 / hour,  # 245.0 / hour,  # 245 m3/hour
                start_steps=int(np.round(.5 * hour)),
                fuel=pl.Resources.natural_gas,
                taxation=taxation)
        CHP_B.time_unit = pd.Timedelta('1h')
        times = CHP_B.times_between(parameters['t_start'],parameters['t_end'])
        production_CHP_B=fs.Sum(CHP_B.production[pl.Resources.heat](t) for t in times)
        parts.add(CHP_B) 

        test_1 = sum(heat_history['DH'][t] for t in times)
        test_2 = sum(heat_history_industry['DH'][t] for t in times)
        limit = float((test_1 + test_2)*0.1) #should be 10% of energy production, not demand, this is test limit
        min_prod = fs.LessEqual(limit, production_CHP_A + production_CHP_B)

        parts.add(
            pl.Boiler(
                name='Existing Boiler A',
                eta=0.9,
                Fmax=8.84 / hour,  # 930.89 / hour,  # Sm3/hour
                # Fmin=135.52 / hour,#Sm3/hour
                fuel=pl.Resources.natural_gas,
                taxation=taxation))

        parts.add(
            pl.Boiler(
                name='Existing Boiler B',
                eta=0.87,
                Fmax=8.84 / hour,  # 930.89 / hour,  # Sm3/hour
                # Fmin=135.52 / hour,#Sm3/hour
                fuel=pl.Resources.natural_gas,
                taxation=taxation))

        parts.add(
            pl.Boiler(
                name='Existing Boiler C',
                eta=0.89,
                Fmax=8.84 / hour,  # 930.89 / hour,  # Sm3/hour
                # Fmin=465.44 / hour,#Sm3/hour
                fuel=pl.Resources.natural_gas,
                taxation=taxation))
        
        parts.add(
            pl.Boiler(
                name='Existing Boiler D',
                eta= 0.77,
                Fmax= 8.84 / hour,  # 930.89 / hour,  # Sm3/hour
                # Fmin=465.44 / hour,#Sm3/hour
                fuel=pl.Resources.natural_gas,
                taxation=taxation))
        """
        parts.add(
            pl.LinearSlowCHP(
                name='Existing Waste Incinerator',
                start_steps=int(np.round(12 * hour)), #int(np.round(12*0.1)),
                fuel=pl.Resources.waste,
                alpha=0.46,
                eta=0.81,
                Fmin= 10/hour, #10 / hour,
                Fmax= 45/hour, #45 /hour, # Update to reflect 25 MW output max according to D4.2 p 32 
                taxation=taxation))        
        """

        parts.add(
            pl.LinearCHP(
                name='Existing Waste Incinerator',
                fuel=pl.Resources.waste,
                alpha=0.46,
                eta=0.81,
                #Fmin= 2.5/hour,
                Fmax= 45/hour, # Update to reflect 25 MW output max according to D4.2 p 32 
                taxation=taxation))  

        parts.add(
            pl.Accumulator(
                name='Existing Accumulator',
                resource=pl.Resources.heat,
                max_flow=60/hour, 
                max_energy= 220,
                loss_factor = 0.005,
                t_start = parameters['t_start'],
                t_end = parameters['t_end']))   
        
        """ Production alternatives for the scenarios"""
        
        solar_data=self.get_solar_data(parameters['time_unit'])

        parts.add(
            pl.LinearSlowCHP(
            name = input_data['CHP']['name'],
            eta = input_data['CHP']['eta'], #Titta så att den här är rätt, är eta = n_el + n__thermal??
            alpha = input_data['CHP']['alpha'], #Kontrollera denna, är alpha = n_el/n_thermal --> 0.5.
            start_steps = int(np.round(input_data['CHP']['start_steps']*hour)),#Vad ska vi ha för start_steps?
            capacity = input_data['CHP']['capacity'],
            max_capacity = input_data['CHP']['max_capacity'],
            fuel =  input_data['CHP']['resource'],
            taxation = input_data['CHP']['taxation'],  #ska vara taxation här men fick inte rätt då
            investment_cost = self.annuity(parameters['interest_rate'], input_data['CHP']['lifespan'], input_data['CHP']['investment_cost'])))

        if '2050' in year:
            if 'Trade_off' in scenario:
                parts.add(
                    pl.LinearSlowCHP(
                    name = input_data['CHP invest']['name'],
                    eta = input_data['CHP invest']['eta'], #Titta så att den här är rätt, är eta = n_el + n__thermal??
                    alpha = input_data['CHP invest']['alpha'], #Kontrollera denna, är alpha = n_el/n_thermal --> 0.5.
                    start_steps = int(np.round(input_data['CHP invest']['start_steps']*hour)),#Vad ska vi ha för start_steps?
                    capacity = input_data['CHP invest']['capacity'],
                    max_capacity = input_data['CHP invest']['max_capacity'],
                    fuel =  input_data['CHP invest']['resource'],
                    taxation = input_data['CHP invest']['taxation'],  #ska vara taxation här men fick inte rätt då
                    investment_cost = self.annuity(parameters['interest_rate'], input_data['CHP invest']['lifespan'], input_data['CHP invest']['investment_cost'])))


        parts.add(
            pl.SolarPV(
                name = input_data['SolarPV']['name'],
                G = solar_data['irradiation'],
                T = solar_data['temperature'], 
                max_capacity = input_data['SolarPV']['max_capacity'],
                capacity = input_data['SolarPV']['capacity'], #Eller capacity borde väl inte anges för investment option
                taxation = input_data['SolarPV']['taxation'], 
                investment_cost = self.annuity(parameters['interest_rate'], input_data['SolarPV']['lifespan'], input_data['SolarPV']['investment_cost'])))
        if '2050' in year:
            parts.add(
                pl.Accumulator(
                    name = input_data['Accumulator']['name'],
                    resource =  input_data['Accumulator']['resource'], 
                    max_flow = input_data['Accumulator']['max_flow'], 
                    max_energy = input_data['Accumulator']['max_energy'], 
                    loss_factor = input_data['Accumulator']['loss_factor'],
                    max_capacity = input_data['Accumulator']['max_capacity'],
                    investment_cost = self.annuity(parameters['interest_rate'], input_data['Accumulator']['lifespan'], input_data['Accumulator']['investment_cost']),
                    t_start = parameters['t_start'],
                    t_end = parameters['t_end']))  

        parts_in_heat_cluster = {p for p in parts
                          if ((pl.Resources.heat in p.production) or
                              (pl.Resources.heat in p.accumulation) or
                              (pl.Resources.heat in p.consumption)) and
                          not isinstance(p, fs.Cluster)}

        city_heat_cluster=fs.Cluster(resource = pl.Resources.heat, name='city heat cluster')
        city_heat_cluster.cost = lambda t: 0

        for p in parts_in_heat_cluster:
            city_heat_cluster.add_part(p)
        parts.add(city_heat_cluster)

        timeindependent_constraint = []
        if 'Trade_off_CO2' in scenario:
            timeindependent_constraint = [CO2_maximum, renovation_const, renovation_const_2, min_prod]
        elif 'Trade_off' in scenario:
            timeindependent_constraint = [renovation_const, renovation_const_2, min_prod]
        else:
            timeindependent_constraint = [min_prod]
        
        return parts, timeindependent_constraint
        

if __name__ == "__main__":
    print('Running city.py standalone')
    import pdb  
    from read_data import read_data
    data=read_data('C:/Users/lovisaax/Documents/Sinfonia/scenario_data_v2.xlsx')

    for year in ['2030']: #'2050
        input_parameters=data[year+'_input_parameters']
        for scenario in ['Trade_off']:#'BAU', 'Max_RES', 'Max_DH', 'Max_Retrofit', 'Trade_off', 'Trade_off_CO2']: 
            input_data=data[year+'_'+scenario]
            model = CityModel(input_data, input_parameters, year, scenario)
            model.RunModel()
            parameters = model.get_parameters()

            from process_results import process_results
            process_results(model, parameters, pl.Resources, year, scenario, input_data)
    