import simpy
import random

# Simulation parameters
SIMULATION_TIME = 720  # Simulation time in minutes
NUM_BERTHS = 2  # Number of available berths
NUM_QUAY_CRANES = 2  # Number of available quay cranes
NUM_TRUCKS = 3  # Number of available trucks
NUM_VESSEL = 4  # Number of vessels to simulate
AVERAGE_VESSEL_ARRIVAL_INTERVAL = 5 * 60  # Average time between vessel arrivals in minutes
CONTAINERS_PER_VESSEL = 150  # Number of containers carried by each vessel
CRANE_CONTAINER_TIME = 3  # Time taken by a quay crane to load/unload one container in minutes
TRUCK_TRANSPORT_TIME = 6  # Time taken by a truck to transport a container in minutes


class Terminal:
    """
    Terminal class representing the container terminal
    """

    def __init__(self, env):
        self.env = env

        # resource representing the available berths
        self.berths = simpy.Resource(env, capacity=NUM_BERTHS)

        # process of available quay cranes
        self.quay_cranes = [QuayCrane(env, f"QC{i}") for i in range(1, NUM_QUAY_CRANES + 1)]

        # process the truck on the terminal
        self.trucks = [Truck(env, f"T{i}") for i in range(1, NUM_TRUCKS + 1)]

    # used for the printing event and  to log events with timestamp
    def log(self, message):
        print(f"{self.env.now}: {message}")


class Vessel:
    """
        Vessel class representing a vessel arriving at the terminal
    """

    def __init__(self, env, name, terminal):
        self.env = env
        self.name = name
        self.terminal = terminal
        self.containers_left = CONTAINERS_PER_VESSEL

        # start the process of vessel arrival on berth
        self.action = env.process(self.arrive())

    def arrive(self):
        """
                the arrival method is  for the  arrival of the vessels
        """

        # vessel arrival message print
        self.terminal.log(f"Vessel {self.name} arrives at the terminal.")

        # now request a berth for the vessel
        berth_request = self.terminal.berths.request()

        yield berth_request

        # vessel berthing message print
        self.terminal.log(f"Vessel {self.name} berths.")

        # Assign a quay crane to the vessel
        crane = self.terminal.quay_cranes.pop(0)  # Assign the next available crane

        # Unload containers from the vessel using the assigned quay crane
        while self.containers_left > 0:
            yield self.env.process(crane.load_container(self))

        # Return the quay crane to the pool after unloading
        self.terminal.quay_cranes.append(crane)

        # Release the berth
        self.terminal.berths.release(berth_request)

        # Log vessel departure
        self.terminal.log(f"Vessel {self.name} leaves the terminal.")


class QuayCrane:
    """
    QuayCrane class representing a quay crane at the terminal which is used for the unloading container from vessel and
    load on the trucks
    """

    def __init__(self, env, name):
        self.env = env
        self.name = name

    def load_container(self, vessel):
        """
        Method representing loading/unloading containers using the quay crane
        :param vessel: vessel container which we want to load on the trucks
        :return:
        """
        # Log container loading/unloading process
        vessel.terminal.log(f"Quay Crane {self.name} starts loading container from Vessel {vessel.name}.")

        # Simulate the time taken to load/unload one container
        yield self.env.timeout(CRANE_CONTAINER_TIME)

        # Update the number of containers left on the vessel
        vessel.containers_left -= 1

        # Log completion of container loading/unloading
        vessel.terminal.log(f"Quay Crane {self.name} loads container from Vessel {vessel.name}.")


class Truck:
    """
    Truck class representing a truck at the terminal which is used for the loading container from vessel using cranes
    """
    def __init__(self, env, name):
        self.env = env
        self.name = name

    def transport_container(self, vessel):
        """
        Process representing transporting a container from the quay crane to the yard
        :param vessel: vessel container
        :return:
        """
        # Log container transportation process
        vessel.terminal.log(f"Truck {self.name} starts transporting container from Vessel {vessel.name} to yard.")

        # Simulate the time taken to transport a container
        yield self.env.timeout(TRUCK_TRANSPORT_TIME)

        # Log completion of container transportation
        vessel.terminal.log(f"Truck {self.name} delivers container from Vessel {vessel.name} to yard.")


def vessel_on_the_terminal(env, terminal):
    """
        Generator function for vessels arriving at the terminal
    :param env: it is a simulation environment
    :param terminal: it is a terminal
    :return: nothing
    """

    for i in range(1, NUM_VESSEL + 1):

        # Generate vessels with an exponential interval between arrivals
        yield env.timeout(random.expovariate(1 / AVERAGE_VESSEL_ARRIVAL_INTERVAL))

        # Check if a berth is available before generating a new vessel
        if len(terminal.berths.queue) < NUM_BERTHS:

            # Create a new vessel
            Vessel(env, f"V{i}", terminal)


# Create a simulation environment
env = simpy.Environment()

# Create a terminal object
terminal = Terminal(env)

# Start the vessel generator process
env.process(vessel_on_the_terminal(env, terminal))

# Run the simulation until the specified time
env.run(until=SIMULATION_TIME)
