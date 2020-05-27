# OUTCOMES_FOR_MOC(moc, di_mild, di_sev, risk, frac_sev, ppe_stop)
#
# Calculate the population outcomes and healthcare impact of an nCoV scenario
# for the provided model of care 'moc'. Other parameters are:
#
# - 'di_mild': the daily incidence of mild cases, who will present but will
#   not require hospitalisation; it should have dimensions [S P D] for S
#   simulations, P population strata, and D days.
# - 'di_sev': the daily incidence of severe cases, who will require
#   hospitalisation; it should have the same dimensions as 'di_mild' (above).
# - 'risk': a [P 1] column vector that has values > 1 for population strata
#   that have increased risks of ICU admission and death.
#See also model_of_care, ppe_usage
import numpy as np
import pdb

from step23 import step23
from step4 import step4
from step5 import step5
from step6 import step6

def outcomes_for_moc(moc, di_mild, di_sev, risk):

	#% Define dimensions that affect variable sizes.
	num_strata = di_mild.shape[0]
	num_days = di_mild.shape[1]


	#% Mild presentations in each setting.
	mld_new_GP = np.zeros([num_strata])
	mld_new_ED = np.zeros([num_strata])
	mld_new_Clinic = np.zeros([num_strata])
	mld_rpt_GP = np.zeros([num_strata])
	mld_rpt_ED = np.zeros([num_strata])
	mld_rpt_Clinic = np.zeros([num_strata])

	#% Severe presentations in each setting.
	sev_new_early = np.zeros([num_strata])
	sev_new_early_GP = np.zeros([num_strata])
	sev_new_early_ED = np.zeros([num_strata])
	sev_new_early_Clinic = np.zeros([num_strata])
	#% Daily incidence of severe cases that present late in each setting.
	sev_new_late = np.zeros([num_strata])
	sev_new_late_ED = np.zeros([num_strata])
	sev_new_late_Clinic = np.zeros([num_strata])
	#% Daily incidence of repeat severe cases that present in each setting.
	sev_rpt_late_ED = np.zeros([num_strata])
	sev_rpt_late_Clinic = np.zeros([num_strata])

	#% Daily incidence of severe cases that present early; they will present
	#% with more severe disease and require hospitalisation.
	sev_rpt_tmrw = np.zeros([num_strata])

	#% The daily demand for hospitalisation.
	#% NOTE: this is the presenting severe proportion, ignoring "early" severe
	#% cases and counting "late" repeat presentations.
	#% Multiply this by frac_ward_to_ICU to determine the ward/ICU split.
	req_hosp = np.zeros(di_sev.shape)

	#% Yesterday's (fractional) ward availability.
	frac_ward_avail = 1

	#% Yesterday's presentations, used to calculate repeat presentation.
	yest_mld_new_GP = np.zeros([num_strata])
	yest_mld_new_ED = np.zeros([num_strata])
	yest_mld_new_Clinic = np.zeros([num_strata])
	yest_mld_rpt_ED = np.zeros([num_strata])
	yest_mld_rpt_Clinic = np.zeros([num_strata])
	#% Early severe presentations that will still require hospitalisation.
	yest_sev_rpt_ED = np.zeros([num_strata])
	yest_sev_rpt_Clinic = np.zeros([num_strata])

	for d in range(num_days):

		#%
		#% Step 1: Daily presentations in each setting.
		#%

		#% Daily incidence of new mild cases in each setting.
		mld_new_GP[:] = moc.mild_to_GP * di_mild[:, d]
		mld_new_ED[:] = moc.mild_to_ED * di_mild[:, d]
		mld_new_Clinic[:] = moc.mild_to_Clinic * di_mild[:, d]
		#% Daily incidence of repeat mild cases in each setting.
		mld_rpt_ED[:] = moc.mild_GP_rpt_ED * yest_mld_new_GP
		mld_rpt_Clinic[:] = moc.mild_GP_rpt_Clinic * yest_mld_new_GP
		mld_rpt_GP[:] = moc.mild_ED_rpt_GP * (yest_mld_new_ED + yest_mld_rpt_ED) + moc.mild_Clinic_rpt_GP * (yest_mld_new_Clinic + yest_mld_rpt_Clinic)
		#% Record these presentations for use tomorrow.
		yest_mld_new_GP[:] = mld_new_GP
		yest_mld_new_ED[:] = mld_new_ED
		yest_mld_new_Clinic[:] = mld_new_Clinic
		yest_mld_rpt_ED[:] = mld_rpt_ED
		yest_mld_rpt_Clinic[:] = mld_rpt_Clinic

		#% Daily incidence of severe cases that present early in each setting.
		sev_new_early[:] = moc.sev_frac_early * di_sev[:, d]
		sev_new_early_GP[:] = moc.sev_early_to_GP * sev_new_early
		sev_new_early_ED[:] = moc.sev_early_to_ED * sev_new_early
		sev_new_early_Clinic[:] = moc.sev_early_to_Clinic * sev_new_early
		#% Daily incidence of severe cases that present late in each setting.
		sev_new_late[:] = moc.sev_frac_late * di_sev[:, d]
		sev_new_late_ED[:] = moc.sev_late_to_ED * sev_new_late
		sev_new_late_Clinic[:] = moc.sev_late_to_Clinic * sev_new_late
		#% Daily incidence of repeat severe cases that require hospitalisation.
		sev_rpt_late_ED[:] = yest_sev_rpt_ED
		sev_rpt_late_Clinic[:] = yest_sev_rpt_Clinic

		#%
		#% Step 1a: Determine what number of severe cases that present early will
		#%          require hospitalisation **tomorrow**.
		#%

		#% Daily incidence of repeat severe cases in EDs and Clinics.
		sev_rpt_tmrw[:] = sev_new_early
		yest_sev_rpt_ED[:] = moc.sev_late_to_ED * sev_rpt_tmrw
		yest_sev_rpt_Clinic[:] = moc.sev_late_to_Clinic * sev_rpt_tmrw

		#% Daily incidence of ED and Clinic cases that require hospitalisation.
		req_hosp[:, d] = sev_new_late + sev_rpt_late_ED + sev_rpt_late_Clinic

		want_beds, avail_clinic, admit_clinic, excess_clinic, admit_ed, excess_ed, avail_ed = step23(moc,num_strata,sev_rpt_late_Clinic, sev_new_late_Clinic, sev_rpt_late_ED, sev_new_late_ED, frac_ward_avail)

		try_ward, req_ward, admit_icu, avail_icu, excess_icu, deaths = step4(d, moc, num_days, num_strata, want_beds, risk)

		admit_ward, avail_ward, excess_ward = step5(d, moc, num_days, num_strata, try_ward)

		#% Update the ward availability, which affects tomorrow's ED capacity.
		frac_ward_avail = avail_ward[d] / moc.cap_Ward

		admit_gp, avail_gp, excess_gp, admit_clinic, avail_clinic, admit_ed, avail_ed, excess_ed, excess_clinic = step6(moc, num_days, num_strata, mld_new_Clinic, mld_rpt_Clinic, mld_new_ED, mld_rpt_ED, mld_new_GP, mld_rpt_GP, admit_clinic, avail_clinic, admit_ed, avail_ed, excess_ed, excess_clinic)

	out = {};
	#additional outputs of unprocessed data
	out['deaths'] = deaths;

	out['excess_icu'] = excess_icu;
	out['excess_ward'] = excess_ward;
	out['excess_ed'] = excess_ed;
	out['excess_clinic'] = excess_clinic;
	out['excess_gp'] = excess_gp;

	out['admit_icu'] = admit_icu;
	out['admit_ward'] = admit_ward;
	out['admit_ed'] = admit_ed;
	out['admit_clinic'] = admit_clinic;
	out['admit_gp'] = admit_gp;

	out['avail_icu'] = avail_icu;
	out['avail_ward'] = avail_ward;
	out['avail_ed'] = avail_ed;
	out['avail_clinic'] = avail_clinic;
	out['avail_gp'] = avail_gp;

	return out



