import numpy as np

def step6(moc, num_days, num_strata, mld_new_Clinic, mld_rpt_Clinic, mld_new_ED, mld_rpt_ED, mld_new_GP, mld_rpt_GP, admit_clinic, avail_clinic, admit_ed, avail_ed, excess_ed, excess_clinic):
#input: mld_new_Clinic, mld_rpt_Clinic, mld_new_ED, mld_rpt_ED, mld_new_GP, mld_rpt_GP
#local: mld_Clinic, mld_ED, mld_GP
#output: admit_gp, avail_gp, excess_gp
#input_output: admit_clinic, avail_clinic, admit_ed, avail_ed, excess_ed, excess_clinic

	#declare locals
	mld_GP = np.zeros([1])
	mld_ED = np.zeros([1])
	mld_Clinic = np.zeros([1])

	#declare outputs
	admit_gp = np.zeros([num_strata])
	avail_gp = moc.cap_GP
	excess_gp = np.zeros([num_strata])

	#%
	#% Step 6: Out-patient presentations and treatment.
	#%
	for s in range(num_strata):

		#% Calculate mild clinic consultations.
		mld_Clinic = mld_new_Clinic[s] + mld_rpt_Clinic[s]
		admit_clinic[s] = np.minimum(avail_clinic, mld_Clinic)
		excess_clinic[s] = excess_clinic[s] + (mld_Clinic - admit_clinic[s])
		avail_clinic = avail_clinic - admit_clinic[s]

		#% Calculate mild ED consultations.
		mld_ED = mld_new_ED[s] + mld_rpt_ED[s]
		#% NOTE: here we overwrite ED presentations that lead to admissions,
		#% which is stored in admit_ed(:, s, d), so we need to record its
		#% current value before proceeding.
		ed_to_ward = admit_ed[s]
		admit_ed[s] = np.minimum(avail_ed, mld_ED)
		excess_ed[s] = excess_ed[s] + (mld_ED - admit_ed[s])
		avail_ed = avail_ed - admit_ed[s]
		#% NOTE: add the ED presentations that lead to admissions, and remove
		#% the temporary variable.
		admit_ed[s] = admit_ed[s] + ed_to_ward

		#% Calculate mild GP consultations.
		mld_GP = mld_new_GP[s] + mld_rpt_GP[s]
		#% Assume that excess ED and Clinic consultations present to GPs.
		mld_GP = mld_GP + excess_clinic[s] + excess_ed[s]
		admit_gp[s] = np.minimum(avail_gp, mld_GP)
		excess_gp[s] = excess_gp[s] + (mld_GP - admit_gp[s])
		avail_gp = avail_gp - admit_gp[s]

	return admit_gp, avail_gp, excess_gp, admit_clinic, avail_clinic, admit_ed, avail_ed, excess_ed, excess_clinic

