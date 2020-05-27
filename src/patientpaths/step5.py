import numpy as np

def step5(d, moc, num_days, num_strata, try_ward):
#input: try_ward
#local: 
#output: admit_ward, avail_ward, excess_ward

	#declare locals

	#declare outputs
	admit_ward = np.zeros([num_strata])
	avail_ward = np.tile(moc.cap_Ward, [num_days])
	excess_ward = np.zeros([num_strata])

	#%
	#% Step 5: Hospital admissions -- how many can we put in ward beds?
	#%
	for s in range(num_strata):
		#% Determine who gets ward beds (second priority).
		#% Note: excess cases have *already* presented to an ED or Clinic, so
		#% we're done with them!
		admit_ward[s] = np.minimum(avail_ward[d], try_ward[s])
		excess_ward[s] = try_ward[s] - admit_ward[s]
		#% Schedule patients to occupy beds for multiple days.
		x = np.minimum(d + moc.LoS_Ward - 1, num_days)
		avail_ward[d:x] = avail_ward[d:x] - admit_ward[s] #Originally: bsxfun(@minus, avail_ward[:, d:x], admit_ward[:, s, d])
		avail_ward[d:x] = np.max(avail_ward[d:x], 0)

	return admit_ward, avail_ward, excess_ward

