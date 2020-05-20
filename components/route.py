import pandas as pd
import numpy as np
from numpy.matlib import repmat
import math

from components.serializable import Serializable
import data_loader

class Route(Serializable):
    '''
    Route class, to construct Timeseries route DAY load
    Including: speed, acceleration, distance, laoder_active, container_mass, charge_power, route_type

    Attributes
    ----------
    Serializable : class

    Methods
    -------
    get_profile
    drivephase
    workphase
    '''

    def __init__(self, timestep, data_route, file_path = None):
        '''
        Parameters:
            timestep: int [s]. simulation timestep
            data_route: dict. route data paraneters
            file_path: json file. Battery parameter load file
        '''
        # Read component parameters from json file
        if file_path:
            self.load(file_path)

        else:
            print('Attention: No json file for route model specified')

        # Define durations as integer
        self.t_wait = int(self.t_wait)

        # [s] Simulation timestep
        # ATTENTION: ROUTE class works only with a timstep of 1s
        self.timestep = timestep

        # Day route data
        self.data_route = data_route

        # Drivecycle data
        self.drivecycle = data_loader.DriveCycle()
        self.drivecycle.read_csv(self.drivecycle_file)


    def get_profile(self):
        '''
        Method creates profile out of different phases:
            drivephase_there - 07:00 to XX:XX
            workphase - XX:XX to XX:XX
            drivephase_back - XX:XX to XX:XX

        Parameters
        ----------
        None
        '''
        # Call phase methods to create phase profiles
        self.df_drivephase_there = self.drivephase(self.data_route['distance_there'])
        self.df_workphase = self.workphase()
        self.df_drivephase_back = self.drivephase(self.data_route['distance_back'])

        df_main = pd.concat([self.df_drivephase_there,
                             self.df_workphase,
                             self.df_drivephase_back],
                            ignore_index=True)

        self.profile_day = df_main


    def workphase(self):
        '''
        Method creates workphase load profile

        Parameters
        ----------
        None
        '''
        ## Parameters
        # Distance between two stops [m]
        self.collection_distance_per_stop = self.data_route['distance_collection'] / (self.data_route['stops_sum']-1)
        #  Number of containers per stop [1]
        self.collection_container_per_stop = self.data_route['containers_sum'] / self.data_route['stops_sum']
        # Mean mass of containers per stop (can be as well float value) [kg]
        self.collection_mass_container_per_stop = self.data_route['container_mass'] * self.collection_container_per_stop

        # [s] Body operation time - loading time per container and multiplied with number of containers per stop
        self.t_loader = math.ceil(self.t_hydraulic * self.collection_container_per_stop)

        # [s] time acceleration till maximum speed
        self.t_a = math.ceil(self.speed_max / self.acceleration_const)
        # [s] time braking till vehicle stops
        self.t_b = self.t_a
        # [m] distance acceleration
        self.s_a = 0.5 * self.acceleration_const * self.t_a**2
        # [m] distance braking
        self.s_b = self.s_a
        # [m] distance constant speed
        self.s_v_max = self.collection_distance_per_stop - self.s_a - self.s_b
        # [s] time constant speed
        self.t_v_max = math.ceil(self.s_v_max/self.speed_max)


        ## Working cycle synthetization
        # [s] duration of a single working cycle
        duration_cycle = self.t_a + self.t_v_max + self.t_b + self.t_loader + self.t_wait

        route_speed = list()
        route_acceleration = list()
        route_loader_active = list()
        route_distance = list()
        route_container_mass = list()
        route_type = list()

        for j in range(0,(self.data_route['stops_sum']-1)):
            #initial values
            self.a_cycle = np.zeros(duration_cycle)
            self.v_cycle = np.zeros(duration_cycle)
            self.s_cycle = np.zeros(duration_cycle)
            self.loader_active_cycle = np.zeros(duration_cycle)
            self.container_mass = np.zeros(duration_cycle)

            # Wait phase
            for i in range(0, self.t_wait):
                self.a_cycle[i] = 0
                self.v_cycle[i] = 0
                self.s_cycle[i] = 0
                self.loader_active_cycle[i] = 0
                self.container_mass[i] = 0

            # loader phase
            for i in range((self.t_wait), (self.t_wait+self.t_loader+1)):
                self.a_cycle[i] = 0
                self.v_cycle[i] = 0
                self.s_cycle[i] = 0
                self.loader_active_cycle[i] = 1
                self.container_mass[i] = self.collection_mass_container_per_stop / (self.t_loader)

            # Acceleration phase
            while self.s_cycle[i-1] < (self.collection_distance_per_stop/2) and self.v_cycle[i-1] < self.speed_max:
                self.v_cycle[i] = min((self.v_cycle[i-1] + self.acceleration_const*self.timestep), self.speed_max)    # [m/s] speed with threshold of speed_max
                self.a_cycle[i] = self.v_cycle[i] - self.v_cycle[i-1]
                self.s_cycle[i] = 0.5*self.a_cycle[i]*self.timestep**2 + self.v_cycle[i-1]*self.timestep + self.s_cycle[i-1]
                self.loader_active_cycle[i] = 0
                self.container_mass[i] = 0
                i = i+1

            # constant speed phase
            while self.s_cycle[i-1] < (self.collection_distance_per_stop - (58.8+8.33)): # distance needed to brake from max speed
                self.a_cycle[i] = 0
                self.v_cycle[i] = self.speed_max
                self.s_cycle[i] = 0.5*self.a_cycle[i]*self.timestep**2 + self.v_cycle[i-1]*self.timestep + self.s_cycle[i-1]
                self.loader_active_cycle[i] = 0
                self.container_mass[i] = 0
                i = i+1

            # braking phase
            while self.s_cycle[i-1] < self.collection_distance_per_stop and self.v_cycle[i-1] > 0:
                self.v_cycle[i] = max((self.v_cycle[i-1] - self.acceleration_const*self.timestep), 0)       # [m/s] speed with threshold of 0m/s (to hinder negative speed)
                self.a_cycle[i] = (self.v_cycle[i] - self.v_cycle[i-1])
                self.s_cycle[i] = 0.5*self.a_cycle[i]*self.timestep**2 + self.v_cycle[i-1]*self.timestep + self.s_cycle[i-1]
                self.loader_active_cycle[i] = 0
                self.container_mass[i] = 0
                i = i+1

            # save arrays to struct
            route_speed = np.append(route_speed,self.v_cycle[:i])
            route_acceleration = np.append(route_acceleration,self.a_cycle[:i])
            route_loader_active = np.append(route_loader_active,self.loader_active_cycle[:i])
            route_container_mass = np.append(route_container_mass, self.container_mass[:i])
            route_distance = np.append(route_distance, self.s_cycle[:i])


        # Append last wait and loader phase
        # wait phase
        route_speed = np.append(route_speed, np.zeros(self.t_wait-1))
        route_acceleration = np.append(route_acceleration, np.zeros(self.t_wait-1))
        route_loader_active = np.append(route_loader_active, np.zeros(self.t_wait-1))
        route_container_mass = np.append(route_container_mass, np.zeros(self.t_wait-1))
        route_distance = np.append(route_distance, np.zeros(self.t_wait-1))

        # loader phase
        route_speed = np.append(route_speed, np.zeros(self.t_loader-1))
        route_acceleration = np.append(route_acceleration, np.zeros(self.t_loader-1))
        route_loader_active = np.append(route_loader_active, np.ones(self.t_loader-1))
        route_container_mass = np.append(route_container_mass, repmat((self.collection_mass_container_per_stop/(self.t_loader-1)),(self.t_loader-1),1))
        route_distance = np.append(route_distance, np.zeros(self.t_loader-1))

        #add charger power for all timesteps
        route_type = 2*np.ones(len(route_distance))
        route_charger_power = np.zeros(len(route_distance))

        ## Add results to DataFrame
        df_workphase = pd.DataFrame({'speed':route_speed,
                                     'acceleration':route_acceleration,
                                     'distance':route_distance,
                                     'loader_active':route_loader_active,
                                     'container_mass':route_container_mass,
                                     'phase_type':route_type,
                                     'charger_power':route_charger_power})

        return df_workphase



    def drivephase(self, phase_distance):
        '''
        Method creates drivephase load profile for drive there and drive back

        Parameters
        ----------
        None
        '''
        ## Input through function
        # Tour start point of driving cycle
        start = 1
        # Route needs to be finished inside driving cycle --> length(drivecycle_distance)

        # Define stopping distance for braking at end of drive there and drive back
        stopping_distance = 0

        #Get data from drivecycle and convert to numpy array
        drivecycle_speed = self.drivecycle.get_speed().values
        drivecycle_acceleration = self.drivecycle.get_acceleration().values
        drivecycle_distance = self.drivecycle.get_distance().values

        ## Get part of driving cycle
        # in case drive distance is shorter than dc distance
        if phase_distance <= drivecycle_distance[-1]:
            # get duration of first element smaller than the drive distance and stopping distance
            duration = len(drivecycle_distance[drivecycle_distance < (phase_distance-stopping_distance)])
            # Get spped/acceleration value of drive cycle till stopping event
            route_speed = drivecycle_speed[start : (start+duration)]
            route_acceleration = drivecycle_acceleration[start : (start+duration)]
            route_distance = drivecycle_distance[start : (start+duration)]

        # in case drive distance is longer than dc distance
        else:
            # get howl muliple of full cycles & the "rest" (decimal place) of the cycle
            duration = (phase_distance / drivecycle_distance[-1])
            rest = math.floor((duration - math.floor(duration)) * len(drivecycle_distance))

            # dc values are repeated to distance (whole multiple) & the "rest" (decimal place)
            route_speed = repmat(drivecycle_speed, 1, math.floor(duration)).flatten()
            route_speed = np.append(route_speed, drivecycle_speed[0:rest])

            route_acceleration = repmat(drivecycle_acceleration, 1, math.floor(duration)).flatten()
            route_acceleration = np.append(route_acceleration, drivecycle_acceleration[0:rest])

            route_distance = repmat(drivecycle_distance, 1, math.floor(duration)).flatten()
            route_distance = np.append(route_distance, drivecycle_distance[0:rest])


        ## Append stopping event to drive cycle
        # Define/get stopping acceleration, speed
        acceleration_stopping = -1
        speed_stopping = route_speed[-1]
        #distance_stopping = phase_distance - route_distance[-1]

        # Append speed, acceleration and distance value to route array
        while speed_stopping > abs(acceleration_stopping):
            route_speed = np.append(route_speed, (speed_stopping + acceleration_stopping))
            route_acceleration = np.append(route_acceleration, acceleration_stopping)
            route_distance = np.append(route_distance, (max(route_distance) + (speed_stopping-acceleration_stopping)))

            speed_stopping = speed_stopping + acceleration_stopping


        # Add loader active and container_mass fields to array with 0
        route_loader_active =  route_distance * 0
        route_container_mass =  route_distance * 0;
        # Add route type & charger power with route phase length
        route_type = np.ones(len(route_distance))
        route_charger_power = np.zeros(len(route_distance))

        ## Add results to DataFrame
        df_workphase = pd.DataFrame({'speed':route_speed,
                                     'acceleration':route_acceleration,
                                     'distance':route_distance,
                                     'loader_active':route_loader_active,
                                     'container_mass':route_container_mass,
                                     'phase_type':route_type,
                                     'charger_power':route_charger_power})
        return df_workphase