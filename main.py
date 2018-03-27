# -*- coding: utf-8 -*-

import pdb
import read_data
import city
import run_model
import process_results


if __name__ == "__main__":
    import pdb
    with open("data_path.txt", mode='r') as f:
        data_path = f.read()

    print('Running CityModel')
    model = city.CityModel()
    model.RunModel()
    print('Model has finished run, processing results')
    data = process_results.process_results(model.m, output_data_path= None)
    process_results.display_results(data)
    pdb.set_trace()