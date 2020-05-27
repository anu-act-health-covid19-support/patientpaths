import numpy as np

def step23(moc, num_strata, sev_rpt_late_Clinic, sev_new_late_Clinic, sev_rpt_late_ED, sev_new_late_ED, frac_ward_avail):
#inputs: sev_rpt_late_Clinic, sev_new_late_Clinic, sev_rpt_late_ED, sev_new_late_ED, frac_ward_avail
#local: req_hosp_via_Clinic, clinic_cs, req_hosp_via_ED, ed_cs
#output: want_beds, avail_clinic, admit_clinic, excess_clinic, admit_ed, excess_ed, avail_ed

	#declare locals
	req_hosp_via_Clinic = np.zeros([1])
	clinic_cs = np.zeros([1])
	req_hosp_via_ED = np.zeros([1])
	ed_cs = np.zeros([1])

	#declare outputs
	want_beds = np.zeros([num_strata])
	avail_clinic = 0
	admit_clinic = np.zeros([num_strata])
	excess_clinic = np.zeros([num_strata])
	admit_ed = np.zeros([num_strata])
	excess_ed = np.zeros([num_strata])
	avail_ed = moc.cap_ED

	#% Okay, we now know how many will *attempt* to present in each
	#% setting *today* and how many will require hospitalisation:
	#%
	#%     req_hosp(:, :, d).
	#%
	#% To account for hospital admission capacity, which depends on ED
	#% capacity, which is itself a function of *yesterday's* ward
	#% utilisation, we need to step forward day by day.
	#%
	#% Recall that arrays are 10000 x 5 x 366 (samples x strata x days).
	#%

	#%
	#% Step 2: ED consultation capacity, given ward utilisation.
	#%
	avail_ed = avail_ed * np.minimum(moc.lm_ED_cap_E1 + (1 - moc.lm_ED_cap_E1) * frac_ward_avail / moc.lm_ED_cap_W0, 1)
	#%
	#% Step 3: Hospital admissions -- how many can we admit?
	#%
	for s in range(num_strata):
		#% Clinic admissions.
		req_hosp_via_Clinic = sev_rpt_late_Clinic[s] + sev_new_late_Clinic[s]

		clinic_cs = np.minimum(req_hosp_via_Clinic, avail_clinic)
		avail_clinic = avail_clinic - clinic_cs
		want_beds[s] = clinic_cs
		admit_clinic[s] = clinic_cs
		excess_clinic[s] = req_hosp_via_Clinic - clinic_cs

		#% ED admissions.
		req_hosp_via_ED = sev_rpt_late_ED[s] + sev_new_late_ED[s]
		ed_cs = np.minimum(req_hosp_via_ED, avail_ed)
		avail_ed = avail_ed - ed_cs
		want_beds[s] = want_beds[s] + ed_cs
		#% NOTE: here we record ED presentations that lead to admissions.
		#% Mild ED presentations are accounted for later on.
		admit_ed[s] = ed_cs
		excess_ed[s] = req_hosp_via_ED - ed_cs
	return want_beds, avail_clinic, admit_clinic, excess_clinic, admit_ed, excess_ed, avail_ed



