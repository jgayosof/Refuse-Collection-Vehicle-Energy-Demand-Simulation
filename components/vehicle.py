import numpy as np
import math

from components.simulatable import Simulatable
from components.serializable import Serializable

class Vehicle(Serializable, Simulatable):
    '''
    Provides all relevant methods for the calculation of battery performance

    Attributes
    ----------
    Serializable: class. In order to load/save component parameters in json format
    Simulatable: class. In order to get time index of each Simulation step
    input_link: class. Class of component which supplies input power
    file_path: json file. Battery parameter load file

    Methods
    -------
    start
    calculate
    vehicle_driving_resistance
    vehicle_motor_electric
    vehicle_motor_diesel
    vehicle_loader_electric
    vehicle_loader_diesel
    '''


    def __init__(self, timestep, input_link, file_path = None):
        '''
        Parameters
        ----------
        timestep: int. Simulation timestep in seconds
        input_link: class. Class of component which supplies input power
        file_path : json file to load vehicle parameters
        '''
        # Read component parameters from json file
        if file_path:
            self.load(file_path)

        else:
            print('Attention: No json file for vehicle model specified')

        # Integrate simulatable class for time indexing
        Simulatable.__init__(self)
        # Integrate input power
        self.input_link = input_link
        # Timestep
        self.timestep = timestep

        ## Basic parameters vehicle
        # Payload vehicle [kg], m_max-m_empty
        self.mass_payload = self.mass_max - self.mass_empty

        # Initial cummulated vehicle mass (mass_empty + waste mass)
        self.mass_cum =self. mass_empty

        # Gravity [m/s2]
        self.grafity = 9.81


    def calculate(self):
        '''
        Method calculates all battery performance parameters by calling implemented methods

        Parameters
        ----------
        None
        '''
        # Vehicle mass, add and get mass of container from route curve
        self.mass_cum = self.mass_cum + self.input_link.container_mass[self.time]

        ## Vehicle is in operating (driving(1) or working(2)) mode
        if self.input_link.phase_type[self.time] != 0:

            # Vehicle loader
            # if loader is active load curve column loader is set to 1
            self.power_hydraulic = self.power_hydraulic_mean * self.input_link.loader_active[self.time];

            # Get vehicle loader power of lifter
            self.vehicle_loader()

            # Get vehicle driving resistance
            self.vehicle_driving_resistance()

            # Get required vehicle motor power, incl. losses
            self.vehicle_motor()

            # Define vehicle power:
            #    power --> goes to connected class
            #    power_electric / power_diesel for evaluation
            if self.specification == 'vehicle_electric':
                self.power = (-1)*(self.power_motor + self.power_loader_motor + self.power_aux)
                self.power_electric = self.power
                self.power_diesel = 0

            elif self.specification == 'vehicle_diesel':
                # Diesel: no vehicle_power_electric
                self.power = 0
                self.power_electric = self.power
                self.power_diesel = (-1)*(self.power_motor + self.power_loader_motor + self.power_aux)

            else:
                print('No vehicle type specified')

        ## Vehicle is in charge modus
        else:
            self.power_drive = 0
            self.power_motor = 0
            self.power_loader_motor = 0
            self.power = self.input_link.charger_power[self.time]


    def vehicle_driving_resistance(self):
        '''
        Vehicle driving resistance: Method calculates the driving resistance power of vehicle [W]

        Parameters
        ----------
        None
        '''
        # Overall vehicle mass with increase for rotational mass  [kg]
        self.mass_rotational = self.mass_cum * self.m_add

        # Air resistance [N]
        self.F_air = 0.5 * self.rho_air * self.cw * self.front_area * (self.input_link.speed[self.time])**2
        # Rolling resistance [N]
        self.F_r = self.mass_rotational * self.grafity * self.cr * math.cos(self.alpha)
        # Slope resistance [N]
        self.F_sl= self.mass_rotational * self.grafity * math.sin(self.alpha)
        # Acceleration resistance [N]
        self.F_a = self.mass_rotational * self.input_link.acceleration[self.time]

        # Vehicle mechanical power demand [W]
        self.power_drive = ((self.F_air + self.F_r + self.F_sl + self.F_a) * self.input_link.speed[self.time])


    def vehicle_motor(self):
        '''
        Vehicle motor model: Method calculates the electric and diesel motor input power [W]

        Parameters
        ----------
        None
        '''
        # Drivetrain efficiency motor [1]
        self.eta_drivetrain = self.efficiency_motor * self.efficiency_transmission * self.efficiency_converter

        ## Electric motor specific recuperation
        if self.specification == 'vehicle_electric':
            # Engine in motor mode and below maximum motor power
            if self.power_drive >= 0 and self.power_drive < self.power_motor_max:
                # Motor inlet power [W]
                self.power_motor = self.power_drive / self.eta_drivetrain

            # Engine in motor mode and above maximum motor power
            elif self.power_drive >= 0 and self.power_drive > self.power_motor_max:
                # Motor inlet power [W]
                self.power_motor = self.power_drive / self.eta_drivetrain
                self.power_motor_max_overflow = 1
                print('vehicle engine in motor mode exceeds maximum engine power!')

            # Engine in generator mode and lower than maximum motor power
            elif self.power_drive <= 0 and self.power_drive > -self.power_motor_max:
                # Motor inlet power [W]
                self.power_motor = self.power_drive * self.eta_drivetrain

            # Engine in generator mode and higher than maximum motor power
            elif self.power_drive <= 0 and self.power_drive < -self.power_motor_max:
                # Motor inlet power [W]
                self.power_motor = - self.power_motor_max
                self.power_motor_max_overflow = -1
                print('vehicle engine in generator mode exceeds maximum engine power!')

            # Engine with no power or in generator mode & above maximum motor power
            else:
                self.power_motor = 0

        ## Diesel motor specific idle consumption
        elif self.specification == 'vehicle_diesel':
            # Engine in motor mode and below maximum motor power
            if self.power_drive > 0 and self.power_drive < self.power_motor_max:
                # Motor inlet power [W]
                self.power_motor = self.power_drive / self.eta_drivetrain

            # Engine in motor mode and above maximum motor power
            elif self.power_drive > 0 and self.power_drive > self.power_motor_max:
                # Motor inlet power [W]
                self.power_motor = self.power_drive / self.eta_drivetrain
                self.power_motor_max_overflow = 1
                print('vehicle engine in motor mode exceeds maximum engine power!')

            # Self consumption in idle mode (10.4 kWh/l * 3 l/h)
            elif self.power_drive == 0 and self.power_loader_motor == 0:
                #[W] Diesel engine self consumption (Varga 2018)
                self.power_motor = 10.4 * 3 * 1000

            # Engine with no power
            else:
                self.power_motor = 0

        else:
            print('no vehicle specification defined in json file!')


    def vehicle_loader(self):
        '''
        Vehicle loader model: Method calculates the inlet power of vehicle loader [W]
         Electric loader eficiency: 0.83 * 0.95 = 0.7785
         Diesel loader efficiency: 0.30

        Parameters
        ----------
        None
        '''
        # [W] electric loader inlet power
        self.power_loader_motor = self.power_hydraulic / self.efficiency_loader
