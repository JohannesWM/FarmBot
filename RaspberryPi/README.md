# Farm-Bot
## System
### Goal
The farmbot system, which runs on the RaspberryPi4, has the goal of planting, analyzing, and nurturing its plants.
### Method
#### V.1.
##### Analyzing Plants
The current iteration of our farmbot project is unable to thoroughly analyze its plants, it lacks all but one sensor 
module: the moisture sensor.  In a future iteration, new modules such as cameras may be added to better analyze the plants,
and their corresponding health + conditions.
##### Planting 
At the beginning of its _run cycle_ the system begins a locally hosted web-server where the user can input/configure 
aspects of the _run._  Since the raspberry pi has been pre-configured to act as a wifi network, users can connect to it 
and be redirected to the flask web-app.  The web-application is very similar to the menu of a 3d printer: moves axes, plant seeds, maintain mode, settings.
###### Settings
Within the settings page there are many configurations to be made, for example what seed is stored in each dispenser, how long should water run for etc.
###### Plant Seeds
When a user selects plant seeds, they are prompted with more information, for example, what kind of seed, where, spacing, maintain after, etc..
**TODO ADD PROMPTED INFO.**  The farmbot then proceeds to plant the seeds with the pre-configured specifications.
###### Maintain Mode
This mode is only for maintaining the plants.  The preconfigured intervals determine how often 

