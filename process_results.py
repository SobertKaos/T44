# -*- coding: utf-8 -*-
import pandas as pd
import friendlysam as fs
import partlib as pl
import pdb
from itertools import chain, product

def process_results(model, parameters, Resources, year, scenario, price_scenario, data, CO2_cost):

    m = model.m
    parts=m.descendants

    input_data = get_input_data(parts, data)
    investment_data=get_investment_data(parts, scenario)
    production, stored_energy, power_production = production_results(m, parameters, parts, Resources)
    consumption, power_consumers = consumption_results(m, parameters, parts, Resources)
    [total_results, static_variables, CO2_emissions] = get_total_results(m, parameters, parts, Resources, scenario)

    waste_consumers=waste_consumption(m, parameters, parts, Resources)
    import_resources = resource_consumption(m, parameters, parts, Resources)
    
    prices = dict()
    for resource, price in parameters['prices'].items():
        prices[resource._name_] = price

    total= {'input for scenario':input_data, 'input investment_data':investment_data, 'production':production,
    'consumption':consumption, 'invest or not': static_variables, 'total cost and emissions':total_results, 'stored_energy':stored_energy,
    'waste consumers': waste_consumers, 'CO2_emissions': CO2_emissions, 'power_production':power_production, 'power_consumers': power_consumers,
    'import resources': import_resources, 'prices': prices}
    save_results_excel(m, parameters, year, scenario, price_scenario, total, 'C:/Users/AlexanderKa/Desktop/Github/T4-4/output/', CO2_cost)
    return total

def get_investment_data(parts, scenario):
    """Gather the input data for the investment options in the model and returns it as a dictionary"""
    investment_data={}
    
    if 'Trade_off' in scenario:
        for part in parts:
            if 'invest' in part.name:
                temp={}
                for item in part.test.items():
                    key=item[0]
                    temp[key]=item[1]
                investment_data[part.name]=temp
    else:
        investment_data[scenario] = ['No investment alternatives in this scenario']

    return investment_data

def get_input_data(parts, data):
    """Gather the input data for the existing parts in the model and returns it as a dictionary"""
    input_data={}
    for part in parts:
        if 'Existing' in part.name:
            temp={}
            for item in part.test.items():
                key=item[0]
                temp[key]=item[1]
            input_data[part.name]=temp
        
        elif part.name in data.keys():
            input_data[part.name] = data[part.name]

    return input_data

def consumption_results(m, parameters, parts, Resources):
    """ Takes a model object, extracts and returns the consumption information."""
    times = m.times_between(parameters['t_start'],parameters['t_end'])

    def _is_consumer(part,resource):
        if not isinstance(part, fs.FlowNetwork):
            return resource in part.consumption

    consumer_names = [p for p in m.descendants if _is_consumer(p,Resources.heat)]
    consumers = {p.name: 
                fs.get_series(p.consumption[Resources.heat], times) 
                for p in consumer_names}
    consumers = pd.DataFrame.from_dict(consumers)

    power_consumer_names = [p for p in m.descendants if _is_consumer(p,Resources.power)]
    power_consumers = {p.name: 
                fs.get_series(p.consumption[Resources.power], times) 
                for p in power_consumer_names}
    power_consumers = pd.DataFrame.from_dict(power_consumers)
    return consumers, power_consumers

def production_results(m, parameters, parts, Resources):
    """ Takes a model object, extracts and returns the production information."""

    def is_producer(part, resource):
        if not isinstance(part, fs.FlowNetwork):
            return resource in part.production

    times = m.times_between(parameters['t_start'],parameters['t_end'])
    heat_producers = [p for p in m.descendants
                if is_producer(p, Resources.heat)] # list comprehension

    heat = {p.name:
        fs.get_series(p.production[Resources.heat], times)
        for p in heat_producers}

    heat = pd.DataFrame.from_dict(heat)

    storage_times = m.times_between(parameters['t_start'], parameters['t_end'])
    import partlib as pl
    storage = [p for p in m.descendants if isinstance(p, pl.Accumulator)]
    stored_energy = {p.name: fs.get_series(p.volume, storage_times) for p in storage}
    stored_energy = pd.DataFrame.from_dict(stored_energy)

    
    power_producers = [p for p in m.descendants
        if is_producer(p, Resources.power)] 

    power = {p.name:
        fs.get_series(p.production[Resources.power], times)
        for p in power_producers}
    
    power_production = pd.DataFrame.from_dict(power) 
    
    return heat, stored_energy, power_production
    
