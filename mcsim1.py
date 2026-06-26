import simpy
import numpy as np
import random


class Global_Variables:
    counter_capacity = 2
    stuff_capacity = 10
    customer_arrival_mean = 1
    
    time = ''
    location = ''

    t_stop_accept_order = 0

    run_amount = 330
    waiting_list = []
    customer_count_list = []
    customer_served_list = []
    len_serve_list = 0
    avg_waiting_list = []
    cyc_waiting_list = []

    customer_total = 0

    FRIES_PRE_TIME = 1.3

    warmup_period = 30
    warmup_check = False

    age_weight = [1/3, 1/3, 1/3]
    food_weight = [(1/8)] * 8

    run_cycle = 1

    end_time_list = []
    log_list = []
    input = {}
    sim_result = []
    total_sim_result = []

    @classmethod
    def ask_input(cls, location, time, cap, staff, duration, cycle):

        cls.run_amount = duration
        
        cls.input = {
            "location": location,
            "time": time,
            "counter": cap,
            "staff": staff,
            "duration": duration,
            "cycle": cycle
        }

        if cls.input["time"] != "morning":
            cls.warmup_check = True
            cls.run_amount += cls.warmup_period

        if cls.input["time"] == "morning":
            cls.customer_arrival_mean *= 1.
            cls.age_weight = [2/10, 5/10, 3/10]
            cls.food_weight = np.array([4/23, 2/23, 1/23, 5/23, 2/23, 1/23, 2/23, 6/23], dtype=float)
        if cls.input["time"] == "peakhour":
            cls.customer_arrival_mean *= 1.4
            cls.age_weight = [4/10, 5/10, 1/10]
            cls.food_weight = np.array([5/23, 4/23, 4/23, 2/23, 4/23, 4/23, 4/23, 0], dtype=float)
        if cls.input["time"] == "night":
            cls.customer_arrival_mean *= 0.9
            cls.age_weight = [3/10, 4/10, 3/10]
            cls.food_weight = np.array([5/27, 4/27, 4/27, 3/27, 4/27, 3/27, 4/27, 0], dtype=float)
        if cls.input["location"] == "regional":
            cls.customer_arrival_mean *= 1
        if cls.input["location"] == "metro":
            cls.customer_arrival_mean *= 1.2

        rand_factor = np.random.uniform(0.8, 1.2)
        cls.food_weight *= rand_factor

        cls.food_weight /= cls.food_weight.sum()

class Customers:

    def __init__(self, id):
        self.id = id

        #self.patient = np.random.exponential(scale=8)

        self.ordering_time = 0
        self.waiting_time = 0
        #self.patient_leave = 0
        nums = np.arange(1,9)
        self.age = np.random.choice(["young", "middleage", "old"], p=Global_Variables.age_weight)

        if self.age == "young":
            self.ordering_time = np.random.exponential(0.7)
            order_weights = nums / nums.sum()
        elif self.age == "middleage":
            self.ordering_time = np.random.exponential(1)
            order_weights = [0.05, 0.1, 0.15, 0.2, 0.2, 0.15, 0.1, 0.05]
            order_weights = np.array(order_weights) / sum(order_weights)
        else:
            self.ordering_time = np.random.exponential(1.5)
            order_weights = 1 / nums
            order_weights /= order_weights.sum()
        
        self.order_amount = np.random.choice(nums, p=order_weights)
        self.food_order = {}
        for i in range(self.order_amount):
            name, time = self.food_service_time()
            if name in self.food_order:
                self.food_order[name].append(time)
            else:
                self.food_order[name] = [time]


    def food_service_time(self):
        food_waiting_time = {
            "Burger": 1.5, "Nugget": 1.5,
            "Cold_Drinks": 0.3, "Hot_Drinks": 0.8,
            "Salad": 0.7, "IceCream": 0.5,
            "Fries": Global_Variables.FRIES_PRE_TIME, "breakfast_meal": 1.1
        }
        food = np.random.choice(list(food_waiting_time.keys()), p=Global_Variables.food_weight)
        return food, (np.random.exponential(food_waiting_time[food]))
