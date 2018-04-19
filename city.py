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
                pl.Resources.waste: 7777,
                pl.Resources.CO2: 0
                },
            'CO2_factor': {
                pl.Resources.natural_gas: 5,
                pl.Resources.power: 5,
                pl.Resources.heat: 5,
                pl.Resources.waste: 15,
                pl.Resources.CO2: 0
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
    """
    def get_heat_history(self, time_unit):
        heat_history = self.read_csv('test_data.csv')
        return heat_history.resample(time_unit).sum()

    def get_heat_history_industry(self, time_unit):
        heat_history_industry = self.read_csv('industrial_load_generated.csv')
        return heat_history_industry.resample(time_unit).sum()
    """
    def get_solar_data(self, time_unit):
        solar_data = pd.read_csv(
            'C:/Users/lovisaax/Desktop/solar_data.csv',
                encoding='utf-8',
                index_col='Time',
                parse_dates=True,
                squeeze=True)
        return solar_data.resample(time_unit).sum()

    def get_production_data(self, **kwargs):
        
        """calculate required production data for solar PV"""
        parameters = self.get_parameters() #Lyckas inte bli av med dessa två raderna i inläsningen av soldatan...
        solar_data=self.get_solar_data(parameters['time_unit']) ###

        production_data = {
            'CHP invest' :{
            'name':'CHP invest',
            'eta' : 0.75, #Titta så att den här är rätt, är eta = n_el + n__thermal??
            'alpha' : 0.98, #Kontrollera denna, är alpha = n_el/n_thermal --> 0.5.
            'start_steps' : int(np.round(.5 * 1)),#bytte ut hour mot 1 här för att få det att fungera.
            'max_capacity' : 35,
            'fuel' : pl.Resources.natural_gas,
            'taxation' : 1,  #ska vara taxation här men fick inte rätt då
            'investment_cost' : 100
            },  
            'Accumulator invest':{
            'name' : 'Accumulator invest',
            'resource' : pl.Resources.heat,
            'max_flow' : 20/1, #Bytte ut hour mot 1. Ska max_flow vara 6 för denna också?
            'max_energy' : 80, 
            'loss_factor' : 0,
            'max_capacity' : 20,
            'investment_cost' : 1
            },

            'SolarPV' : {
                'name' : 'SolarPV invest',
                'G' : solar_data['irradiation'],
                'T' : solar_data['temperature'], 
                'max_capacity' : 20,
                'capacity' : 10,
                'taxation' : None, 
                'investment_cost' : 10
        }
            }
        return production_data

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
        
        #heat_history = self.get_heat_history(parameters['time_unit'])
        hour = pd.Timedelta('1h') / parameters['time_unit']
        series_reader = lambda series: series.loc.__getitem__
        city = fs.Node(name='City')
        import math
        city.consumption[pl.Resources.heat] = lambda t: 30 + 5*math.sin(t.value)
        #series_reader(heat_history)
        city.consumption[pl.Resources.power]= lambda t: 13
        city.cost = lambda t: 0
        city.state_variables = lambda t: ()
        parts.add(city)

        Industry = fs.Node(name='Industry')
        Industry.consumption[pl.Resources.heat] = lambda t: 30
        Industry.cost = lambda t: 0
        Industry.state_variables = lambda t: ()
        parts.add(Industry)

        powerExport = pl.Export(resource = pl.Resources.power,
                             capacity=1000 / hour, # Arbitrarily chosen, assumed higher than combined production
                             price = parameters['prices'][pl.Resources.power]/10)
        parts.add(powerExport)

        def maximum_CO2(CO2_cap):       
            def CO2_constraint(t):
                t_start = parameters['t_start']
                t_end = parameters['t_end']
                times = CO2.times_between(t_start, t_end)
                emissions = fs.Sum(CO2.consumption[pl.Resources.CO2](tid) for tid in times)
                return fs.LessEqual(emissions, CO2_cap)
            return CO2_constraint

        CO2 = fs.Node(name = 'CO2_emissions')
        capacity=5000/hour
        quantity = fs.VariableCollection(lb=0, ub=capacity)

        CO2.consumption[pl.Resources.CO2] = lambda t: quantity(t)
        CO2.cost = lambda t: 0
        CO2.state_variables = lambda t: {quantity(t)}
        CO2.constraints += maximum_CO2(100000000)

        parts.add(CO2)

        parts.add(
            pl.LinearSlowCHP(
                name='Existing CHP A',
                eta=0.776, # was 77.6
                alpha=0.98,
                Fmax= 4.27 / hour,  # 449.0 / hour,  # 449 m3/hour
                Fmin= 2.33 / hour,  # 245.0 / hour,  # 245 m3/hour
                #start_steps=int(np.round(.5 * hour)),
                fuel=pl.Resources.natural_gas,
                taxation=taxation))
        
        parts.add(
            pl.LinearSlowCHP(
                name='Existing CHP B',
                eta=0.778, #was 77.8
                alpha=0.98,
                Fmax= 4.27 /hour, # 449.0 / hour,  # 449 m3/hour
                Fmin=2.33 / hour,  # 245.0 / hour,  # 245 m3/hour
                start_steps=int(np.round(.5 * hour)),
                fuel=pl.Resources.natural_gas,
                taxation=taxation))

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
        
        parts.add(
            pl.LinearSlowCHP(
                name='Existing Waste Incinerator',
                start_steps=12,
                fuel=pl.Resources.waste,
                alpha=0.46,
                eta=0.81,
                Fmin=10 / hour,
                Fmax=45 /hour, # Update to reflect 25 MW output max according to D4.2 p 32 
                taxation=taxation))        
        
        parts.add(
            pl.Accumulator(
                name='Existing Accumulator',
                resource=pl.Resources.heat,
                max_flow=60/hour, 
                max_energy= 220,
                loss_factor = 0))   

        """ Investment alternatives for the scenarios"""
        production_data = self.get_production_data()

        parts.add(
            pl.LinearSlowCHP(
                name=production_data['CHP invest']['name'],
                eta=production_data['CHP invest']['eta'], 
                alpha=production_data['CHP invest']['alpha'], 
                start_steps= production_data['CHP invest']['start_steps'],
                max_capacity = production_data['CHP invest']['max_capacity'], 
                fuel=production_data['CHP invest']['fuel'], 
                taxation= production_data['CHP invest']['taxation'],
                investment_cost = production_data['CHP invest']['investment_cost']))

        parts.add(
            pl.Accumulator(
                name=production_data['Accumulator invest']['name'],
                resource= production_data['Accumulator invest']['resource'],
                max_flow=production_data['Accumulator invest']['max_flow'], 
                max_energy= production_data['Accumulator invest']['max_energy'], 
                loss_factor = production_data['Accumulator invest']['loss_factor'], 
                max_capacity = production_data['Accumulator invest']['max_capacity'],
                investment_cost = production_data['Accumulator invest']['investment_cost']))     
        
        parts.add(
            pl.SolarPV(
                name = production_data['SolarPV']['name'],
                G = production_data['SolarPV']['G'],
                T = production_data['SolarPV']['T'],
                max_capacity = production_data['SolarPV']['max_capacity'],
                capacity = production_data['SolarPV']['capacity'],
                taxation = production_data['SolarPV']['taxation'], 
                investment_cost = production_data['SolarPV']['investment_cost'])) 
        
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
    
    def DisplayResult(self):
        from process_results import is_producer

        t_start = self._DEFAULT_PARAMETERS['t_start']
        t_end = self._DEFAULT_PARAMETERS['t_end']
        heat_producers = [p for p in self.m.descendants
                          if is_producer(p, pl.Resources.heat) and
                          not isinstance(p, fs.Cluster)]
        
        times = self.m.times_between(t_start, t_end)
        
        heat = {p.name: fs.get_series(p.production[pl.Resources.heat], times) for p in heat_producers}
        heat = pd.DataFrame.from_dict(heat)

        storage_times = self.m.times_between(t_start, t_end)
        storage = [p for p in self.m.descendants if isinstance(p, pl.Accumulator)]
        stored_energy = {p.name: fs.get_series(p.volume, storage_times) for p in storage}
        stored_energy = pd.DataFrame.from_dict(stored_energy)

        p = heat.plot(kind='area', legend='reverse', lw=0, figsize=(8,8))
        p.get_legend()       
        s = stored_energy.plot(kind='area', legend='reverse', lw=0, figsize=(8,8))
        s.get_legend().set_bbox_to_anchor((0.5, 1))
        plt.show()
        plt.close()
            
        return 

    def save_results(self, year, scenario, results, output_data_path):#, heat, power):
        import xlsxwriter
        #this writes the production_data to an excel_sheet, but does not include the values...
        try:   
            workbook=xlsxwriter.Workbook(output_data_path+'output_%s_%s.xlsx' %(year, scenario))
            worksheet = workbook.add_worksheet()
            row = 0
            col= 0

            for key in results.keys():
                worksheet.write(row, col, key)
                for item in results[key]:
                    worksheet.write(row, col+1, item)
                    row += 1
            workbook.close()

        except PermissionError:
            time=str(datetime.datetime.now().time())
            time=time.replace(":", ".")
            writer= pd.ExcelWriter(output_data_path+'output_%s_%s_%s.xlsx' %(year,scenario,time), engine='xlsxwriter')
            for sheet_name, data in results.items():
                data.to_excel(writer, sheet_name='%s'%sheet_name)
            writer.save()

        """
        writer = pd.ExcelWriter(output_data_path+'output_%s_%s.xlsx' %(year,scenario), engine='xlsxwriter')

        #this does not accept e.g. resources.natural_gas as an input
        results = pd.DataFrame(results)
        import pdb

        for sheet_name, data in results.items():
            data.to_excel(writer)#, float_format='x', na_rep = 'Nan')#sheet_name='%s'%sheet_name)
        writer.save()
        """
        return

if __name__ == "__main__":
    print('Running city.py standalone')
    import pdb
    model = CityModel()
    model.RunModel()
    parameters = model.get_parameters()

    from process_results import process_results
    process_results(model, parameters, pl.Resources)
    
    
    """
    production_data = model.get_production_data()
    model.save_results('2030', 'BAU', production_data, 'C:/Users/lovisaax/Desktop/test/')
    """