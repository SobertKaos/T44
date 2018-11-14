# -*- coding: utf-8 -*-

import sys
import io
import logging
import csv
import pdb
import winsound
from read_data import read_data
import pandas as pd
import numpy as np
import friendlysam as fs
import partlib as pl
import matplotlib.pyplot as plt
from models import DispatchModel
from copy import deepcopy
from process_results import process_results
from final_processor import final_processor
# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.DEBUG)

print("using pandas version ", pd.__version__)
print("using python version", sys.version)


class CityModel():

    def __init__(self, input_data, input_parameters, year=None, scenario=None):
        print('Initializing model')
        self.m = None
        self.solution = None
        self.input_data = input_data
        self.input_parameters = input_parameters
        self.year = year
        self.scenario = scenario
        self._DEFAULT_PARAMETERS = {
            'time_unit': pd.Timedelta('7d'),  # Time unit
            't_start': pd.Timestamp('2016-01-01'),
            't_end': pd.Timestamp('2016-12-30'), 
            'prices': { },
            'CO2_factor': { },
            'interest_rate': 0.01
            }
        
    def RunModel(self):
        seed = None
        parameters = self.get_parameters()

        self.m = self.make_model(parameters, self.input_data, self.year, self.scenario, seed=seed)
        _start_time = pd.Timestamp.now()

        print("Beginning simulation {}".format(pd.datetime.now().time()))
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
        heat_history = pd.read_csv('C:/Users/alexanderka/desktop/Bolzano Heat with renovations.csv', index_col = 'Time (UTC)', parse_dates=True, delimiter=',')
        #heat_history['DH'] = heat_history['Test_A0H']
        return heat_history
    
    def get_heat_history_industry(self, time_unit):
        heat_history_industry = self.read_csv('C:/Users/AlexanderKa/Desktop/Github/T4-4/input/industrial_heat_load.csv')
        return heat_history_industry.resample(time_unit).sum()

    def get_solar_data(self, time_unit):
        solar_data = self.read_csv('C:/Users/AlexanderKa/Desktop/Github/T4-4/input/Solar_data_Bolzano.csv')
        return solar_data  #.resample(time_unit).sum()
    
    def get_power_demand(self, time_unit):
        power_demand = self.read_csv('C:/Users/AlexanderKa/Desktop/Github/T4-4/input/test_power_demand.csv')
        return power_demand.resample(time_unit).sum()

    def annuity(self, interest_rate, lifespan, investment_cost):
        k = interest_rate/(1-(1+interest_rate)**(-lifespan))
        r = investment_cost*k
        return r

    def get_parameters(self,  **kwargs):
        parameters = deepcopy(self._DEFAULT_PARAMETERS)
        parameters.update(kwargs)
        parameters['interest_rate'] = self.input_parameters['interest_rate']['interest_rate']
        
        for resource in pl.Resources:
            conversion_factor=0.003600 #To convert CO2 factor from kg/TJ to kg/MWh
            parameters['prices'][resource] = self.input_parameters['prices'][resource.name]
            parameters['CO2_factor'][resource] = self.input_parameters['CO2_factor'][resource.name]*conversion_factor
        
        return parameters
    
    def make_model(self, parameters, input_data, year=None, scenario=None, seed=None):
        if seed:
            raise NotImplementedError('Randomizer not supported')


        parts, timeindependent_constraint = self.make_parts(parameters)

        model = DispatchModel(t_start=parameters['t_start'],
                              t_end=parameters['t_end'],
                              time_unit=parameters['time_unit'],#) #,
                              timeindependent_constraint = timeindependent_constraint)

        for r in pl.Resources:
            cluster = fs.Cluster(resource=r, name='{} cluster'.format(r))
            cluster.cost = lambda t: 0
            for p in parts:
                if not isinstance(p, fs.parts.FlowNetwork) and (r in p.resources):
                    cluster.add_part(p)
                else:
                    model.add_part(p)
            model.add_part(cluster)

        for p in model.descendants_and_self:
            p.time_unit = parameters['time_unit']
  
        return model

    def make_parts(self, parameters):
        def make_tax_function(*args, **kwargs):
            def tax_function(*args, **kwargs):
                return 0
            return  tax_function

        parts = set()
        taxation = make_tax_function(parameters)
        heat_history = self.get_heat_history(parameters['time_unit'])
        power_demand = heat_history['Electricity']
        
        for r in pl.Resources:
            if r not in [pl.Resources.heat, pl.Resources.CO2]:
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
        
        if self.year == '2030':
            # All renovation data are negative numbers
            renovation_data_1_DH = heat_history['2030 Renovation 1 per cent DH']
            renovation_data_1_Other = heat_history['2030 Renovation 1 per cent Other']
            renovation_data_15_DH = heat_history['2030 renovation 1.5 per cent DH']
            renovation_data_15_Other = heat_history['2030 renovation 1.5 per cent Other']
            
            shallow_renovation_data_1_DH = heat_history['2030 Shallow Renovation 1 per cent DH']
            shallow_renovation_data_1_Other = heat_history['2030 Shallow Renovation 1 per cent Other']
            shallow_renovation_data_15_DH = heat_history['2030 Shallow renovation 1.5 per cent DH']
            shallow_renovation_data_15_Other = heat_history['2030 Shallow renovation 1.5 per cent Other']

        else:
            renovation_data_1_DH = heat_history['2050 Renovation 1 per cent DH']
            renovation_data_1_Other = heat_history['2050 Renovation 1 per cent Other']
            renovation_data_15_DH = heat_history['2050 renovation 1.5 per cent DH']
            renovation_data_15_Other = heat_history['2050 renovation 1.5 per cent Other']

            shallow_renovation_data_1_DH = heat_history['2050 Shallow Renovation 1 per cent DH']
            shallow_renovation_data_1_Other = heat_history['2050 Shallow Renovation 1 per cent Other']
            shallow_renovation_data_15_DH = heat_history['2050 Shallow renovation 1.5 per cent DH']
            shallow_renovation_data_15_Other = heat_history['2050 Shallow renovation 1.5 per cent Other']

        if not 'Trade_off' in scenario:
            renovation = fs.Node(name = input_data['Renovation']['name'])
            renovation.consumption[pl.Resources.heat]= lambda t: renovation_data_1_DH[t]
            renovation.consumption[pl.Resources.natural_gas] = lambda t: renovation_data_1_Other[t]
            renovation.state_variables = lambda t: ()
            renovation.cost = lambda t: 0
            parts.add(renovation)

        else:
            renovation = fs.Node(name = input_data['Renovation']['name'])
            inv_1 = fs.Variable(name= 'inv_1', domain = fs.Domain.binary)
            #inv_0 = fs.Variable(name= 'inv_0', domain = fs.Domain.binary)
            renovation.test = {'investment_cost' : self.annuity(parameters['interest_rate'],input_data['Renovation']['lifespan'],input_data['Renovation']['investment_cost']), 'renovation level': input_data['Renovation']['capacity']}
            renovation.state_variables = lambda t: {}
            renovation.static_variables = {inv_1}#!AK, inv_0}

            renovation.consumption[pl.Resources.heat]= lambda t: renovation_data_1_DH[t]*inv_1
            renovation.consumption[pl.Resources.natural_gas] = lambda t: renovation_data_1_Other[t]*inv_1

            renovation.investment_cost =  self.annuity(parameters['interest_rate'],input_data['Renovation']['lifespan'],input_data['Renovation']['investment_cost']) * inv_1 #+ 0 * inv_0
            renovation.cost = lambda t:0
            parts.add(renovation)
            
            
            renovation_15 = fs.Node(name = input_data['Renovation_15']['name'])
            inv_15 = fs.Variable(name = 'inv_15', domain = fs.Domain.binary)
            #inv_2 = fs.Variable(name = 'inv_2', domain = fs.Domain.binary)
            renovation_15.test = {'investment_cost' : self.annuity(parameters['interest_rate'],input_data['Renovation_15']['lifespan'],input_data['Renovation_15']['investment_cost']), 'renovation level': input_data['Renovation_15']['capacity']}
            renovation_15.state_variables = lambda t: {}
            renovation_15.static_variables ={inv_15}#!AK, inv_2}

            renovation_15.consumption[pl.Resources.heat]= lambda t: renovation_data_15_DH[t]*inv_15
            renovation_15.consumption[pl.Resources.natural_gas] = lambda t: renovation_data_15_Other[t]*inv_15

            renovation_15.investment_cost =  self.annuity(parameters['interest_rate'],input_data['Renovation_15']['lifespan'],input_data['Renovation_15']['investment_cost']) * inv_15 #!AK+ 0 * inv_2
            renovation_15.cost = lambda t:0
            parts.add(renovation_15)
            
            #renovation_const = fs.Eq(inv_0 + inv_1, 1)
            #renovation_const_2 = fs.Eq(inv_1 + inv_2 + inv_15, 1)
            
            # Shallow renovations
            shallow_inv_1 = fs.Variable(name= 'shallow_inv_1', domain = fs.Domain.binary)
            shallow_renovation_1 =fs.Node(name = input_data['Shallow_Renovation_1']['name'])
            shallow_renovation_1.test = {'investment_cost' : self.annuity(parameters['interest_rate'],input_data['Shallow_Renovation_1']['lifespan'],input_data['Shallow_Renovation_1']['investment_cost']), 'renovation level': input_data['Shallow_Renovation_1']['capacity']}
            shallow_renovation_1.state_variables = lambda t: {}
            shallow_renovation_1.static_variables ={shallow_inv_1}
            shallow_renovation_1.consumption[pl.Resources.heat]= lambda t: shallow_renovation_data_1_DH[t]*shallow_inv_1
            shallow_renovation_1.consumption[pl.Resources.natural_gas] = lambda t: shallow_renovation_data_1_Other[t]*shallow_inv_1
            shallow_renovation_1.investment_cost =  self.annuity(parameters['interest_rate'],input_data['Shallow_Renovation_1']['lifespan'],input_data['Shallow_Renovation_1']['investment_cost']) * shallow_inv_1
            shallow_renovation_1.cost = lambda t: 0
            parts.add(shallow_renovation_1)

            shallow_inv_15 = fs.Variable(name= 'shallow_inv_15', domain = fs.Domain.binary)
            shallow_renovation_15 =fs.Node(name = input_data['Shallow_Renovation_15']['name'])
            shallow_renovation_15.test = {'investment_cost' : self.annuity(parameters['interest_rate'],input_data['Shallow_Renovation_15']['lifespan'],input_data['Shallow_Renovation_15']['investment_cost']), 'renovation level': input_data['Shallow_Renovation_15']['capacity']}
            shallow_renovation_15.state_variables = lambda t: {}
            shallow_renovation_15.static_variables ={shallow_inv_15}
            shallow_renovation_15.consumption[pl.Resources.heat]= lambda t: shallow_renovation_data_15_DH[t]*shallow_inv_15
            shallow_renovation_15.consumption[pl.Resources.natural_gas] = lambda t: shallow_renovation_data_15_Other[t]*shallow_inv_15
            shallow_renovation_15.investment_cost =  self.annuity(parameters['interest_rate'],input_data['Shallow_Renovation_15']['lifespan'],input_data['Shallow_Renovation_15']['investment_cost']) * shallow_inv_15
            shallow_renovation_15.cost = lambda t: 0
            parts.add(shallow_renovation_15)

            renovation_const_1 = fs.LessEqual(shallow_inv_15+inv_15 + shallow_inv_1+inv_1, 1)




            #shallow_renovation_15 = fs.Node(name = input_data['Shallow_Renovation_15']['Name'])

            
        city = fs.Node(name='City')
        
        city.state_variables = lambda t: {}

        if scenario in 'Max_DH':
            if self.year == '2030':
                city.consumption[pl.Resources.heat] =  lambda t: heat_history['DH'][t]+heat_history['2030 DH expansion'][t]
            else:
                city.consumption[pl.Resources.heat] =  lambda t: heat_history['DH'][t]+heat_history['2050 DH expansion'][t]
        else:
            city.consumption[pl.Resources.heat] =  lambda t: heat_history['DH'][t]

        city.consumption[pl.Resources.power] =lambda t: power_demand[t]
        city.cost = lambda t: power_demand[t] * parameters['prices'][pl.Resources.power]
        parts.add(city) 

        # Removing taxes according to excel Innsbruck_v3 sheet electricity cotst italy
        power_export_price = (parameters['prices'][pl.Resources.power]-(0.0612+0.00658)*1000)/1.1
        powerExport = pl.Export(resource = pl.Resources.power,
                                price =  power_export_price,
                                name='power export')
        parts.add(powerExport)
        
        CO2 = pl.Export(resource = pl.Resources.CO2,
                        price = 0,
                        name = 'CO2_emissions')
        CO2.time_unit = parameters['time_unit']
        parts.add(CO2)

        "Timeindependent constraint on maximum CO2 emissions during the whole timeperiod"
        times = CO2.times_between(parameters['t_start'], parameters['t_end'])
        emissions = fs.Sum(CO2.consumption[pl.Resources.CO2](t) for t in times)
        CO2_maximum = fs.LessEqual(emissions, 100000000000) #below 24 069 146 limit the CO2 emissions
        
        heating = fs.Node(name='Heating') #se till att heat_history['Other'] minskar när DH byggs ut och blir större
        if self.scenario in 'Max DH':
            heating.consumption[pl.Resources.natural_gas] = lambda t: (heat_history['Other heating'][t]- heat_history['{} DH expansion'.format(self.year)][t])*0.8/0.95 #verkningsgrad gasuppvärmning
        else:
            heating.consumption[pl.Resources.natural_gas] = lambda t: (heat_history['Other heating'][t])*0.8/0.95 #verkningsgrad gasuppvärmning
        heating.consumption[pl.Resources.power] = lambda t: 10 #heat_history['Other'][t]*0.2/0.97  #verkningsgrad eluppvärmning
        heating.cost = lambda t: 0
        heating.state_variables = lambda t: {}
        parts.add(heating)

        CHP_A = pl.LinearCHP(name='Existing CHP A', eta=0.776, alpha=0.98, Fmax= 4.27 / hour, fuel=pl.Resources.natural_gas, taxation=taxation)
        # Fmin= 2.33 / hour, start_steps=int(np.round(.5 * hour)), 
        parts.add(CHP_A)        

        CHP_B =pl.LinearCHP(name='Existing CHP B', eta=0.778, alpha=0.98, Fmax= 4.27 /hour, fuel=pl.Resources.natural_gas, taxation=taxation)
        # Fmin= 2.33 / hour, start_steps=int(np.round(.5 * hour)),
        parts.add(CHP_B) 
    
        parts.add(pl.Boiler(name='Existing Boiler A', eta=0.9, Fmax=8.84 / hour, fuel=pl.Resources.natural_gas, taxation=taxation))

        parts.add(pl.Boiler(name='Existing Boiler B',eta=0.87, Fmax=8.84 / hour, fuel=pl.Resources.natural_gas, taxation=taxation))

        parts.add(pl.Boiler(name='Existing Boiler C', eta=0.89, Fmax=8.84 / hour, fuel=pl.Resources.natural_gas, taxation=taxation))
        
        parts.add(pl.Boiler(name='Existing Boiler D', eta= 0.77, Fmax= 8.84 / hour, fuel=pl.Resources.natural_gas, taxation=taxation))


        # Running waste incinerator at 25 MW output max according to D4.2 p 32, techincal limit is 45
        parts.add(
            pl.LinearCHP(name='Existing Waste Incinerator', fuel=pl.Resources.waste, alpha=0.46, eta=0.81, Fmax= 25/hour, taxation=taxation)
            )  
        
        parts.add(
            pl.Accumulator(name='Existing Accumulator', resource=pl.Resources.heat, max_flow=60/hour, max_energy= 220, loss_factor = 0.005, t_start = parameters['t_start'], t_end = parameters['t_end'])
            )

        """ Production alternatives for the scenarios"""
        
        solar_data=self.get_solar_data(parameters['time_unit'])
        parts.add(
            pl.LinearCHP(
                name = input_data['CHP']['name'],
                eta = input_data['CHP']['eta'],
                alpha = input_data['CHP']['alpha'],
                Fmax = input_data['CHP']['capacity'] /hour,
                fuel =  input_data['CHP']['resource'],
                taxation = input_data['CHP']['taxation'],  #ska vara taxation här men fick inte rätt då
                investment_cost = self.annuity(parameters['interest_rate'], input_data['CHP']['lifespan'], input_data['CHP']['investment_cost']),
                max_capacity =  input_data['CHP']['max_capacity']/hour if input_data['CHP']['max_capacity'] else input_data['CHP']['max_capacity']
                )
        )
        
        if '2050' in year:
            if 'Trade_off' in scenario:
                parts.add(
                    pl.LinearCHP(
                    name = input_data['CHP invest']['name'],
                    eta = input_data['CHP invest']['eta'],
                    alpha = input_data['CHP invest']['alpha'],
                    Fmax = input_data['CHP invest']['capacity'] /hour,
                    max_capacity = input_data['CHP invest']['max_capacity']/hour,
                    fuel =  input_data['CHP invest']['resource'],
                    taxation = input_data['CHP invest']['taxation'],  #ska vara taxation här men fick inte rätt då
                    investment_cost = self.annuity(parameters['interest_rate'], input_data['CHP invest']['lifespan'], input_data['CHP invest']['investment_cost'])))
        
        parts.add(
            pl.SolarPV(
                name = input_data['SolarPV']['name'],
                G = solar_data['Mean Irradiance [W/m2]'],
                T = solar_data['Mean temperature [C]'], 
                max_capacity = None if input_data['SolarPV']['max_capacity'] is None else float(input_data['SolarPV']['max_capacity']),
                capacity = input_data['SolarPV']['capacity']/hour, #Eller capacity borde väl inte anges för investment option
                taxation = input_data['SolarPV']['taxation'], 
                investment_cost = self.annuity(parameters['interest_rate'], input_data['SolarPV']['lifespan'], input_data['SolarPV']['investment_cost'])))
        
        if '2050' in year:
            parts.add(
                pl.Accumulator(
                    name = input_data['Accumulator']['name'],
                    resource =  input_data['Accumulator']['resource'], 
                    max_flow = input_data['Accumulator']['max_flow']/hour, 
                    max_energy = input_data['Accumulator']['max_energy'], 
                    loss_factor = input_data['Accumulator']['loss_factor']/hour,
                    max_capacity = input_data['Accumulator']['max_capacity'],
                    investment_cost = self.annuity(parameters['interest_rate'], input_data['Accumulator']['lifespan'], input_data['Accumulator']['investment_cost']),
                    t_start = parameters['t_start'],
                    t_end = parameters['t_end']))  
        
        timeindependent_constraint = []
        if 'Trade_off_CO2' in scenario:
            timeindependent_constraint = [CO2_maximum] #, renovation_const, renovation_const_2]
        elif 'Trade_off' in scenario:
            timeindependent_constraint = [renovation_const_1] # ,renovation_const, renovation_const_2] #!AK
        else:
            timeindependent_constraint = []
        
        return parts, timeindependent_constraint
        

