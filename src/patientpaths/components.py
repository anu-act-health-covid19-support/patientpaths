
import numpy as np

def allocate(num_strata,demand,capacity):
	admit = np.zeros([num_strata])
	excess = np.zeros([num_strata])
	for s in range(num_strata):
		admit[s] = np.minimum(demand[s], capacity)
		capacity = capacity - admit[s]
		excess[s] = demand[s] - admit[s]
	return admit,excess,capacity

def allocate_duration(num_strata,num_days,avail,d,LoS,demand):
	admit = np.zeros([num_strata])
	excess = np.zeros([num_strata])
	for s in range(num_strata):
		admit[s] = min(avail[d], demand[s])
		excess[s] = demand[s] - admit[s]
		x = np.minimum(d + LoS - 1, num_days);
		avail[d:x] = avail[d:x] - admit[s]
		avail[d:x] = np.max(avail[d:x], 0)
	return admit,excess
