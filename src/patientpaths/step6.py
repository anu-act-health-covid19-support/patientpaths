import numpy as np

def step6(moc, num_days, num_strata, mld_new_Clinic, mld_rpt_Clinic, mld_new_ED, mld_rpt_ED, mld_new_GP, mld_rpt_GP, avail_clinic, avail_ed, excess_ed_sev, excess_clinic_sev):
#input_output: avail_clinic, avail_ed

	#declare locals
	mld_GP = np.zeros([1])
	mld_ED = np.zeros([1])
	mld_Clinic = np.zeros([1])

	#declare outputs
	admit_gp = np.zeros([num_strata])
	avail_gp = moc.cap_GP
	excess_gp = np.zeros([num_strata])
	admit_clinic_mld = np.zeros([num_strata])
	admit_ed_mld = np.zeros([num_strata])
	excess_ed_mld = np.zeros([num_strata])
	excess_clinic_mld = np.zeros([num_strata])

	#%
	#% Step 6: Out-patient presentations and treatment.
	#%
	for s in range(num_strata):

		#% Calculate mild clinic consultations.
		mld_Clinic = mld_new_Clinic[s] + mld_rpt_Clinic[s]
		admit_clinic_mld[s] = np.minimum(avail_clinic, mld_Clinic)
		excess_clinic_mld[s] = mld_Clinic - admit_clinic_mld[s]
		avail_clinic = avail_clinic - admit_clinic_mld[s]

		#% Calculate mild ED consultations.
		mld_ED = mld_new_ED[s] + mld_rpt_ED[s]
		admit_ed_mld[s] = np.minimum(avail_ed, mld_ED)
		excess_ed_mld[s] = mld_ED - admit_ed_mld[s]
		avail_ed = avail_ed - admit_ed_mld[s]

		#% Calculate mild GP consultations.
		mld_GP = mld_new_GP[s] + mld_rpt_GP[s]
		#% Assume that excess ED and Clinic consultations present to GPs.
		mld_GP = mld_GP + excess_clinic_mld[s] + excess_clinic_sev[s] + excess_ed_mld[s] + excess_ed_sev[s]
		admit_gp[s] = np.minimum(avail_gp, mld_GP)
		excess_gp[s] = excess_gp[s] + (mld_GP - admit_gp[s])
		avail_gp = avail_gp - admit_gp[s]

	return admit_gp, avail_gp, excess_gp, admit_clinic_mld, avail_clinic, admit_ed_mld, avail_ed, excess_ed_mld, excess_clinic_mld

