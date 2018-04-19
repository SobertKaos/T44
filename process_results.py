# -*- coding: utf-8 -*-
import pandas as pd
import friendlysam as fs

def process_results(model, parameters, Resources):
    import pdb

    m = model.m
    parts=m.descendants

    get_input_data(parts)
    process_results_2(m, parameters, parts, Resources, 'C:/Users/lovisaax/Desktop/test/' )
    total_results(m, parameters, parts, Resources)

def get_input_data(parts):
    import pdb
    
    input_data={}
    investment_data={}

    for part in parts:

        if 'Existing' in part.name:
            temp={}
            for item in part.test.items():
                key=item[0]
                temp[key]=item[1]
            input_data[part.name]=temp
  
    save_results('2050','BAU', input_data, 'C:/Users/lovisaax/Desktop/test/', 'input_data')
    
    for part in parts:

        if 'invest' in part.name:
            temp={}
            for item in part.test.items():
                key=item[0]
                temp[key]=item[1]
            investment_data[part.name]=temp

    save_results('2030','BAU', investment_data, 'C:/Users/lovisaax/Desktop/test/', 'investment_options')

def process_results_2(m, parameters, parts, Resources, output_data_path):
    """ Takes a model object, extracts and returns relevant information.
    If an output_data_path is supplied, writes the data. 
    If no data path is provided it is only returned
    """
    import pdb

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
    def _is_consumer(part,resource):
        if not isinstance(part, fs.FlowNetwork):
            return resource in part.consumption

    consumer_names = [p for p in m.descendants if _is_consumer(p,Resources.heat)]
    consumers = {p.name: 
                fs.get_series(p.consumption[Resources.heat], times) 
                for p in consumer_names}
    consumers = pd.DataFrame.from_dict(consumers)

    data = {'heat_producers': heat, 'consumers': consumers}#, 'power_producers': power,}
    if output_data_path:

       save_res('2010', 'test', data, output_data_path)

    
def total_results(m, parameters, parts, Resources):
    """Calculate the cost of the scenario"""
    import pdb

    times = m.times_between(parameters['t_start'],parameters['t_end'])

    from itertools import chain, product

    investment_cost={}
    investment_cost_tot=0
    for part in parts:
        if 'static_variables' in dir(part):
            for v in part.static_variables:
                print(part.name, 'state variable', v.value)
            if part.investment_cost:
                investment_cost[part.name]=part.investment_cost.value
                investment_cost_tot += part.investment_cost.value
    print(investment_cost)
    print('total investment cost is %s' %investment_cost_tot)

    cost={}
    cost_tot=0
    for part, t in product(parts, m.times_between(parameters['t_start'],parameters['t_end'])):
        if part.cost(t):
            cost[part.name]=part.cost(t).value
            cost_tot += part.cost(t).value
    print(cost)
    print('Total running cost is %s' %cost_tot)


    #Try to calculate the CO2 emissions from the system
    for part in parts:
        print(part)
        if 'Resources.CO2 cluster' in part.name:
            pdb.set_trace()

def save_res(year, scenario, results, output_data_path):
    import pdb
    import xlsxwriter
    
    writer = pd.ExcelWriter(output_data_path+'output_%s_%s.xlsx' %(year, scenario), engine='xlsxwriter')
    for sheet_name, data in results.items():
        data.to_excel(writer, sheet_name='%s'%sheet_name)
    writer.save()
    """
    #add test of type of data, to make it possible to only have one save function...
    writer = pd.ExcelWriter(output_data_path+'output_%s_%s.xlsx' %(year, scenario), engine='xlsxwriter')

    for sheet_name, data in results.items():
        data.to_excel(writer, sheet_name='%s'%sheet_name)
    writer.save()
    """
    
    """
    i=0
    writer = pd.ExcelWriter(output_data_path+'output_%s_%s.xlsx' %(year, scenario),  engine='xlsxwriter')
    for a in data:
        #pdb.set_trace()
        production = pd.DataFrame(a)
        pdb.set_trace()
        sheet_name = sheet_name+'add_%s' %(i)
        production.to_excel(writer, sheet_name='%s'%(sheet_name))
        i+=1
    writer.save()
    """
    """
    #pdb.set_trace()
    consumption = pd.DataFrame(consumption)
    #pdb.set_trace()
    consumption.to_excel(writer, sheet_name='consumption', na_rep = 'not relevant')
    writer.save()
    """
    