def get_total_results(m, parameters, parts, Resources, scenario):
    """Gather the investment cost for the system, including which investment options to invest in"""
    investment_cost={}
    investment_cost_tot=0
    static_variables={}
    
    """Each scenario includes investments that is fixed by the scenario except for the trade off scenarios where the
    model optimize for total cost of the system."""
    for part in parts:
        if hasattr(part, 'investment_cost'):
            try:
                part_investment_cost = part.investment_cost.value
            except AttributeError:
                part_investment_cost = part.investment_cost
            investment_cost[part.name] = part_investment_cost
            investment_cost_tot += part_investment_cost
        if not 'existing' in part.name.lower():
            if hasattr(part, 'static_variables'):
                variables = set()
                for v in part.static_variables:
                    if v.value > 0:
                        static_variables[v.name]=v.value
                    #variables.add('{}: {}'.format(v.name, v.value))
                #static_variables[part.name]=variables
                
    """
    if 'Trade_off' in scenario:
        for part in parts:
            if 'static_variables' in dir(part):
                if hasattr(part, 'investment_cost'):
                    if not 'Existing' in part.name:
                        investment_cost[part.name]=part.investment_cost.value
                        investment_cost_tot += part.investment_cost.value

                    for v in part.static_variables:
                        if v.value == 0:
                            v.value = 'no investment'
                        elif v.value == 1:
                            v.value = 'yes invest max capacity'
                        else:
                            v.value = ('yes invest %s MW' %v.value)
                        if 'Renovation' in part.name:
                            if investment_cost[part.name] != 0:
                                v.value = 'invest max capacity'
                            else:
                                v.value = 'no investment'
                        static_variables[part.name]=v.value           
    else:
        static_variables[scenario] = ['No investment alternatives in this scenario']

        for part in parts:
            if hasattr(part, 'investment_cost'):
                if not 'Existing' in part.name:
                    investment_cost_tot += part.investment_cost
    """
    """Running cost for the system, in this case it only includes fuel cost"""
    
    cost = {}
    cost_tot=0

    for p in parts:
        cost[p.name] = 0
    
    
    for part, t in product(parts, m.times_between(parameters['t_start'],parameters['t_end'])):
        if part.cost(t):
            try:
                cost[part.name] +=part.cost(t).value
                cost_tot += part.cost(t).value
            except AttributeError:
                cost[part.name] += part.cost(t)
                cost_tot += part.cost(t)
    
    """The CO2 emissions from the system"""
    total_emissions=0
    CO2_emissions = dict()
    for part in parts:
        times=m.times_between(parameters['t_start'],parameters['t_end'])
        if (not isinstance(part, fs.FlowNetwork)) and (not isinstance(part, fs.Cluster)):
            if (Resources.CO2 in part.consumption):
                CO2_emissions[part.name] = fs.get_series(part.consumption[Resources.CO2], times)
                total_emissions += CO2_emissions[part.name].sum()
                
        if isinstance(part, pl.Export) and Resources.power in part.consumption:
            CO2_emissions[part.name] = -fs.get_series(part.consumption[Resources.power], times) * parameters['CO2_factor'][Resources.power]
            total_emissions += CO2_emissions[part.name].sum()

    CO2_emissions=pd.DataFrame.from_dict(CO2_emissions)
    
    total_results={'investment cost [EUR/year]':investment_cost_tot, 'running cost [EUR/year]': cost_tot, 
                    'total emissions [kg/year]':total_emissions}
    return total_results, static_variables, CO2_emissions

