# Refuse Collection Vehicle Simulation

### About

This tool includes an object oriented programmed energy demand simulation of a waste collection vehicle. The backwards simulation has a resolution of one second. All related power flows of the vehicle are modeled and can be analyzed.  

### Features

1. Models for electric and diesel driven vehicle drivetrains, the vehicle body, the vehicle route and in case of an electric vehicle a battery, battery management and charger model included. 

   *All component models stored in the folder components.*

2. Models are fully serializable, component parameter are stored in json files.

   *All model parameters stored in the folder data/components*

3. Vehicle route is synthesized on route parameter and normalized driven cycles.

   *Route parameters are stored in the folder data/load*

   

### Getting started

Sample component and route data is provided. Test simulation can be started with file *MAIN.py*, results will be stored in folder *results* and include general evaluation parameters as energy consumption and detailed timeseries powerflows of all relevant components.



###  Remark

The simulation tool was developed during a research project. Research results obtained on the basis of the model will be published in the upcoming months and will be referenced here.