def save_results(year, scenario, data, output_data_path, sheet_name):
    '''Export data to excel'''
    import xlsxwriter
    import pdb
    
    #this writes the production_data to an excel_sheet, but does not include the values...
    try:  
        workbook=xlsxwriter.Workbook(output_data_path+'output_%s_%s.xlsx' %(year, scenario))
        worksheet = workbook.add_worksheet(sheet_name)
        #worksheet2 = workbook.add_worksheet('investment_options')
        row = 0
        col= 0
        
        for item in data.items():
            key=item[0]
            worksheet.write(row, col, key)
            properties=item[1]
            for prop in properties:
                value=properties[prop]
                worksheet.write(row, col+1, prop)
                worksheet.write(row, col+2, value)
                row += 1
        workbook.close()

    #This exception is not working correctly right now. 
    except PermissionError:
        time=str(datetime.datetime.now().time())
        time=time.replace(":", ".")
        writer= pd.ExcelWriter(output_data_path+'output_%s_%s_%s.xlsx' %(year,scenario,time), engine='xlsxwriter')
        for sheet_name, data in data.items():
            data.to_excel(writer, sheet_name='%s'%sheet_name)
        writer.save()


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
    """other = ['Boiler A',
                'Boiler B',
                'Boiler C',
                'Boiler D']
    heat['Other'] = heat[other].sum(axis=1)
    for key in other:
        del heat[key]
    """

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

def GetHeatLoad(self, p_equipment):
    import datetime
    from process_results import is_producer

    t_start = self._DEFAULT_PARAMETERS['t_start']
    t_end = self._DEFAULT_PARAMETERS['t_end']

    heat_producers = [p for p in self.m.descendants
                        if is_producer(p, pl.Resources.heat) and not
                        isinstance(p, fs.Cluster)]

    times = self.m.times_between(t_start, t_end)

    heat = {p.name: fs.get_series(p.production[pl.Resources.heat], times)
            for p in heat_producers}
    heat = pd.DataFrame.from_dict(heat)

    heatLoadWithTimestamps = heat[p_equipment].to_dict()
    heatLoad = dict()
    for elem in heatLoadWithTimestamps:
        heatLoad[elem]=heatLoadWithTimestamps[elem]
        #heatLoad[elem.to_pydatetime()] = heatLoadWithTimestamps[elem] #[str(elem.to_pydatetime())] = heatLoadWithTimestamps[elem]
    return heatLoad
    
def GetPowerLoad(self, p_equipment):
    power_producers = [p for p in self.m.descendants
                        if is_producer(p, Resources.power) and
                        not isinstance(p, fs.Cluster)]

    times = self.m.times_between(self.t_start, self.t_end)

    power = {p.name: fs.get_series(p.production[Resources.power], times)
                for p in power_producers}
    power = pd.DataFrame.from_dict(power)

    powerLoadWithTimestamps = power[p_equipment].to_dict()
    powerLoad = dict()
    for elem in powerLoadWithTimestamps:
        powerLoad[str(elem.to_pydatetime())] = powerLoadWithTimestamps[elem]

    return powerLoad

def GetNaturalGasConsumption(self, p_equipment):
    from process_results import is_consumer

    t_start = self._DEFAULT_PARAMETERS['t_start']
    t_end = self._DEFAULT_PARAMETERS['t_end']

    gas_consummers = [p for p in self.m.descendants
                        if is_consumer(p, pl.Resources.natural_gas) and
                        not isinstance(p, fs.Cluster)]

    times = self.m.times_between(t_start, t_end)

    gas = {p.name: fs.get_series(p.consumption[pl.Resources.natural_gas], times)
            for p in gas_consummers}
    gas = pd.DataFrame.from_dict(gas)

    gasLoadWithTimestamps = gas[p_equipment].to_dict()
    gasLoad = dict()
    for elem in gasLoadWithTimestamps:
        gasLoad[elem] = gasLoadWithTimestamps[elem]
        #gasLoad[str(elem.to_pydatetime())] = gasLoadWithTimestamps[elem]

    return gasLoad

