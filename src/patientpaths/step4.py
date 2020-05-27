import numpy as np

def step4(d, moc, num_days, num_strata, want_beds, risk):

	#declare locals
	#% The daily demand for bed occupancy for each strata.
	req_icu = np.zeros([num_strata])
	#% Identify cohorts with increased risk of ICU admission and death.
	frac_ward_to_ICU = moc.ward_to_ICU * np.ones([num_strata, 1])
	frac_ward_to_ICU[risk > 1] = moc.ward_to_ICU_highrisk
	frac_ICU_to_death = moc.ICU_to_death * np.ones([num_strata, 1])
	frac_ICU_to_death[risk > 1] = moc.ICU_to_death_highrisk
	#% Halve the survival rate for cases that require ICU admission but cannot
	#% be admitted into an ICU.
	frac_noICU_to_death = 1 - 0.5 * (1 - frac_ICU_to_death)

	#declare outputs
	#% Daily number of cases we want to admit to wards.
	try_ward = np.zeros([num_strata])
	req_ward = np.zeros([num_strata])
	admit_icu = np.zeros([num_strata])
	avail_icu = np.tile(moc.cap_ICU, [num_days])
	excess_icu = np.zeros([num_strata])
	#% Daily deaths.
	deaths = np.zeros([num_strata])

	#%
	#% Step 4: Hospital admissions -- how many can we put in ICU beds?
	#%
	for s in range(num_strata):
		#% Determine who needs ward beds and ICU beds.
		req_icu[s] = want_beds[s] * frac_ward_to_ICU[s]
		try_ward[s] = want_beds[s] - req_icu[s]
		req_ward[s] = try_ward[s]

		#% Determine who gets ICU beds.
		admit_icu[s] = min(avail_icu[d], req_icu[s])
		excess_icu[s] = req_icu[s] - admit_icu[s]
		try_ward[s] = try_ward[s] + excess_icu[s]

		#% Schedule patients to occupy beds for multiple days.
		x = np.minimum(d + moc.LoS_ICU - 1, num_days);
		avail_icu[d:x] = avail_icu[d:x] - admit_icu[s] #Originally: bsxfun(@minus, avail_icu[:, d:x], admit_icu[:, s, d])
		avail_icu[d:x] = np.max(avail_icu[d:x], 0)

		#% Calculate deaths, on the assumption that not getting an ICU
		#% bed halves the survival rate.
		deaths[s] = np.squeeze(admit_icu[s]) * frac_ICU_to_death[s] + np.squeeze(excess_icu[s]) * frac_noICU_to_death[s]

	return try_ward, req_ward, admit_icu, avail_icu, excess_icu, deaths

