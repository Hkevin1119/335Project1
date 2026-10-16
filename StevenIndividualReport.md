Individual Contribution Report  
Steven Price

Role: Data & Matching Lead  
<br/>As the data and matching lead I mainly focused on creating the input files for the project. I created loader.py as a way to load the raw JSON file data into compatible data by converting each recipient dictionary into objects. Here I used the JSON dictionary format for key pair lookup so that each object of recipients, volunteers, and donations could have their attributes properly mapped to our dataclass instances enabling dot-notation attribute access. One problem that came up was that even though the dataclasses are immutable, the accepted_types attribute within the Recipient dataclass remained mutable. Because of this I had to convert the list to a frozenset when loading the data. The end result created lists of objects with immutable attributes labeled by their classes.

Additionally, I created the simulation portion of the project. This part encompassed calling on the fifo.py and greedy.py as well as loader.py to output legible results. It calls on fifo.py and greedy.py to provide their respective results and provide explanations as predescribed in matching.py and greedy.py. The exact output is “(Status.’ASSIGNED or UNASSIGNED’) Donation ‘donation id’ (‘amount’) ‘decision reason [‘volunteer id’ ‘pickup time’ ‘capacity reason’]’. The decision reason changes based on the specific circumstances.

AI Disclosure: Gemini was used to help in producing JSON sample files for testing for specific outputs.

External Sources: Geeks for Geeks JSON python reading was used in helping implement JSON file reading in python as I’m inexperienced in reading JSON files using python. 
