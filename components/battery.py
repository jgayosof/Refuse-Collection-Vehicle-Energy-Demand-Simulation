import numpy as np
from components.simulatable import Simulatable
from components.serializable import Serializable

class Battery(Serializable, Simulatable):
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
    battery_temperature
    battery_power
    battery_state_of_charge
    battery_charge_discharge_boundary
    battery_aging_calendar
    battyr_aging_cycling
    battery_state_of_destruction
    '''

    def __init__(self, timestep, input_link, file_path = None):
        '''
        Parameters
        ----------
        timestep: int. Simulation timestep in seconds
        input_link: class. Class of component which supplies input power
        file_path : json file to load battery parameters
        '''

        # Read component parameters from json file
        if file_path:
            self.load(file_path)

        else:
            print('Attention: No json file for battery model specified')

        # Integrate simulatable class for time indexing
        Simulatable.__init__(self)
        # Integrate input power
        self.input_link = input_link
        # [s] Timestep
        self.timestep = timestep

        ##Basic parameters
        self.specification = self.specification
        ##Power model
        # [Wh] Current battery nominal capacity at nominal C-Rate
        self.capacity_current_wh = self.capacity_nominal_wh
        # Initialize initial paremeters
        self.state_of_charge = 0.9

        ## Temperature model
        # [kg] Mass of the battery
        self.mass =  self.capacity_nominal_wh / self.energy_density_kg
        # [m^2] Battery area
        self.surface = self.capacity_nominal_wh / self.energy_density_m2
        # Initialize initial parameters
        self.temperature = 298.15
        self.power_loss = 0.


    def calculate(self):
        '''
        Method calculates all battery performance parameters by calling implemented methods

        Parameters
        ----------
        None
        '''
        ## Battery
        # Get Battery temperature
        self.battery_temperature()

        ## Calculate theoretical battery power and state of charge with available input power
        self.power = self.input_link.power
        # Get effective charge/discharge power
        self.battery_power()
        #Set power to battery power
        self.power = self.power_battery
        # Get State of charge and boundary
        self.battery_state_of_charge()
        self.battery_charge_discharge_boundary()

        # Check weather battery is capable of discharge/charge power provided
        # Discharge case
        if self.input_link.power < 0:
            # Calculated SoC is under boundary - EMPTY
            if (self.state_of_charge < self.charge_discharge_boundary):
                # Recalc power
                self.power_battery = (self.power + ((abs(self.state_of_charge - self.charge_discharge_boundary)
                                    - self.power_self_discharge_rate) * self.capacity_current_wh / (self.timestep/3600))).round(4)

                # Validation if power can be extracted or new soc is higher than old soc (positiv battery_power for charge case)
                if self.power_battery > 0: # new boundary is higher than current soc, stay at old soc, no battery power
                    self.power_battery = 0.
                    self.state_of_charge = self.state_of_charge_old
                
                else:
                    self.state_of_charge = self.charge_discharge_boundary

        # Charge case
        elif self.input_link.power > 0:
            # Calculated SoC is above boundary - FULL
            if (self.state_of_charge > self.charge_discharge_boundary):
                # Recalc power and set state of charge to maximum charge boundary
                self.power_battery = (self.power - ((abs(self.state_of_charge - self.charge_discharge_boundary)
                                    + self.power_self_discharge_rate) * self.capacity_current_wh / (self.timestep/3600))).round(4)

                # Validation if power can be added or new soc is lower than old soc (negative battery_power for charge case)
                if self.power_battery < 0: # new boundary is lower than current soc, stay at old soc, no battery power
                    self.power_battery = 0.
                    self.state_of_charge = self.state_of_charge_old
                
                else:
                    self.state_of_charge = self.charge_discharge_boundary


    def battery_temperature(self):
        '''
        Battery Thermal Model: Method calculates the battery temperature in Kelvin [K]

        Parameters
        ----------
        None
        '''
        # Static ambient temperature [K]
        self.temperature_ambient = 298.15

        # Battery temperature
        self.temperature = self.temperature + ((np.abs(self.power_loss) - \
                    self.heat_transfer_coefficient * self.surface * \
                    (self.temperature -  self.temperature_ambient)) / \
                    (self.heat_capacity * self.mass / self.timestep))


    def battery_power(self):
        '''
        Battery stationary power model: Method calculates the battery efficiency & charging/discharging power in Watt [W]

        Parameters
        ----------
        None
        '''
        #ohmic losses for charge or discharge
        if self.power > 0.: #charge
            self.efficiency = self.charge_power_efficiency_a * (self.power/self.capacity_nominal_wh) + self.charge_power_efficiency_b
            self.power_battery = self.power * self.efficiency

        elif self.power == 0.: #idle
            self.efficiency = 0
            self.power_battery = self.power * self.efficiency

        elif self.power < 0.: #discharge
            self.efficiency = self.discharge_power_efficiency_a*(abs(self.power)/self.capacity_nominal_wh) + self.discharge_power_efficiency_b
            self.power_battery = self.power / self.efficiency

        #Calculation of battery power loss
        self.power_loss = self.power - self.power_battery


    def battery_state_of_charge(self):
        '''
        Battery State of Charge model: Method calculates the SoC [1]

        Parameters
        ----------
        None

        Battery self discharge in [1/s]
        '''
        # save soc of last timestep
        self.state_of_charge_old = self.state_of_charge

        #caculate soc of current timestep
        self.state_of_charge = self.state_of_charge + (self.power / self.capacity_current_wh * (self.timestep/3600)) - (self.power_self_discharge_rate * self.timestep)
        self.state_of_charge = self.state_of_charge


    def battery_charge_discharge_boundary(self):
        '''
        Battery State of Charge Boundary model: Method defines battery charge/discharge boundaries [1]

        Parameters
        ----------
        None
        '''
        #Discharge
        if self.input_link.power < 0.:
            self.charge_discharge_boundary = self.end_of_discharge_a * (abs(self.power_battery)/self.capacity_nominal_wh) + self.end_of_discharge_b

        #Charge
        else:
            self.charge_discharge_boundary = self.end_of_charge_a * (self.power_battery/self.capacity_nominal_wh) + self.end_of_charge_b