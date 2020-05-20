class Simulatable:
    '''
    Simulatable class - Parent class for System Simulation
    Provides basic methods for the power flow simulation
    Gives possibilities to access of each component calculated parameters at different timesteps

    Attributes
    ----------
    *childs : class. All classes which shall be simulated

    Methods
    -------
    calculate
    start
    end
    update
    '''

    def __init__(self, *childs):
        '''
        Parameters
        ----------
        *childs : class. All classes which shall be simulated
        '''
        #self.step_width = step_width
        self.time = -1
        self.childs = list(childs)


    def calculate(self):
        '''
        Null methods - stands for for calculation methods of component/other classes

        Parameters
        ----------
        None
        '''
        pass


    def start(self):
        '''
        Start Method, which initialize start method for all childs
        Sets time index to 0

        Parameters
        ----------
        None
        '''
        # Set time index to zero
        self.time = 0
        # Calls start method for all simulatable childs
        for child in self.childs:
            if isinstance(child, Simulatable):
                child.start()


    def end(self):
        '''
        End Method, which terminates Simulatable with end method for all childs
        Sets time index back to 0

        Parameters
        ----------
        None
        '''
        # Set time index back to 0
        self.time = 0
        # Calls end method for all simulatable childs
        for child in self.childs:
            if isinstance(child, Simulatable):
                child.end()


    def update(self):
        '''
        Method, which updates time index and goes to next simulation step

        Parameters
        ----------
        None
        '''
        # Call null method
        self.calculate()

        # Update time parameters with +1
        self.time += 1
        # Calls update method for all simulatable childs
        for child in self.childs:
            if isinstance(child, Simulatable):
                child.update()