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
            if resource is pl.Resources.pvpower:
                continue
            conversion_factor=0.003600 #To convert CO2 factor from kg/TJ to kg/MWh
            parameters['prices'][resource] = self.input_parameters['prices'][resource.name]
            parameters['CO2_factor'][resource] = self.input_parameters['CO2_factor'][resource.name]*conversion_factor
        
        parameters['CO2_factor'][pl.Resources.pvpower] = parameters['CO2_factor'][pl.Resources.power]
        parameters['prices'][pl.Resources.pvpower] = parameters['prices'][pl.Resources.power]
        
        return parameters
    
    def make_model(self, parameters, input_data, year=None, scenario=None, seed=None):
        if seed:
            raise NotImplementedError('Randomizer not supported')


        parts, timeindependent_constraint = self.make_parts(parameters)

        model = DispatchModel(t_start=parameters['t_start'],
                              t_end=parameters['t_end'],
                              time_unit=parameters['time_unit'],#) #,
                              timeindependent_constraint = timeindependent_constraint)
        """
        pv_export_pipe = fs.FlowNetwork(resource= pl.Resources.power, name = 'PV export pipe')
        parts.add(pv_export_pipe)
        pv_city_pipe = fs.FlowNetwork(resource= pl.Resources.power, name = 'PV city pipe')
        parts.add(pv_city_pipe)
        """
        """
        pv_power_export = pl.Export(resource = pl.Resources.power,
                                    price = power_export_price,
                                    name = 'PV Power export'
                                    """
        """ PV_power_export <--< PV >--> city """

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
        from cases import cases as investment_option_dict

        parts = set()
        heat_history = self.get_heat_history(parameters['time_unit'])
        power_demand = heat_history['Electricity']
        hour = pd.Timedelta('1h') / parameters['time_unit']
        power_export_price = (parameters['prices'][pl.Resources.power]-(0.0612+0.00658)*1000)/1.1

        for r in pl.Resources:
            if r not in [pl.Resources.heat, pl.Resources.CO2]:
                parts.add(
                    pl.Import(
                        resource=r,
                        price=parameters['prices'][r],
                        name='Import({})'.format(r),
                        CO2_factor=parameters['CO2_factor'][r]))
        

        
        # All renovation data are negative numbers
        renovation_data_1_DH = heat_history['{} Renovation 1 per cent DH'.format(year)]
        renovation_data_1_Other = heat_history['{} Renovation 1 per cent Other'.format(year)]
        renovation_data_15_DH = heat_history['{} renovation 1.5 per cent DH'.format(year)]
        renovation_data_15_Other = heat_history['{} renovation 1.5 per cent Other'.format(year)]
        
        shallow_renovation_data_1_DH = heat_history['{} Shallow Renovation 1 per cent DH'.format(year)]
        shallow_renovation_data_1_Other = heat_history['{} Shallow Renovation 1 per cent Other'.format(year)]
        shallow_renovation_data_15_DH = heat_history['{} Shallow renovation 1.5 per cent DH'.format(year)]
        shallow_renovation_data_15_Other = heat_history['{} Shallow renovation 1.5 per cent Other'.format(year)]

        inv_1 = fs.Variable(name= '1 per cent deep renovation', lb = investment_option_dict[year][scenario]['1 per cent deep']['capacity lb'], ub = investment_option_dict[year][scenario]['1 per cent deep']['capacity ub'], domain = fs.Domain.binary)
        inv_15 =fs.Variable( name = '1.5 per cent deep renovation', lb = investment_option_dict[year][scenario]['1.5 per cent deep']['capacity lb'], ub = investment_option_dict[year][scenario]['1.5 per cent deep']['capacity ub'], domain = fs.Domain.binary)
        shallow_inv_1 = fs.Variable(name= '1 per cent shallow renovation', lb = investment_option_dict[year][scenario]['1 per cent shallow']['capacity lb'], ub = investment_option_dict[year][scenario]['1 per cent shallow']['capacity ub'], domain = fs.Domain.binary)
        shallow_inv_15 = fs.Variable(name= '1.5 per cent shallow renovation', lb = investment_option_dict[year][scenario]['1.5 per cent shallow']['capacity lb'], ub = investment_option_dict[year][scenario]['1.5 per cent shallow']['capacity ub'], domain = fs.Domain.binary)
        
        
        deep_1_cost = self.annuity(parameters['interest_rate'], 40, investment_option_dict[year][scenario]['1 per cent deep']['specific investment cost'])
        deep_15_cost = self.annuity(parameters['interest_rate'], 40, investment_option_dict[year][scenario]['1.5 per cent deep']['specific investment cost'])
        shallow_1_cost = self.annuity(parameters['interest_rate'], 40, investment_option_dict[year][scenario]['1 per cent shallow']['specific investment cost'])
        shallow_15_cost = self.annuity(parameters['interest_rate'], 40, investment_option_dict[year][scenario]['1.5 per cent shallow']['specific investment cost'])

        renovation_non_dh_heating = lambda t: shallow_renovation_data_1_Other[t] * shallow_inv_1 \
                                            + shallow_renovation_data_15_Other[t] * shallow_inv_15 \
                                            + renovation_data_1_Other[t] * inv_1 \
                                            + renovation_data_15_Other[t] * inv_15
        renovation_dh_heating = lambda t: shallow_renovation_data_1_DH[t] * shallow_inv_1 \
                                            + shallow_renovation_data_15_DH[t] * shallow_inv_15 \
                                            + renovation_data_1_DH[t] * inv_1 \
                                            + renovation_data_15_DH[t] * inv_15


        grid_expansion_variable = fs.Variable(lb = investment_option_dict[year][scenario]['DH grid expansion']['capacity [MWh per y] lb'], 
                                     ub = investment_option_dict[year][scenario]['DH grid expansion']['capacity [MWh per y] ub'],
                                     name='DH grid expansion in 1000 MWh')
        grid_expansion_cost = self.annuity(parameters['interest_rate'], 100, investment_option_dict[year][scenario]['DH grid expansion']['specific investment cost [EUR per GWh]'])

        city = fs.Node(name='City')
        city.consumption[pl.Resources.heat] = lambda t: heat_history['DH'][t]  + grid_expansion_variable * heat_history['1000 MWh expansion'][t] + renovation_dh_heating(t)
        city.consumption[pl.Resources.power] =lambda t: power_demand[t]
        city.cost = lambda t: power_demand[t] * parameters['prices'][pl.Resources.power]
        city.investment_cost = grid_expansion_variable * grid_expansion_cost + inv_1 * deep_1_cost + inv_15 * deep_15_cost + shallow_inv_1 * shallow_1_cost + shallow_inv_15 * shallow_15_cost 
        city.state_variables = lambda t: {}
        city.static_variables = {grid_expansion_variable, inv_1, inv_15, shallow_inv_1, shallow_inv_15}
        parts.add(city)     


        heating = fs.Node(name='Heating') #se till att heat_history['Other'] minskar när DH byggs ut och blir större
        non_dh_heating_consumption = lambda t: heat_history['Other heating'][t]  - grid_expansion_variable * heat_history['1000 MWh expansion'][t] + renovation_non_dh_heating(t)
        heating.consumption[pl.Resources.natural_gas] = lambda t: 0.8 * non_dh_heating_consumption(t) / 0.95 # Verkningsgrad gasuppvärmning
        heating.consumption[pl.Resources.power] = lambda t: 0.2 * non_dh_heating_consumption(t) / 0.97 # Verkningsgrad eluppvärmning
        heating.cost = lambda t: heating.consumption[pl.Resources.power](t) * parameters['prices'][pl.Resources.power]
        heating.state_variables = lambda t: {}
        heating.static_variables = {grid_expansion_variable, inv_1, inv_15, shallow_inv_1, shallow_inv_15}        
        parts.add(heating)

        # Removing taxes according to excel Innsbruck_v3 sheet electricity cotst italy
        powerExport = pl.Export(resource = pl.Resources.power,
                                price =  0,
                                name='power export')
        parts.add(powerExport)

        pv_power_export = pl.Export(resource = pl.Resources.pvpower,
                                    price = power_export_price,
                                    name = 'PV Power export')
        parts.add(pv_power_export)
        
        CO2_emissions = pl.Export(resource = pl.Resources.CO2,
                        price = 0,
                        name = 'CO2_emissions')
        CO2_emissions.time_unit = parameters['time_unit']
        parts.add(CO2_emissions)


        """ Production Units """
        parts.add(pl.LinearCHP(name='Existing CHP A', eta=0.776, alpha=0.98, capacity_lb= 4.27, capacity_ub = 4.27 , fuel=pl.Resources.natural_gas, running_cost = -power_export_price, hour = hour))
        parts.add(pl.LinearCHP(name='Existing CHP B', eta=0.778, alpha=0.98, capacity_lb= 4.27, capacity_ub = 4.27, fuel=pl.Resources.natural_gas, running_cost = -power_export_price, hour = hour))
    
        parts.add(pl.Boiler(name='Existing Boiler A', eta=0.9, Fmax=8.84, fuel=pl.Resources.natural_gas, hour = hour))
        parts.add(pl.Boiler(name='Existing Boiler B',eta=0.87, Fmax=8.84, fuel=pl.Resources.natural_gas, hour = hour))
        parts.add(pl.Boiler(name='Existing Boiler C', eta=0.89, Fmax=8.84, fuel=pl.Resources.natural_gas, hour = hour))    
        parts.add(pl.Boiler(name='Existing Boiler D', eta= 0.77, Fmax= 8.84, fuel=pl.Resources.natural_gas, hour = hour))

        # Running waste incinerator at 25 MW output max according to D4.2 p 32, techincal limit is 45
        parts.add(pl.LinearCHP(name='Existing Waste Incinerator', eta=0.81, alpha=0.46, capacity_lb= 45, capacity_ub= 45, fuel=pl.Resources.waste, running_cost = -power_export_price, hour = hour))  
        
        parts.add(pl.Accumulator(name='Existing Accumulator', resource=pl.Resources.heat, max_flow=60, capacity_lb= 220, capacity_ub= 220, loss_factor = 0.005, t_start = parameters['t_start'], t_end = parameters['t_end'], hour = hour))
        
        """ Production alternatives for the scenarios"""
        parts.add(
            pl.LinearCHP(
                name = 'Natural gas CHP',
                alpha = 0.98,
                eta = 0.75,
                capacity_lb = investment_option_dict[year][scenario]['NG CHP']['capacity [MW] lb'],
                capacity_ub = investment_option_dict[year][scenario]['NG CHP']['capacity [MW] ub'],
                specific_investment_cost = self.annuity(parameters['interest_rate'], 25, investment_option_dict[year][scenario]['NG CHP']['specific investment cost']),
                fuel =  pl.Resources.natural_gas,
                running_cost = -power_export_price,
                hour = hour
                )
        )
        
        parts.add(
            pl.LinearCHP(
                name = 'Biomass CHP',
                alpha = 0.98,
                eta = 0.7,
                capacity_lb = investment_option_dict[year][scenario]['Bio CHP']['capacity [MW] lb'],
                capacity_ub = investment_option_dict[year][scenario]['Bio CHP']['capacity [MW] ub'],
                specific_investment_cost = self.annuity(parameters['interest_rate'], 25, investment_option_dict[year][scenario]['Bio CHP']['specific investment cost']),
                fuel =  pl.Resources.natural_gas,
                running_cost = -power_export_price,
                hour = hour
                )
        )
        
        solar_data=self.get_solar_data(parameters['time_unit'])
        parts.add(
            pl.SolarPV(
                name = input_data['SolarPV']['name'],
                G = solar_data['Mean Irradiance [W/m2]'],
                T = solar_data['Mean temperature [C]'], 
                capacity_lb = investment_option_dict[year][scenario]['PV']['capacity [MW] lb'],
                capacity_ub = investment_option_dict[year][scenario]['PV']['capacity [MW] ub'],
                specific_investment_cost = self.annuity(parameters['interest_rate'], input_data['SolarPV']['lifespan'], investment_option_dict[year][scenario]['PV']['specific investment cost']),
                running_cost = -power_export_price,
                hour = hour
            )
        )
                
        parts.add(
            pl.Accumulator(
                name = 'New Accumulator',
                resource = pl.Resources.heat, 
                max_flow = investment_option_dict[year][scenario]['Accumulator']['max flow [MWh perh]'], 
                capacity_lb = investment_option_dict[year][scenario]['Accumulator']['capacity [MWh] lb'],
                capacity_ub = investment_option_dict[year][scenario]['Accumulator']['capacity [MWh] ub'],
                loss_factor = 0.005,
                specific_investment_cost = self.annuity(parameters['interest_rate'], input_data['Accumulator']['lifespan'], investment_option_dict[year][scenario]['Accumulator']['specific investment cost']),
                t_start = parameters['t_start'],
                t_end = parameters['t_end'],
                hour = hour
            )
        )  
    
        timeindependent_constraint = []
        renovation_const_1 = fs.LessEqual(shallow_inv_15+inv_15 + shallow_inv_1+inv_1, 1)
        minimum_renovation = fs.Eq(1, inv_1+inv_15+shallow_inv_1+shallow_inv_15)
        if 'Trade_off' in scenario:
            timeindependent_constraint = [minimum_renovation]
            #renovation_const_1
            #timeindependent_constraint = [inv_1_lb, inv_1_ub, inv_15_lb, inv_15_ub, shallow_inv_1_lb, shallow_inv_1_ub, shallow_inv_15_lb, shallow_inv_15_ub] 
        #else:
            #timeindependent_constraint = [inv_1_lb, inv_1_ub, inv_15_lb, inv_15_ub, shallow_inv_1_lb, shallow_inv_1_ub, shallow_inv_15_lb, shallow_inv_15_ub]
        
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

                for scenario in ['BASE', 'BAU', 'Max_RES', 'Max_DH', 'Max_Retrofit', 'Trade_off']: 
                    print('Running {}_{}_{}_{}'.format(year, scenario, price_scenario, CO2_cost))
                    if scenario in 'BASE':
                        input_data = data[year+'_BAU']
                    else:
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
                                    base_case = '2030_BASE_Italy medium_No_CO2_cost')
    winsound.PlaySound("*", winsound.SND_ALIAS)
    