class Mcdonald_Sim:
    def __init__(self):
        self.env = simpy.Environment()
        self.customer_counter = 0

        self.counters = simpy.Resource(self.env, capacity=Global_Variables.input["counter"])
        self.stuffs = simpy.Resource(self.env, capacity=Global_Variables.input["staff"])
        self.fries = simpy.Container(self.env, capacity=8, init=0)
    def customer_arrival(self):
        while self.env.now + Global_Variables.t_stop_accept_order < Global_Variables.run_amount:
            #increment current customer
            self.customer_counter += 1
            #generate customer arrival time
            t_arrive = np.random.exponential(1./Global_Variables.customer_arrival_mean)
            #pause time at when customer arrived
            yield self.env.timeout(t_arrive)
            #create customer from customers class
            current_customer = Customers(self.customer_counter)
            #run simulation for counter
            self.env.process(self.process_run(current_customer))

    def food_prepare(self, current_customer, food, prepare_time, i, t_arrive):
        with self.stuffs.request() as request:
            yield request                
            Global_Variables.log_list.append(f"{self.env.now} Customer {current_customer.id} {food} {i} getting prepared")
            yield self.env.timeout(prepare_time)
            Global_Variables.log_list.append(f"{self.env.now} Customer {current_customer.id} {food} {i} finished")   
    def process_run(self, current_customer):
        events = []
        t_arrive = self.env.now
        if t_arrive > Global_Variables.warmup_period or not Global_Variables.warmup_check:
                Global_Variables.customer_total += 1

        Global_Variables.log_list.append(f"{self.env.now} Customer {current_customer.id} arrived")

        with self.counters.request() as request:
            yield request
            current_customer.waiting_time = self.env.now - t_arrive
            '''if current_customer.waiting_time > current_customer.patient:
                if t_arrive > Global_Variables.warmup_period or not Global_Variables.warmup_check:
                    Global_Variables.sim_result.append({"t_arrive": t_arrive,
                                                "t_waiting": current_customer.waiting_time,
                                                "left": True})
                print(f"Customer {current_customer.id} leaves due to impatient")
                Global_Variables.log_list.append(f"Customer {current_customer.id} leaves due to impatient")
                return'''
            foods = [str(foods) for foods in current_customer.food_order.keys()]    
            log_entry = f"{self.env.now} Customer {current_customer.id} ordered " + ", ".join(foods)
            Global_Variables.log_list.append(log_entry)

            yield self.env.timeout(current_customer.ordering_time)
            t_ordered = self.env.now
            Global_Variables.log_list.append(f"{self.env.now} Customer {current_customer.id} finished ordering")

        for food, prep_times in current_customer.food_order.items():
            for i, prep_time in enumerate(prep_times):
                '''if current_customer.waiting_time > current_customer.patient:
                current_customer.waiting_time = self.env.now - t_arrive
                if t_arrive > Global_Variables.warmup_period or not Global_Variables.warmup_check:
                    Global_Variables.sim_result.append({"t_arrive": t_arrive,
                                                "t_waiting": current_customer.waiting_time,
                                                "left": True})
                print(f"Customer {current_customer.id} leaves due to impatient")
                Global_Variables.log_list.append(f"Customer {current_customer.id} leaves due to impatient")
                return'''
                if food == "Fries" and self.fries.level > 1:
                    yield self.fries.get(1)
                elif food == "Fries" and self.fries.level < 1:
                    yield self.env.process(self.food_prepare(current_customer, food, prep_time, i, t_arrive))
                    yield self.fries.put(4)
                    yield self.fries.get(1)
                else:
                    yield self.env.process(self.food_prepare(current_customer, food, prep_time, i, t_arrive))

    
        current_customer.waiting_time += (self.env.now - t_ordered)

        if t_arrive > Global_Variables.warmup_period or not Global_Variables.warmup_check:
            Global_Variables.sim_result.append({"t_arrive": t_arrive,
                                                "t_waiting": current_customer.waiting_time,
                                                "left": False})
        Global_Variables.log_list.append(f"{self.env.now} customer {current_customer.id} leaves")


    def run(self):
        
        Global_Variables.sim_result = []
        Global_Variables.customer_total = 0


        self.env.process(self.customer_arrival())
        self.env.run()
        
        Global_Variables.end_time_list.append(self.env.now - Global_Variables.run_amount)
        Global_Variables.total_sim_result.append(Global_Variables.sim_result)