price_scenarios = {
    '2030' : {
        'Italy medium' : {
            'natural_gas': 38.62104,
            'power': 247.19, 
            'heat': 0,
            'waste': 2,
            'biomass': 23.33,
            'CO2': 25,
            'interest_rate': None,
        },
        'Italy pessimistic' : {
            'natural_gas': 35.51381,
            'power': 204.4159,
            'heat': 0,
            'waste': 2,
            'biomass': 32.80,
            'CO2': 34,
            'interest_rate': None,
        },
        'SD' : {
            'natural_gas': 30.39,
            'power': 121.5048,
            'heat': 0,
            'waste': 2,
            'biomass': 32.16,
            'CO2': 80,
            'interest_rate': None,
        },
        'NP' : {
            'natural_gas': 34.81,
            'power': 121.5048,
            'heat': 0,
            'waste': 2,
            'biomass': 15.31,
            'CO2': 29,
            'interest_rate': None,
        }
    },
    '2050' : {
        'Italy medium' : {
            'natural_gas': 31.04095,
            'power': 233.90,
            'heat': 0,
            'waste': 2,
            'biomass': 94.45,
            'CO2': 234,
            'interest_rate': None,
        },
        'Italy pessimistic' : {
            'natural_gas': 40.64786,
            'power': 202.4691,
            'heat': 0,
            'waste': 2,	
            'biomass': 44.67,
            'CO2': 90,
            'interest_rate': None,
        },
        'SD' : {
            'natural_gas': 34.47,
            'power': 127.0048,
            'heat': 0,
            'waste': 2,
            'biomass': 63.34,  
            'CO2': 172,	
            'interest_rate': None,
        },
        'NP' : {
            'natural_gas': 41.62,
            'power': 127.0048,
            'heat': 0,
            'waste': 2, 
            'biomass': 23.58,
            'CO2': 57,
            'interest_rate': None,
        }
    }
}

