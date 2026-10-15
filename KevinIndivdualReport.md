Individual Contribution Report  
Kevin Huynh

Role: Algorithm & Optimization Lead  
<br/>I was the Algorithm & Optimization lead, the things I was primarily responsible for was the implementations of the FIFO scheduler, and the Greedy Rule. This is seen in the files as fifo.py and greedy.py. Fifo.py is rather simple just a single function that sorts and then orders the individual inputs of the list and then returns the input using the function run_in_order. Greedy.py is slightly more complex. It sorts primarily by the shelf life of each object in the list, it then sorts by quantity and finally the arrival order of the objects. This is based on the recommended rule given in the document. The schedule_greedy function is main function for how the greedy algorithm sorts it works similarly to fifo except uses the primary key (Shelf Life) instead of the default of arrival order in fifo.py.

Besides creating the algorithms I had also helped my group in the design of the greedy rules as well as the tests used for the program.

AI Disclosure: Claude AI was used within this project for help with debugging as well as the initial drafting/design of the algorithms. AI was also used for the creation of the individual contribution report through the use of spell checkers and auto correct programs (Grammarly)