def WriteLoadToCsv(self, pLoad, pPath, pFilename):
    writer = csv.DictWriter(open(pPath + '/' + pFilename, 'w'),
                            fieldnames=['Time', 'Load'])
    writer.writeheader()
    for elem in pLoad:
        writer.writerow({'Time': elem, 'Load': pLoad[elem]})

def OutputResults(self, pPath):
    #  write time series
    self.WriteLoadToCsv(self.GetHeatLoad('Boiler A'), pPath, 'BoilerA_heat.csv')
    self.WriteLoadToCsv(self.GetHeatLoad('Boiler B'), pPath, 'BoilerB_heat.csv')
    self.WriteLoadToCsv(self.GetHeatLoad('Boiler C'), pPath, 'BoilerC_heat.csv')
    self.WriteLoadToCsv(self.GetHeatLoad('Boiler D'), pPath, 'BoilerD_heat.csv')
    self.WriteLoadToCsv(self.GetHeatLoad('CHP A'), pPath, 'CHPA_heat.csv')
    self.WriteLoadToCsv(self.GetHeatLoad('CHP B'), pPath, 'CHPB_heat.csv')
    self.WriteLoadToCsv(self.GetHeatLoad('Waste Incinerator'), pPath, 'Waste_heat.csv')
    self.WriteLoadToCsv(self.GetPowerLoad('CHP A'), pPath, 'CHPA_power.csv')
    self.WriteLoadToCsv(self.GetPowerLoad('CHP B'), pPath, 'CHPB_power.csv')
    self.WriteLoadToCsv(self.GetNaturalGasConsumption('CHP A'), pPath, 'CHPA_gas.csv')
    self.WriteLoadToCsv(self.GetNaturalGasConsumption('CHP B'), pPath, 'CHPB_gas.csv')
    self.WriteLoadToCsv(self.GetNaturalGasConsumption('Boiler A'), pPath, 'BoilerA_gas.csv')
    self.WriteLoadToCsv(self.GetNaturalGasConsumption('Boiler B'), pPath, 'BoilerB_gas.csv')
    self.WriteLoadToCsv(self.GetNaturalGasConsumption('Boiler C'), pPath, 'BoilerC_gas.csv')
    self.WriteLoadToCsv(self.GetNaturalGasConsumption('Boiler D'), pPath, 'BoilerD_gas.csv')

    #  write sums for the whole simulation
    writer = open(pPath + '/KPIs.csv', 'w')
    writer.write("DeliveredGas,ExportedHeat,ExportedPower\n")
    print(self.TotalDeliveredGas())
    print(self.TotalExportedHeat())
    print(self.TotalExportedPower())
    writer.write(str(self.TotalDeliveredGas())+","+str(self.TotalExportedHeat())+","+str(self.TotalExportedPower())+"\n")
    writer.close()

def TotalDeliveredGas(self):
    res = 0
    for equipment in ['Boiler A', 'Boiler B', 'Boiler C',
                        'Boiler D', 'CHP A', 'CHP B', 'CHP invest']:
        res += sum(self.GetNaturalGasConsumption(equipment).values())
    return res

def TotalExportedHeat(self):
    res = 0
    for equipment in ['Boiler A', 'Boiler B', 'Boiler C',
                        'Boiler D', 'CHP A', 'CHP B', 'Waste Incinerator', 'CHP invest']:
        res += sum(self.GetHeatLoad(equipment).values())
    return res

def TotalExportedPower(self):
    res = 0
    for equipment in ['CHP A', 'CHP B', 'Waste Incinerator']:
        res += sum(self.GetPowerLoad(equipment).values())
    return res


if __name__ == '__main__':
    pass
