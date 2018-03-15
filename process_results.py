# -*- coding: utf-8 -*-



""" is_producer, is_consumer, and get_produced_heat_df are old functions, restructure or possibly throw away"""
def is_producer(part, resource):
    if hasattr(part, 'production'):
        return resource in part.production


def is_consumer(part, resource):
    if hasattr(part, 'consumption'):
        return resource in part.consumption


def get_produced_heat_df():
    load_A = pd.read_csv('BoilerA_heat.csv', encoding='utf-8',
                         parse_dates=True, index_col='Time',
                         names=['Time', 'BoilerA'], skiprows=1)

    load_B = pd.read_csv('BoilerB_heat.csv', encoding='utf-8',
                         parse_dates=True, index_col='Time',
                         names=['Time', 'BoilerB'], skiprows=1)

    load_C = pd.read_csv('BoilerC_heat.csv', encoding='utf-8',
                         parse_dates=True, index_col='Time',
                         names=['Time', 'BoilerC'], skiprows=1)

    load_D = pd.read_csv('BoilerD_heat.csv', encoding='utf-8',
                         parse_dates=True, index_col='Time',
                         names=['Time', 'BoilerD'], skiprows=1)

    load_CHPA = pd.read_csv('CHPA_heat.csv', encoding='utf-8',
                            parse_dates=True, index_col='Time',
                            names=['Time', 'CHPA'], skiprows=1)

    load_CHPB = pd.read_csv('CHPB_heat.csv', encoding='utf-8',
                            parse_dates=True, index_col='Time',
                            names=['Time', 'CHPB'], skiprows=1)

    load_Waste = pd.read_csv('Waste_heat.csv', encoding='utf-8',
                             parse_dates=True, index_col='Time',
                             names=['Time', 'Waste'], skiprows=1)

    load_df = pd.concat([load_A, load_B, load_C, load_D,
                         load_CHPA, load_CHPB, load_Waste],
                        axis=1, join='inner')
    return load_df


def save_results(year, scenario, results, output_data_path):
    '''Export data to excel'''
     
    try:   
        writer = pd.ExcelWriter(output_data_path+'output_%s_%s.xlsx' %(year,scenario), engine='xlsxwriter')
        for sheet_name, data in results.items():
            data.to_excel(writer, sheet_name='%s'%sheet_name)
        writer.save()

    except PermissionError:
        time=str(datetime.datetime.now().time())
        time=time.replace(":", ".")
        writer= pd.ExcelWriter(output_data_path+'output_%s_%s_%s.xlsx' %(year,scenario,time), engine='xlsxwriter')
        for sheet_name, data in results.items():
            data.to_excel(writer, sheet_name='%s'%sheet_name)
        writer.save()

    return None


def process_results(model, parameters, output_data_path= None):
    """ Takes a model object, extracts and returns relevant information.
    If an output_data_path is supplied, writes the data. 
    If no data path is provided it is only returned
    """

    m=model
    
    def is_producer(part, resource):
        if not isinstance(part, fs.FlowNetwork):
            return resource in part.production

    times = m.times_between(parameters['t0'],parameters['t_end'])

    heat_producers = [p for p in m.descendants
            if is_producer(p, pl.Resources.heat)] # list comprehension


    def is_producer(part, resource):
        if not isinstance(part, fs.FlowNetwork):
            return resource in part.production


    power_producers = [p for p in m.descendants
        if is_producer(p, pl.Resources.power)] 

    power = {p.name:
        fs.get_series(p.production[pl.Resources.power], times)
        for p in power_producers}
    power = pd.DataFrame.from_dict(power)


    heat = {p.name:
        fs.get_series(p.production[pl.Resources.heat], times)
        for p in heat_producers}

    heat = pd.DataFrame.from_dict(heat)
    order= ['Rya', 'heatpump', 'woodBoiler', 'CHP_second', 'CHP']
    heat=heat[order]

    def _is_consumer(part,resource):
        if not isinstance(part, fs.FlowNetwork):
            return resource in part.consumption

    consumer_names = [p for p in m.descendants if _is_consumer(p, pl.Resources.heat)]
    consumers = {p.name: fs.get_series(p.consumption[pl.Resources.heat], times) for p in consumer_names}
    consumers = pd.DataFrame.from_dict(consumers)
    

    data = {'heat_producers': heat, 'power_producers': power, 'consumers': consumers}

    if output_data_path:
        save_results(year, scenario, data, output_data_path)
    
    return data

if __name__ == '__main__':
    pass
