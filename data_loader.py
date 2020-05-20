import pandas

class CSV:
    '''
    CSV loader for loading csv file of load profile

    Attributes
    ----------
    file_name : str
        file path and name of csv file
    i : int
        row number of csv dataset

    Methods
    -------
    load(file_name)
        loads the csv file and stores it in parameter __data_set
    get_column(i)
        extracts row of __data_set
    '''

    def read_csv(self, file_name):
        '''loads the csv file and stores it in parameter __data_set

        Parameters
        -----------
        file_name : str
            file path and name of csv file
        '''
        self.__data_set = pandas.read_csv(file_name, comment='#', header=None, decimal='.', sep=';')


    def get_colomn(self, i):
        '''extracts row of __data_set

        Parameters
        -----------
        i : int
            row number of csv dataset

        Returns
        -------
            __data_set with extracted row
        '''

        return self.__data_set[:][i]


class DriveCycle(CSV):
    '''
    Data loader for extracting data from drivecycle csv file

    Attributes
    ----------
    nothing needed

    Methods
    -------
    get_speed
    get_acceleration
    get_distance
    '''

    def get_speed(self):
        '''returns speed profile'''
        return super().get_colomn(0)

    def get_acceleration(self):
        '''returns acceleration profile'''
        return super().get_colomn(1)

    def get_distance(self):
        '''returns distance profile'''
        return super().get_colomn(2)