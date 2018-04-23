# -*- coding: utf-8 -*-
import pandas as pd
import friendlysam as fs
import pdb

def process_results(model, parameters, Resources):

    m = model.m
    parts=m.descendants

    input_data = get_input_data(parts)
    investment_data=get_investment_data(parts)
    production = production_results(m, parameters, parts, Resources)
    consumption = consumption_results(m, parameters, parts, Resources )
    [total_results, static_variables] = get_total_results(m, parameters, parts, Resources)

    total= {'input for existing units':input_data, 'input investment_data':investment_data, 'production':production, 
    'consumption':consumption, 'total cost and emissions':total_results, 'invest or not': static_variables}
    save_results_excel(m, parameters, 'year', 'scenario', total, 'C:/Users/lovisaax/Desktop/test/')

def get_investment_data(parts):
    """Gather the input data for the investment options in the model and returns it as a dictionary"""
    investment_data={}

    for part in parts:

        if 'invest' in part.name:
            temp={}
            for item in part.test.items():
                key=item[0]
                temp[key]=item[1]
                
            investment_data[part.name]=temp

    return investment_data

def get_input_data(parts):
    """Gather the input data for the existing parts in the model and returns it as a dictionary"""
    input_data={}

    for part in parts:

        if 'Existing' in part.name:
            temp={}
            for item in part.test.items():
                key=item[0]
                temp[key]=item[1]
            input_data[part.name]=temp
    
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
    return consumers

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
    """
    power_producers = [p for p in m.descendants
        if is_producer(p, Resources.power)] 

    power = {p.name:
        fs.get_series(p.production[Resources.power], times)
        for p in power_producers}

    power = pd.DataFrame.from_dict(power) 

    """
    return heat
    
def get_total_results(m, parameters, parts, Resources):
    """Gather the investment cost for the system, including which investment options to invest in"""
    investment_cost={}
    investment_cost_tot=0
    static_variables={}
    for part in parts:
        if 'static_variables' in dir(part):
            if part.investment_cost:
                investment_cost[part.name]=part.investment_cost.value
                investment_cost_tot += part.investment_cost.value
                
            for v in part.static_variables:
                if v.value == 0:
                    v.value = 'no investment'
                elif v.value == 1:
                    v.value = 'yes invest max capacity'
                else:
                    v.value = ('yes invest %s MW' %v.value)
                static_variables[part.name]=v.value
    #print('total investment cost is %s' %investment_cost_tot)

    """TRnning cost for the system, in this case it only includes fuel cost"""
    from itertools import chain, product
    cost={}
    cost_tot=0
    for part, t in product(parts, m.times_between(parameters['t_start'],parameters['t_end'])):
        if part.cost(t):
            cost[part.name]=part.cost(t).value
            cost_tot += part.cost(t).value
    #print('Total running cost is %s' %cost_tot)

    """The CO2 emissions from the system"""
    for part in parts:
        if (not isinstance(part, fs.FlowNetwork)) and (not isinstance(part, fs.Cluster)):
            if (Resources.CO2 in part.consumption):
                times=m.times_between(parameters['t_start'],parameters['t_end'])
                CO2_emissions = {part.name:
                    fs.get_series(part.consumption[Resources.CO2], times)}
                i=0
                total_emissions=0
                for CO2 in CO2_emissions.values():
                    for i in range(len(CO2)):
                        value = CO2[i]
                        total_emissions += value
                        i +=1
                #print('total emissions is %s' %total_emissions)
    total_results={'investment cost [EUR]':investment_cost_tot, 'running cost [EUR]': cost_tot, 'total emissions':total_emissions}
    return total_results, static_variables

def save_results_excel(m, parameters, year, scenario, results, output_data_path):
    """Write the results to on excelfile for each year and scenario"""
    import xlsxwriter
    import datetime

    try:
        writer = pd.ExcelWriter(output_data_path+'output_%s_%s.xlsx' %(year, scenario), engine='xlsxwriter')

        for item in results.items():
            key=item[0]
            data=item[1]
            if type(data) == dict:
                test=pd.Series(data)
                #test=pd.DataFrame.from_dict([data])
                test.to_excel(writer, sheet_name='%s'%key)
            else:
                test=pd.DataFrame(data)
                test.to_excel(writer, sheet_name='%s'%key)
        
    except: 
        time=str(datetime.datetime.now().time())
        time=time.replace(":", ".")
        writer= pd.ExcelWriter(output_data_path+'output_%s_%s_%s.xlsx' %(year,scenario,time), engine='xlsxwriter')
        for item in results.items():
            key=item[0]
            data=item[1]
            if type(data) == dict:
                test=pd.DataFrame.from_dict([data])
                test.to_excel(writer, sheet_name='%s'%key)
            else:
                test=pd.DataFrame(data)
                test.to_excel(writer, sheet_name='%s'%key)
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
