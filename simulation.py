from datetime import datetime

from components.simulatable import Simulatable

from components.route import Route
from components.vehicle import Vehicle
from components.power_component import Power_Component
from components.battery import Battery


class Simulation(Simulatable):
    '''
    Central Simulation class, where vehicle energy system is constructed
    Extractable system power flows are defined here

    Attributes
    ----------
    Simulatable : class. In order to simulate system

    Methods
    -------
    simulate
    '''

    def __init__(self, data_route):
        '''
        Parameters
        ----------
        data_route: dict - route profile parameter:
            container_mass: float [kg].     Mass of container
            containers_sum: int [1].        Number of containers of collection route
            stops_sum: int [1].             Number of stops of route
            distance_there: float [m].      Route phase distance of transfer drive to collection from recycling hub
            distance_back: float [m].       Route phase distance of transfer drive from collection to recycling hub
            distance_collection: float [m]. Route phase distance of collection phase
            overall_distance: float [m].    Overall route distance
        '''

        ## Define simulation parameters
        # [s] Simulation timestep
        self.timestep = 1

        ## Create route profile
        self.route = Route(timestep=self.timestep,
                           data_route=data_route,
                           file_path='data/components/route_profile.json' )
        self.route.get_profile()

        ## Initialize system component classes
        # Vehicle
        self.vehicle = Vehicle(timestep=self.timestep,
                               input_link=self.route.profile_day,
                               file_path='data/components/vehicle_electric.json')

        # Battery Management System
        self.battery_management = Power_Component(timestep=self.timestep,
                                                  input_link=self.vehicle,
                                                  file_path='data/components/battery_management.json')
        # Battery
        self.battery = Battery(timestep=self.timestep,
                               input_link=self.battery_management,
                               file_path='data/components/battery_lfp.json')

        ## Initialize Simulatable class and define needs_update initially to True
        Simulatable.__init__(self, self.vehicle, self.battery_management, self.battery)

        self.needs_update = True


    def simulate(self):
        '''
        Central simulation method, which :
            initializes all list containers to store simulation results
            iterates over all simulation timesteps and calls Simulatable.start/update/end()

        Parameters
        ----------
        None
        '''
        ## Initialization of list containers to store simulation results

        # Timeindex
        self.timeindex = list()

        # Vehicle
        self.vehicle_mass_cum = list()
        self.vehicle_power_drive = list()
        self.vehicle_power_loader = list()
        self.vehicle_power_motor = list()
        self.vehicle_power_electric = list()
        self.vehicle_power_diesel = list()
        self.vehicle_efficiency_drivetrain = list()
        # BMS
        self.battery_management_power = list()
        self.battery_management_efficiency = list()
        # Battery
        self.battery_power = list()
        self.battery_efficiency = list()
        self.battery_power_loss = list()
        self.battery_state_of_charge = list()
        self.battery_temperature = list()

        # As long as needs_update = True simulation takes place
        if self.needs_update:
            print(datetime.today().strftime('%Y-%m-%d %H:%M:%S'), ' Start')

            ## Call start method (inheret from Simulatable) to start simulation
            self.start()

            ## Iteration over all simulation steps
            for t in range(0, len(self.route.profile_day)):#self.simulation_period_hours):
                ## Call update method to call calculation method and go one simulation step further
                self.update()

                # Vehicle
                self.vehicle_mass_cum.append(self.vehicle.mass_cum)
                self.vehicle_power_drive.append(self.vehicle.power_drive)
                self.vehicle_power_loader.append(self.vehicle.power_loader_motor)
                self.vehicle_power_motor.append(self.vehicle.power_motor)
                self.vehicle_power_electric.append(self.vehicle.power_electric)
                self.vehicle_power_diesel.append(self.vehicle.power_diesel)
                self.vehicle_efficiency_drivetrain.append(self.vehicle.eta_drivetrain)
                # BMS
                self.battery_management_power.append(self.battery_management.power)
                self.battery_management_efficiency.append(self.battery_management.efficiency)
                # Battery
                self.battery_power.append(self.battery.power_battery)
                self.battery_efficiency.append(self.battery.efficiency)
                self.battery_power_loss.append(self.battery.power_loss)
                self.battery_state_of_charge.append(self.battery.state_of_charge)
                self.battery_temperature.append(self.battery.temperature)

            ## Simulation over: set needs_update to false and call end method
            self.needs_update = False
            print(datetime.today().strftime('%Y-%m-%d %H:%M:%S'), ' End')
            self.end()