def waste_consumption(m, parameters, parts, Resources):
    times = m.times_between(parameters['t_start'],parameters['t_end'])

    def _is_consumer(part,resource):
        if not isinstance(part, fs.FlowNetwork):
            return resource in part.consumption

    consumer_names = [p for p in m.descendants if _is_consumer(p,Resources.waste)]
    waste_consumers = {p.name: 
                fs.get_series(p.consumption[Resources.waste], times) 
                for p in consumer_names}
    waste_consumers = pd.DataFrame.from_dict(waste_consumers)

    return waste_consumers

def resource_consumption(m, parameters, parts, Resources):

    for part in parts:
        if 'Import' in part.name:
            times=m.times_between(parameters['t_start'],parameters['t_end'])
            if 'Import(Resources.waste)' in part.name:
                waste_prod = {part.name: fs.get_series(part.production[Resources.waste], times)}
                waste_1 = sum(waste_prod.values())
                waste_import = sum(waste_1)
            if 'Import(Resources.power)' in part.name:
                power_prod = {part.name: fs.get_series(part.production[Resources.power], times)}
                power_1 = sum(power_prod.values())
                power_import = sum(power_1)
            if 'Import(Resources.natural_gas)' in part.name:
                natural_gas_prod = {part.name: fs.get_series(part.production[Resources.natural_gas], times)}
                natural_gas = sum(natural_gas_prod.values())
                natural_gas_import = sum(natural_gas)
    
    import_resources ={'waste import': waste_import, 'power import': power_import, 'natural gas import' : natural_gas_import}
    return import_resources


def waste_incinerator_modes(m, parameters, parts, Resources):
    
    for part in parts:
        if isinstance(part, pl.LinearSlowCHP):
            times = m.times_between(parameters['t_start'],parameters['t_end'])
            modes = {mode: 
                    fs.get_series(part.modes[mode], times)
                    for mode in ['on', 'off', 'starting']}
    modes = pd.DataFrame.from_dict(modes)
    
    return modes

def save_results_excel(m, parameters, year, scenario, price_scenario ,results, output_data_path, CO2_cost):
    """Write the results to on excelfile for each year and scenario"""
    import xlsxwriter
    import datetime

    try:
        writer = pd.ExcelWriter(output_data_path+'output_%s_%s_%s_%s.xlsx' %(year, scenario, price_scenario, CO2_cost), engine='xlsxwriter')

        for item in results.items():
            key=item[0]
            data=item[1]
            if type(data) == dict:
                output=pd.Series(data)
                output.to_excel(writer, sheet_name='%s'%key)
            else:
                output=pd.DataFrame(data)
                output.to_excel(writer, sheet_name='%s'%key)
        writer.save()
    except: 
        time=str(datetime.datetime.now().time())
        time=time.replace(":", ".")
        writer= pd.ExcelWriter(output_data_path+'output_%s_%s_%s.xlsx' %(year,scenario,time), engine='xlsxwriter')
        for item in results.items():
            key=item[0]
            data=item[1]
            if type(data) == dict:
                output=pd.Series(data)
                output.to_excel(writer, sheet_name='%s'%key)
            else:
                output=pd.DataFrame(data)
                output.to_excel(writer, sheet_name='%s'%key)
    writer.save()
    writer.close()

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

    order =[]
    for heat_producers in heat:
        order.append(heat_producers)
    heat=heat[order]
    heat *= pd.Timedelta('1h') / heat.index.freq
    print(heat)

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
    #wasteMode = [p for p in self.m.descendants if isinstance(p, pl.LinearSlowCHP)]
    #wasteMode = {p.name: fs.get_series(p.modes['on'], storage_times) for p in wasteMode}
    return heat

if __name__ == '__main__':
    pass
