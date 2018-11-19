cases = {
    '2030': {
        'BAU': {
            'PV': {'capacity [MW] lb': 23, 'capacity [MW] ub': 23, 'specific investment cost': 6050000/23},
            'Accumulator': {'capacity [MWh] lb': 0, 'capacity [MWh] ub': 0,'max flow [MWh perh]': 0,'specific investment cost': 0},
            'DH grid expansion': {'capacity [MWh per y]': '155000 MWh DH exp','specific investment cost': 234.7},
            'NG CHP': {'capacity [MW] lb': 35, 'capacity [MW] ub': 35,'specific investment cost': 1200000},
            'Bio CHP': {'capacity [MW] lb': 0, 'capacity [MW] ub': 0,'specific investment cost': 0},                   
            },
        'Max_RES': {
            'PV': {'capacity [MW] lb': 30, 'capacity [MW] ub': 30, 'specific investment cost': 12100000/30},
            'Accumulator': {'capacity [MWh] lb': 0, 'capacity [MWh] ub': 0,'max flow [MWh perh]': 0,'specific investment cost': 0},
            'DH grid expansion': {'capacity [MWh per y]': '155000 MWh DH exp','specific investment cost': 234.7},
            'NG CHP': {'capacity [MW] lb': 35, 'capacity [MW] ub': 35,'specific investment cost': 1200000},
            'Bio CHP': {'capacity [MW] lb': 0, 'capacity [MW] ub': 0,'specific investment cost': 0}
            },
        'Max_DH': {
            'PV': {'capacity [MW] lb': 23, 'capacity [MW] ub': 23, 'specific investment cost': 6050000/23},
            'Accumulator': {'capacity [MWh] lb': 0, 'capacity [MWh] ub': 0,'max flow [MWh perh]': 0,'specific investment cost': 0},
            'DH grid expansion': {'capacity [MWh per y]': '183000 MWh DH exp','specific investment cost': 234.7},
            'NG CHP': {'capacity [MW] lb': 35, 'capacity [MW] ub': 35,'specific investment cost': 1200000},
            'Bio CHP': {'capacity [MW] lb': 0, 'capacity [MW] ub': 0,'specific investment cost': 0}                    
            },
        'Max_Retrofit':{
            'PV': {'capacity [MW] lb': 23, 'capacity [MW] ub': 23, 'specific investment cost': 6050000/23},
            'Accumulator': {'capacity [MWh] lb': 0, 'capacity [MWh] ub': 0,'max flow [MWh perh]': 0,'specific investment cost': 0},
            'DH grid expansion': {'capacity [MWh per y]': '183000 MWh DH exp','specific investment cost': 234.7},
            'NG CHP': {'capacity [MW] lb': 35, 'capacity [MW] ub': 35,'specific investment cost': 1200000},
            'Bio CHP': {'capacity [MW] lb': 0, 'capacity [MW] ub': 0,'specific investment cost': 0}                    
            },
        'Trade_off': {
            'PV': {'capacity [MW] lb': 0, 'capacity [MW] ub': 30, 'specific investment cost': 6050000/23},
            'Accumulator': {'capacity [MWh] lb': 0, 'capacity [MWh] ub': 0,'max flow [MWh perh]': 0,'specific investment cost': 0},
            'DH grid expansion': {'capacity [MWh per y]': 'ANY','specific investment cost': 234.7},
            'NG CHP': {'capacity [MW] lb': 0, 'capacity [MW] ub': 35,'specific investment cost': 1200000},
            'Bio CHP': {'capacity [MW] lb': 0, 'capacity [MW] ub': 0,'specific investment cost': 0}                    
            }
        },
    '2050': {
        'BAU': {
            'PV': {'capacity [MW] lb': 33, 'capacity [MW] ub': 33, 'specific investment cost': 12000000/33},
            'Accumulator': {'capacity [MWh] lb': 0, 'capacity [MWh] ub': 0,'max flow [MWh perh]': 0,'specific investment cost': 0},
            'DH grid expansion': {'capacity [MWh per y]': '213000 MWh DH exp','specific investment cost': 234.7},
            'NG CHP': {'capacity [MW] lb': 35, 'capacity [MW] ub': 35,'specific investment cost': 1200000},
            'Bio CHP': {'capacity [MW] lb': 0, 'capacity [MW] ub': 0,'specific investment cost': 0}                    
            },
        'Max_RES': {
            'PV': {'capacity [MW] lb': 60, 'capacity [MW] ub': 60, 'specific investment cost': 29960000/60},
            'Accumulator': {'capacity [MWh] lb': 0, 'capacity [MWh] ub': 0,'max flow [MWh perh]': 0,'specific investment cost': 0},
            'DH grid expansion': {'capacity [MWh per y]': '213000 MWh DH exp','specific investment cost': 234.7},
            'NG CHP': {'capacity [MW] lb': 35, 'capacity [MW] ub': 35,'specific investment cost': 1200000},
            'Bio CHP': {'capacity [MW] lb': 0, 'capacity [MW] ub': 0,'specific investment cost': 0}                    
            },
        'Max_DH': {
            'PV': {'capacity [MW] lb': 33, 'capacity [MW] ub': 33, 'specific investment cost': 12000000/33},
            'Accumulator': {'capacity [MWh] lb': 80, 'capacity [MWh] ub': 80,'max flow [MWh perh]': 20,'specific investment cost': 415000},
            'DH grid expansion': {'capacity [MWh per y]': '223000 MWh DH exp','specific investment cost': 234.7},
            'NG CHP': {'capacity [MW] lb': 0, 'capacity [MW] ub': 0,'specific investment cost': 1200000},
            'Bio CHP': {'capacity [MW] lb': 55, 'capacity [MW] ub': 55,'specific investment cost': 72600000/55}                    
            },
        'Max_Retrofit':{
            'PV': {'capacity [MW] lb': 33, 'capacity [MW] ub': 33, 'specific investment cost': 12000000/33},
            'Accumulator': {'capacity [MWh] lb': 0, 'capacity [MWh] ub': 0,'max flow [MWh perh]': 0,'specific investment cost': 0},
            'DH grid expansion': {'capacity [MWh per y]': '213000 MWh DH exp','specific investment cost': 234.7},
            'NG CHP': {'capacity [MW] lb': 35, 'capacity [MW] ub': 35,'specific investment cost': 1200000},
            'Bio CHP': {'capacity [MW] lb': 0, 'capacity [MW] ub': 0,'specific investment cost': 0}                    
            },
        'Trade_off': {
            'PV': {'capacity [MW] lb': 0, 'capacity [MW] ub': 60, 'specific investment cost': 12000000/33},
            'Accumulator': {'capacity [MWh] lb': 0, 'capacity [MWh] ub': 80,'max flow [MWh perh]': 20,'specific investment cost': 415000},
            'DH grid expansion': {'capacity [MWh per y]': 'ANY','specific investment cost': 234.7},
            'NG CHP': {'capacity [MW] lb': 0, 'capacity [MW] ub': 35,'specific investment cost': 1200000},
            'Bio CHP': {'capacity [MW] lb': 0, 'capacity [MW] ub': 55,'specific investment cost': 72600000/55}                    
            },
        }

    }

