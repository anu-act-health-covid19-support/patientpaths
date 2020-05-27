import numpy as np

def step23(moc, num_strata, sev_rpt_late_Clinic, sev_new_late_Clinic, sev_rpt_late_ED, sev_new_late_ED, frac_ward_avail):

	#declare outputs
	want_beds = np.zeros([num_strata])
	avail_clinic = 0
	admit_clinic_sev = np.zeros([num_strata])
	excess_clinic_sev = np.zeros([num_strata])
	admit_ed_sev = np.zeros([num_strata])
	excess_ed = np.zeros([num_strata])
	avail_ed = moc.cap_ED

	#%
	#% Step 2: ED consultation capacity, given ward utilisation.
	#%
	avail_ed = avail_ed * np.minimum(moc.lm_ED_cap_E1 + (1 - moc.lm_ED_cap_E1) * frac_ward_avail / moc.lm_ED_cap_W0, 1)
	#%
	#% Step 3: Hospital admissions -- how many can we admit?
	#%
	for s in range(num_strata):
		#% Clinic admissions.

		admit_clinic_sev[s] = np.minimum(sev_rpt_late_Clinic[s] + sev_new_late_Clinic[s], avail_clinic)
		avail_clinic = avail_clinic - admit_clinic_sev[s]
		want_beds[s] = admit_clinic_sev[s]
		excess_clinic_sev[s] = sev_rpt_late_Clinic[s] + sev_new_late_Clinic[s] - admit_clinic_sev[s]

		#% ED admissions.
		admit_ed_sev[s] = np.minimum(sev_rpt_late_ED[s] + sev_new_late_ED[s], avail_ed)
		avail_ed = avail_ed - admit_ed_sev[s]
		want_beds[s] = want_beds[s] + admit_ed_sev[s]
		excess_ed[s] = sev_rpt_late_ED[s] + sev_new_late_ED[s] - admit_ed_sev[s]
	return want_beds, avail_clinic, admit_clinic_sev, excess_clinic_sev, admit_ed_sev, excess_ed, avail_ed



