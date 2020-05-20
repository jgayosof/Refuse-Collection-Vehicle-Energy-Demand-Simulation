from components.simulatable import Simulatable
from components.serializable import Serializable

class Charger(Serializable, Simulatable):
    '''
    Static grid charger class
    Provides static full capacity efficiency for charge and discharge case
    !!! Charger power is defined as power flow from (charge case) / to (discharge case) grid !!!

    Info: Charger is modeled with static efficiency curve for charge/discharge case

    Attributes
    ----------
    Serializable: class. In order to load/save component parameters in json format
    Simulatable : class. In order to get time index of each Simulation step

    Methods
    -------
    None
    '''

    def __init__(self, power_grid, file_path):
        '''
        Parameters
        ----------
        power_grid : float. Charger power from/to grid
            Charge case:
                Positive power value (taken from grid)
            Discharge case:
                Negative power value (supplied to grid)
        file_path : json file to load grid charger parameters
        '''

        # Read component parameters from json file
        if file_path:
            self.load(file_path)

        else:
            print('Attention: No json file for power component efficiency specified')

        ## Decision of charge/discharge case and efficiency detection
        # Discharge
        if power_grid < 0:
            self.efficiency = self.efficiency_discharging
        # Charge
        if power_grid > 0:
           self.efficiency = self.efficiency_charging

        self.power = power_grid * self.efficiency
