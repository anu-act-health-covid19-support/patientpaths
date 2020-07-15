import numpy as np


# for a resource of a given capacity, and a demand vector from each of the cohorts
# allocate the resources to the demand in order, returning how many are admitted to the resource
# as a vector and the excess vector, and the new capacity
def allocate(num_strata, demand, capacity):
    admit = np.zeros([num_strata])
    excess = np.zeros([num_strata])
    for s in range(num_strata):
        admit[s] = np.minimum(demand[s], capacity)
        capacity = capacity - admit[s]
        excess[s] = demand[s] - admit[s]
    return admit, excess, capacity


# for a resource with an availability vector (capacity over days), and a demand vector each which demand the resource
# for LoS (length of stay) days, starting from day d, adjust the availability vector to admit the demand
# returninng the admit and excess vectors
def allocate_duration(num_strata, num_days, avail, d, LoS, demand):
    admit = np.zeros([num_strata])
    excess = np.zeros([num_strata])
    for s in range(num_strata):
        admit[s] = min(avail[d], demand[s])
        excess[s] = demand[s] - admit[s]
        x = np.minimum(d + LoS - 1, num_days)
        avail[d:x] = avail[d:x] - admit[s]
        avail[d:x] = np.max(avail[d:x], 0)
    return admit, excess
