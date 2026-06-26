# McSim50

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Flask](https://img.shields.io/badge/Flask-2.x-lightgrey)
![SimPy](https://img.shields.io/badge/SimPy-DES-green)
![Plotly](https://img.shields.io/badge/Plotly-Interactive-orange)
![SQLite](https://img.shields.io/badge/SQLite-Database-lightblue)

A discrete event simulation engine modelling customer flow, resource allocation and queue behaviour in a fast food environment

## Demo
https://www.youtube.com/watch?v=S3PMURujmWo

## Technologies
**Languages:** Python, HTML, CSS, JavaScript

**Libraries:** Flask, Flask-Session, SimPy, NumPy, Pandas, Plotly Express, pytz, datetime

## How to Run
1. clone repo
2. pip install -r requirements.txt
3. flask run
4. open broswer and enter http://127.0.0.1:5000

## Features
- Simulate customer flow, staff and counter allocation using SimPy
- Customisable inputs: location, time period, counter capacity, staff count, duration and cycles
- Age-based customer behaviour affecting order size, ordering speed and food preference
- Time-based menus and customer arrival rate (morning, peak hour, night)
- Location-based arrival rate (regional vs metro)
- Batch fries system using SimPy Container — no wait time if fries already prepped
- Warmup period for non-morning simulations to stabilise results before recording
- Multi-cycle simulation with reload prevention
- 6 interactive Plotly graphs including animated waiting time scatter
- Save simulation results to database and revisit anytime
- Activity log showing timestamped events during simulation
- User login and register with hashed passwords

## Project Structure
``` 
CS50-FINALPROJECT/
├── app.py              # Flask app and routes
├── mcsim1.py           # Simulation logic and OOP classes
├── help.py             # Helper functions, graph generation
├── requirements.txt
├── mcsim.db            # SQLite database
├── static/
│   └── style.css
└── templates/
    ├── layout.html
    ├── index.html      # Input form
    ├── gen.html        # Simulation results and graphs
    ├── graph.html      # Saved result graphs
    ├── log.html        # Activity log
    ├── save.html       # Saved simulations
    ├── login.html
    ├── register.html
    └── video.html
```
## How It Works
This simulation uses the SimPy package to handle concurrency and resource allocation. 
`app.py` contains the Flask integration; it collects input from the index page and 
stores it in `mcsim1.py` global variables. Each POST request empties the previous 
simulation data, and `/gen` runs the simulation, calculates results via `help.py`, 
and renders templates with graphs. The simulation run is limited by the length of 
the result list, this prevents re-running on page reload, only generating new 
results on POST from the index page.

Inside `mcsim1.py`, everything is organised in OOP. A `@classmethod` stores inputs 
and sets arrival rates and food weights based on location and time period. The 
`Customers` class assigns age using `numpy.random.choice`, which then determines 
ordering speed, order size and food preferences. Younger customers order more, 
middle-aged customers order moderately, and older customers order less.
Then each weight is standardised. The choice of foods is also determined by time of operation; 
morning will have a breakfast meal and lower weight on ordering ice cream in the morning, etc. 

## Engineering Decisions & Challenges 

### Patient Time (Abandoned) 
I tried to simulate behavioural patterns by randomly assigning each customer a patience threshold. I discovered this breaks waiting time calculation, as recorded wait time would reflect when a customer left rather than true queue time. I spent a couple of days working through three different approaches: 

Approach 1: AllOf events: Appended all food prep processes into a list and yielded them together using SimPy's `AllOf`. This enforced strict FIFO but the patience check never triggered correctly, events were appended instantly so the time check was almost never true.

Approach 2: Boolean live check: Ran a separate process per customer to monitor patience in real time. Same problem; events appended instantly so the check never ran properly. 

Approach 3: Sequential yield in for loop: Yielded each food prep process individually instead of using `AllOf`. This unlocked a loose FIFO where large orders could be overtaken by later customers, which is more realistic in theory. The patience check worked this time, but average waiting time dropped significantly under extreme parameters, confirming it corrupted the metric. These calculations remain in the code but are commented out. 

### Staff & Kitchen Assumptions 
Counter staff and kitchen staff are treated as separate resources, neither can perform the other's role. Each food item is prepared by one person using a random exponential mean time rather than split across stations. 

### Fries Container System 
Fries are handled using SimPy's `Container` (a mutable resource). When a customer orders fries, the simulation checks the container level. If enough fries are available, one is taken immediately with no wait time. If not, a full prep process runs and 4 fries are added to the container, simulating batch grilling.