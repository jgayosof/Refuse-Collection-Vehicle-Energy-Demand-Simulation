import json

class Serializable:
    '''
    Class to make simulation serializable with json format

    Attributes
    ----------
    file_path : string. File path where to store json file

    Methods
    -------
    load
    save
    '''

    def __init__(self, file_path = None):
        '''
        Parameters
        ----------
        file_path : string. File path where to store json file
        '''
        self.file_path = file_path


    def load(self, file_path = None):
        '''
        Load method to load component parameter form json file

        Parameters
        ----------
        file_path : string. File path where to store json file
        '''
        # if no file_path is specified via load method it is taken from __init__method
        if not file_path:
            file_path = self.file_path

        # open json file from file_path
        with open(file_path, "r") as json_file:
            data = json.load(json_file)
            # Integrate content of json in component __init__ class
            self.__dict__ = data


    def save(self, file_path = None):
        '''
        Save method to save component parameter to json file

        Parameters
        ----------
        file_path : string. File path where to store json file
        '''
        # if no file_path is specified via load method it is taken from __init__method
        if not file_path:
            file_path = self.file_path

        # create json file in given file_path and save all parametrers given in __dict__ to it
        with open(file_path, "w") as json_file:
            obj_attributes = dict()
            for obj in self.__dict__:
                if not hasattr(self.__dict__[obj], '__dict__'):
                    obj_attributes[obj] = self.__dict__[obj]
            # final dump command with format parameter indent=4
            json.dump(obj_attributes, json_file, indent=4)