total_results = dict()
if __name__ == "__main__":
    
    data=read_data('C:/Users/AlexanderKa/Desktop/Github/T4-4/input/scenario_data_v2.xlsx')
    scenario_start_time = pd.Timestamp.now()
    print('Beginning scenario loop at {}'.format(scenario_start_time))
    for price_scenario in ['Italy medium', 'Italy pessimistic', 'SD', 'NP']:
        for year in ['2030', '2050']:
            for CO2_cost in ['CO2_cost', 'No_CO2_cost']:
                input_parameters=data[year+'_input_parameters']
                interest_rate = 0.028 #input_parameters['prices']['interest_rate']
                input_parameters['prices'] = price_scenarios[year][price_scenario]
                input_parameters['prices']['interest_rate'] = interest_rate
                if CO2_cost in 'No_CO2_cost':
                    input_parameters['prices']['CO2'] = 0

                for scenario in ['BAU', 'Max_RES', 'Max_DH', 'Max_Retrofit', 'Trade_off']: 
                    print('Running {}_{}_{}_{}'.format(year, scenario, price_scenario, CO2_cost))
                    input_data=data[year+'_'+scenario]
                    
                    model = CityModel(input_data, input_parameters, year, scenario)
                    model.RunModel()
                    parameters = model.get_parameters()
                    
                    
                    results = process_results(model, parameters, pl.Resources, year, scenario, price_scenario, input_data, CO2_cost)
                    scenario_name = year+"_"+scenario+"_"+price_scenario+"_"+CO2_cost
                    total_results[scenario_name] = results
                    total_results[scenario_name]['interest rate'] = interest_rate
    
    scenario_end_time = pd.Timestamp.now()
    print('Finished scenario loop at {}, total time elapsed: {}'.format(scenario_end_time, scenario_end_time-scenario_start_time))
    
    
    final_results = final_processor(total_results,
                                    output_path = "C:/Users\AlexanderKa/Desktop/Github/T4-4/output/total/",
                                    base_case = '2030_BAU_Italy medium_No_CO2_cost')
    winsound.PlaySound("*", winsound.SND_ALIAS)
    