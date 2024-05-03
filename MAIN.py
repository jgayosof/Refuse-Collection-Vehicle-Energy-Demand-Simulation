import pandas as pd
import numpy as np
import pickle
from collections import OrderedDict

from simulation import Simulation
from components.charger import Charger
from components.power_component import Power_Component
from components.battery import Battery

## Define simulation parameters
###############################################################################
# Tour data
data_route = pd.read_pickle('data/load/tour.pkl')

# Create Simulation instance
sim = Simulation(data_route)
# Call Main Simulation method
sim.simulate()
 
## Result powerflow data
###########################################################################
# Summarize route data
results_powerflows = pd.DataFrame(
                        data=OrderedDict({'route_type':sim.route.profile_day.phase_type,
                                          'route_speed':sim.route.profile_day.speed, 
                                          'route_acceleration':sim.route.profile_day.acceleration, 
                                          'route_distance':sim.route.profile_day.distance,
                                          'route_loader_active':sim.route.profile_day.loader_active,
                                          'route_container_mass':sim.route.profile_day.container_mass,
                                          'vehicle_mass_cum':sim.vehicle_mass_cum, 
                                          'vehicle_power_drive':sim.vehicle_power_drive,  
                                          'vehicle_power_loader':sim.vehicle_power_loader,
                                          'vehicle_power_motor':sim.vehicle_power_motor,
                                          'vehicle_power_electric':sim.vehicle_power_electric,
                                          'vehicle_power_diesel':sim.vehicle_power_diesel,
                                          'vehicle_eta':sim.vehicle_efficiency_drivetrain,
                                          'battery_management_power':sim.battery_management_power, 
                                          'battery_management_eta':sim.battery_management_efficiency, 
                                          'battery_power':sim.battery_power,
                                          'battery_c-rate':abs((np.array(sim.battery_power)/sim.battery.capacity_nominal_wh)),
                                          'battery_soc':sim.battery_state_of_charge,
                                          'battery_eta':sim.battery_efficiency}))

# Set Datetimeindex
datetimeindex_day = pd.date_range('01.01.2020 07:00:00', periods=len(sim.route.profile_day.speed), freq='s')
results_powerflows['date'] = datetimeindex_day
results_powerflows = results_powerflows.set_index('date')


## Results parameter data
###############################################################################
results_parameter = {}

# Route distance
results_parameter['route_distance'] = data_route['overall_distance']
# Waste mass collected
results_parameter['waste_mass'] = (max(sim.vehicle_mass_cum) - sim.vehicle.mass_empty)
# Sum of energy consumption for vehicle motor
results_parameter['energy_motor'] = abs(sum([x for x in sim.vehicle_power_motor if x > 0])) / 3600
# Sum of energy consumption for vehicle loader 
results_parameter['energy_loader'] =  abs(sum([x for x in sim.vehicle_power_loader if x > 0])) / 3600
    
if sim.vehicle.specification == 'vehicle_electric':
    ## ELECTRO        
    charger = Charger(power_grid=22000, 
                      file_path='data/components/charger_ac.json')
    charger.calculate()
            
    bms = Power_Component(timestep=1,
                          input_link=charger, 
                          file_path='data/components/battery_management.json')
    bms.calculate()
    
    battery = Battery(timestep=1, 
                      input_link=bms, 
                      file_path='data/components/battery_lfp.json')
    battery.calculate()
    
    # Sum of recuperated energy [Wh]
    results_parameter['energy_recuperation'] = (sum([x for x in sim.battery_power if x > 0]) / 3600)
    # Sum of BRUTTO energy consumption (without recuperation) [Wh]
    results_parameter['energy_consumption'] = abs(sum([x for x in sim.battery_power if x < 0]))  / 3600
    # Sum of NETTO energy consumption [Wh]
    results_parameter['energy'] = (results_parameter['energy_consumption'] - results_parameter['energy_recuperation']) \
                                    / (charger.efficiency * bms.efficiency * battery.efficiency)
    # Spesific energy per distance [Wh/m] or [kWh/km]
    results_parameter['energy_per_km'] = results_parameter['energy'] / data_route['overall_distance']
    # Specific energy per kg waste [Wh/kg] or [kWh/t]                                
    results_parameter['energy_per_kg'] = results_parameter['energy'] / (max(sim.vehicle_mass_cum) - sim.vehicle.mass_empty)
    
    
elif sim.vehicle.specification =='vehicle_diesel':
    ## Diesel
    # Sum of recuperated energy [Wh]
    results_parameter['energy_recuperation'] = 0
    # Sum of BRUTTO energy consumption (without recuperation) [Wh]
    results_parameter['energy_consumption'] = abs(sum([x for x in sim.vehicle_power_diesel if x < 0]))  / 3600
    # Sum of NETTO energy consumption [Wh]
    results_parameter['energy'] = results_parameter['energy_consumption']
    # Specific energy per distance [Wh/m] or [kWh/km]
    results_parameter['energy_per_km'] = results_parameter['energy'] / data_route['overall_distance']
    # Specific energy per kg waste [Wh/kg] or [kWh/t]                                
    results_parameter['energy_per_kg'] = (results_parameter['energy'] / (max(sim.vehicle_mass_cum) - sim.vehicle.mass_empty))

else:
    print('No vehicle type specified in json file')   
    

## Save all daytour dicts to pkl
###############################################################################
# Save results powerflow dict
file_name = 'results/EDS_power_flows_'+sim.vehicle.specification+'.pkl'
output = open(file_name, 'wb')
pickle.dump(results_powerflows, output)
output.close() 

# Save results parameter dict
file_name = 'results/EDS_parameter_'+sim.vehicle.specification+'.pkl'
output = open(file_name, 'wb')
pickle.dump(results_parameter, output)
output.close() 
