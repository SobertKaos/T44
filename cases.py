cases = {
    '2030': {
        'BAU': {
            'PV': {'capacity [MW] lb': 23, 'capacity [MW] ub': 23, 'specific investment cost': 6050000/23},
            'Accumulator': {'capacity [MWh] lb': 0, 'capacity [MWh] ub': 0,'max flow [MWh perh]': 0,'specific investment cost': 0},
            'DH grid expansion': {'capacity [MWh per y] lb': 155, 'capacity [MWh per y] ub': 155, 'specific investment cost [EUR per GWh]': 234742},
            'NG CHP': {'capacity [MW] lb': 35, 'capacity [MW] ub': 35,'specific investment cost': 1200000},
            'Bio CHP': {'capacity [MW] lb': 0, 'capacity [MW] ub': 0,'specific investment cost': 0},
            '1 per cent deep': {'capacity lb': 1, 'capacity ub': 1, 'specific investment cost': 78856545},
            '1.5 per cent deep': {'capacity lb': 0, 'capacity ub': 0, 'specific investment cost': 114573740},
            '1 per cent shallow': {'capacity lb': 0, 'capacity ub': 0, 'specific investment cost': 45884967},
            '1.5 per cent shallow': {'capacity lb': 0, 'capacity ub': 0, 'specific investment cost': 66668052}            
            },
        'Max_RES': {
            'PV': {'capacity [MW] lb': 30, 'capacity [MW] ub': 30, 'specific investment cost': 12100000/30},
            'Accumulator': {'capacity [MWh] lb': 0, 'capacity [MWh] ub': 0,'max flow [MWh perh]': 0,'specific investment cost': 0},
            'DH grid expansion': {'capacity [MWh per y] lb': 155, 'capacity [MWh per y] ub': 155, 'specific investment cost [EUR per GWh]': 234742},
            'NG CHP': {'capacity [MW] lb': 35, 'capacity [MW] ub': 35,'specific investment cost': 1200000},
            'Bio CHP': {'capacity [MW] lb': 0, 'capacity [MW] ub': 0,'specific investment cost': 0},
            '1 per cent deep': {'capacity lb': 1, 'capacity ub': 1, 'specific investment cost': 78856545},
            '1.5 per cent deep': {'capacity lb': 0, 'capacity ub': 0, 'specific investment cost': 114573740},
            '1 per cent shallow': {'capacity lb': 0, 'capacity ub': 0, 'specific investment cost': 45884967},
            '1.5 per cent shallow': {'capacity lb': 0, 'capacity ub': 0, 'specific investment cost': 66668052}   
            },
        'Max_DH': {
            'PV': {'capacity [MW] lb': 23, 'capacity [MW] ub': 23, 'specific investment cost': 6050000/23},
            'Accumulator': {'capacity [MWh] lb': 0, 'capacity [MWh] ub': 0,'max flow [MWh perh]': 0,'specific investment cost': 0},
            'DH grid expansion': {'capacity [MWh per y] lb': 183, 'capacity [MWh per y] ub': 183,'specific investment cost [EUR per GWh]': 234742},
            'NG CHP': {'capacity [MW] lb': 35, 'capacity [MW] ub': 35,'specific investment cost': 1200000},
            'Bio CHP': {'capacity [MW] lb': 0, 'capacity [MW] ub': 0,'specific investment cost': 0},
            '1 per cent deep': {'capacity lb': 1, 'capacity ub': 1, 'specific investment cost': 78856545},
            '1.5 per cent deep': {'capacity lb': 0, 'capacity ub': 0, 'specific investment cost': 114573740},
            '1 per cent shallow': {'capacity lb': 0, 'capacity ub': 0, 'specific investment cost': 45884967},
            '1.5 per cent shallow': {'capacity lb': 0, 'capacity ub': 0, 'specific investment cost': 66668052}                       
            },
        'Max_Retrofit':{
            'PV': {'capacity [MW] lb': 23, 'capacity [MW] ub': 23, 'specific investment cost': 6050000/23},
            'Accumulator': {'capacity [MWh] lb': 0, 'capacity [MWh] ub': 0,'max flow [MWh perh]': 0,'specific investment cost': 0},
            'DH grid expansion': {'capacity [MWh per y] lb': 183, 'capacity [MWh per y] ub': 183, 'specific investment cost [EUR per GWh]': 234742},
            'NG CHP': {'capacity [MW] lb': 35, 'capacity [MW] ub': 35,'specific investment cost': 1200000},
            'Bio CHP': {'capacity [MW] lb': 0, 'capacity [MW] ub': 0,'specific investment cost': 0},
            '1 per cent deep': {'capacity lb': 0, 'capacity ub': 0, 'specific investment cost': 78856545},
            '1.5 per cent deep': {'capacity lb': 1, 'capacity ub': 1, 'specific investment cost': 114573740},
            '1 per cent shallow': {'capacity lb': 0, 'capacity ub': 0, 'specific investment cost': 45884967},
            '1.5 per cent shallow': {'capacity lb': 0, 'capacity ub': 0, 'specific investment cost': 66668052}                       
            },
        'Trade_off': {
            'PV': {'capacity [MW] lb': 0, 'capacity [MW] ub': 30, 'specific investment cost': 6050000/23},
            'Accumulator': {'capacity [MWh] lb': 0, 'capacity [MWh] ub': 0,'max flow [MWh perh]': 0,'specific investment cost': 0},
            'DH grid expansion':{'capacity [MWh per y] lb': 0, 'capacity [MWh per y] ub': 183 ,'specific investment cost [EUR per GWh]': 234742},
            'NG CHP': {'capacity [MW] lb': 0, 'capacity [MW] ub': 35,'specific investment cost': 1200000},
            'Bio CHP': {'capacity [MW] lb': 0, 'capacity [MW] ub': 0,'specific investment cost': 0},
            '1 per cent deep': {'capacity lb': 0, 'capacity ub': 1, 'specific investment cost': 78856545},
            '1.5 per cent deep': {'capacity lb': 0, 'capacity ub': 1, 'specific investment cost': 114573740},
            '1 per cent shallow': {'capacity lb': 0, 'capacity ub': 1, 'specific investment cost': 45884967},
            '1.5 per cent shallow': {'capacity lb': 0, 'capacity ub': 1, 'specific investment cost': 66668052}                       
            }
        },
    '2050': {
        'BAU': {
            'PV': {'capacity [MW] lb': 33, 'capacity [MW] ub': 33, 'specific investment cost': 12000000/33},
            'Accumulator': {'capacity [MWh] lb': 0, 'capacity [MWh] ub': 0,'max flow [MWh perh]': 0,'specific investment cost': 0},
            'DH grid expansion': {'capacity [MWh per y] lb': 213, 'capacity [MWh per y] ub': 213, 'specific investment cost [EUR per GWh]': 234742},
            'NG CHP': {'capacity [MW] lb': 35, 'capacity [MW] ub': 35,'specific investment cost': 1200000},
            'Bio CHP': {'capacity [MW] lb': 0, 'capacity [MW] ub': 0,'specific investment cost': 0},
            '1 per cent deep': {'capacity lb': 1, 'capacity ub': 1, 'specific investment cost': 173897482},
            '1.5 per cent deep': {'capacity lb': 0, 'capacity ub': 0, 'specific investment cost': 241410529},
            '1 per cent shallow': {'capacity lb': 0, 'capacity ub': 0, 'specific investment cost': 101187291},
            '1.5 per cent shallow': {'capacity lb': 0, 'capacity ub': 0, 'specific investment cost': 140471715}                    
            },
        'Max_RES': {
            'PV': {'capacity [MW] lb': 60, 'capacity [MW] ub': 60, 'specific investment cost': 29960000/60},
            'Accumulator': {'capacity [MWh] lb': 0, 'capacity [MWh] ub': 0,'max flow [MWh perh]': 0,'specific investment cost': 0},
            'DH grid expansion': {'capacity [MWh per y] lb': 213, 'capacity [MWh per y] ub': 213, 'specific investment cost [EUR per GWh]': 234742},
            'NG CHP': {'capacity [MW] lb': 35, 'capacity [MW] ub': 35,'specific investment cost': 1200000},
            'Bio CHP': {'capacity [MW] lb': 0, 'capacity [MW] ub': 0,'specific investment cost': 0},
            '1 per cent deep': {'capacity lb': 1, 'capacity ub': 1, 'specific investment cost': 173897482},
            '1.5 per cent deep': {'capacity lb': 0, 'capacity ub': 0, 'specific investment cost': 241410529},
            '1 per cent shallow': {'capacity lb': 0, 'capacity ub': 0, 'specific investment cost': 101187291},
            '1.5 per cent shallow': {'capacity lb': 0, 'capacity ub': 0, 'specific investment cost': 140471715}                    
            },
        'Max_DH': {
            'PV': {'capacity [MW] lb': 33, 'capacity [MW] ub': 33, 'specific investment cost': 12000000/33},
            'Accumulator': {'capacity [MWh] lb': 80, 'capacity [MWh] ub': 80,'max flow [MWh perh]': 20,'specific investment cost': 415000},
            'DH grid expansion': {'capacity [MWh per y] lb': 223, 'capacity [MWh per y] ub': 223, 'specific investment cost [EUR per GWh]': 234742},
            'NG CHP': {'capacity [MW] lb': 0, 'capacity [MW] ub': 0,'specific investment cost': 1200000},
            'Bio CHP': {'capacity [MW] lb': 55, 'capacity [MW] ub': 55,'specific investment cost': 72600000/55},
            '1 per cent deep': {'capacity lb': 1, 'capacity ub': 1, 'specific investment cost': 173897482},
            '1.5 per cent deep': {'capacity lb': 0, 'capacity ub': 0, 'specific investment cost': 241410529},
            '1 per cent shallow': {'capacity lb': 0, 'capacity ub': 0, 'specific investment cost': 101187291},
            '1.5 per cent shallow': {'capacity lb': 0, 'capacity ub': 0, 'specific investment cost': 140471715}                    
            },
        'Max_Retrofit':{
            'PV': {'capacity [MW] lb': 33, 'capacity [MW] ub': 33, 'specific investment cost': 12000000/33},
            'Accumulator': {'capacity [MWh] lb': 0, 'capacity [MWh] ub': 0,'max flow [MWh perh]': 0,'specific investment cost': 0},
            'DH grid expansion': {'capacity [MWh per y] lb': 213, 'capacity [MWh per y] ub': 213, 'specific investment cost [EUR per GWh]': 234742},
            'NG CHP': {'capacity [MW] lb': 35, 'capacity [MW] ub': 35,'specific investment cost': 1200000},
            'Bio CHP': {'capacity [MW] lb': 0, 'capacity [MW] ub': 0,'specific investment cost': 0},
            '1 per cent deep': {'capacity lb': 0, 'capacity ub': 0, 'specific investment cost': 173897482},
            '1.5 per cent deep': {'capacity lb': 1, 'capacity ub': 1, 'specific investment cost': 241410529},
            '1 per cent shallow': {'capacity lb': 0, 'capacity ub': 0, 'specific investment cost': 101187291},
            '1.5 per cent shallow': {'capacity lb': 0, 'capacity ub': 0, 'specific investment cost': 140471715}                    
            },
        'Trade_off': {
            'PV': {'capacity [MW] lb': 0, 'capacity [MW] ub': 60, 'specific investment cost': 12000000/33},
            'Accumulator': {'capacity [MWh] lb': 0, 'capacity [MWh] ub': 80,'max flow [MWh perh]': 20,'specific investment cost': 415000},
            'DH grid expansion': {'capacity [MWh per y] lb': 0, 'capacity [MWh per y] ub': 223,'specific investment cost [EUR per GWh]': 234742},
            'NG CHP': {'capacity [MW] lb': 0, 'capacity [MW] ub': 35,'specific investment cost': 1200000},
            'Bio CHP': {'capacity [MW] lb': 0, 'capacity [MW] ub': 55,'specific investment cost': 72600000/55},
            '1 per cent deep': {'capacity lb': 0, 'capacity ub': 1, 'specific investment cost': 173897482},
            '1.5 per cent deep': {'capacity lb': 0, 'capacity ub': 1, 'specific investment cost': 241410529},
            '1 per cent shallow': {'capacity lb': 0, 'capacity ub': 1, 'specific investment cost': 101187291},
            '1.5 per cent shallow': {'capacity lb': 0, 'capacity ub': 1, 'specific investment cost': 140471715}                   
            },
        }

    }

