from components.simulatable import Simulatable
from components.serializable import Serializable


class Power_Component(Serializable, Simulatable):
    '''
    Provides all relevant methods for the efficiency and aging calculation of power_components
    Model is based on method by Sauer and Schmid [Source]

    Attributes
    ----------
    Serializable: class. In order to load/save component parameters in json format
    Simulatable : class. In order to get time index of each Simulation step
    input_link : class. Class of component which supplies input power

    Methods
    -------
    calculate
    __calculate_power_output
    __calculate_power_input
    '''

    def __init__(self, timestep, input_link, file_path = None):
        '''
        Parameters
        ----------
        timestep: int. Simulation timestep in seconds
        input_link : class. Class of component which supplies input power
        file_path : json file to load power component parameters
        '''
        # Read component parameters from json file
        if file_path:
            self.load(file_path)

        else:
            print('Attention: No json file for power component efficiency specified')

        # Integrate Simulatable class for time indexing
        Simulatable.__init__(self)
        # Integrate input power
        self.input_link = input_link
        # [s] Timestep
        self.timestep = timestep

        # Calculate star parameters of efficeincy curve
        self.voltage_loss_star =  self.voltage_loss
        self.resistance_loss_star  = self.resistance_loss / self.efficiency_nominal
        self.power_self_consumption_star  =  self.power_self_consumption * self.efficiency_nominal

        ## Power model
        # Initialize power
        self.power = 0


    def calculate(self):
        '''
        Method calculates all power component parameter by calling implemented methods
        Decides weather input_power or output_power method is to be called

        Parameters
        ----------
        None
        '''
        # Calculate the Power output or input
        if self.input_link.power >= 0:
            self.__calculate_power_output()
        if self.input_link.power < 0:
            self.__calculate_power_input()


    def __calculate_power_output (self):
        '''
        Power Component Power output model:
        Method to calculate the Power output dependent on Power Input P_out(P_in)

        Parameters
        ----------
        None
        '''
        if self.input_link.power == 0:
            self.power_norm = 0.
            self.efficiency = 0.
        else:
            power_input = min(1, self.input_link.power / self.power_nominal)
            self.efficiency = -((1 + self.voltage_loss_star) / (2 * self.resistance_loss_star * power_input)) \
                    + (((1 + self.voltage_loss_star)**2 / (2 * self.resistance_loss_star * power_input)**2) \
                    + ((power_input - self.power_self_consumption_star) / (self.resistance_loss_star * power_input**2)))**0.5
            self.power_norm = power_input * self.efficiency

            # In case of negative efficiency it is set to zero
            if self.efficiency < 0:
                self.efficiency = 0
            # no negative power flow as output possible
            # Assumption component goes to stand by mode and self consumption is reduced
            if self.power_norm < 0:
                self.power_norm = 0

        self.power = self.power_norm * self.power_nominal


    def __calculate_power_input (self):
        '''
        Power Component input model:
        Method to calculate the Power input dependent on Power Output P_in(P_out)
        Calculated power output is NEGATIVE but fuction can only handle Positive value
        Therefore first abs(), at the end -

        Parameters
        ----------
        None
        '''

        #power_output = min(1, abs(self.input_link.power) / self.power_nominal)
        power_output = (abs(self.input_link.power) / self.power_nominal)

        self.efficiency = power_output / (power_output + self.power_self_consumption + (power_output * self.voltage_loss) \
                   + (power_output**2 * self.resistance_loss))

        self.power_norm = power_output / self.efficiency
        self.power = - (self.power_norm * self.power_nominal)