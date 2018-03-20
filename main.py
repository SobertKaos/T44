# -*- coding: utf-8 -*-

import pdb
import read_data
import city
import run_model
import process_results


if __name__ == "__main__":
    with open("data_path.txt", mode='r') as f:
        data_path = f.read()
        pdb.set_trace()

      
model = city.CityModel()
print("heat_history : " + data_path + "/heat_history.csv")
print("power_price : " + data_path + "/power_price.csv")
print("power_demand : " + data_path + "/power_demand.csv")
city.set_heat_history(data_path + "/heat_history.csv") ## OLD
city.set_power_price(data_path + "/power_price.csv")
city.set_power_demand(data_path + "/power_demand.csv")
city.set_fixed_price(data_path + "/fixed_prices.csv")

run_model.RunModel(model)
process_results.process_results(model)
print("FriendlySam run finished")