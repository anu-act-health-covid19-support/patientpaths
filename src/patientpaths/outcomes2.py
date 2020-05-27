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

from Presentation_Matrix import Presentation_Matrix

def outcomes_for_moc(moc, di_mild, di_sev, risk):

	#% Define dimensions that affect variable sizes.
	num_strata = di_mild.shape[0]
	num_days = di_mild.shape[1]
	#% Yesterday's (fractional) ward availability.
	frac_ward_avail = 1

	pres = Presentation_Matrix()
	pres.set_default(np.zeros([num_strata]))
	pres.transition("di_mild","mld_new_GP",moc.mild_to_GP)
	pres.transition("di_mild","mld_new_ED",moc.mild_to_ED)
	pres.transition("di_mild","mld_new_Clinic",moc.mild_to_Clinic)
	pres.transition("mld_new_GP","mld_rpt_ED",moc.mild_GP_rpt_ED)
	pres.transition("mld_new_GP","mld_rpt_Clinic",moc.mild_GP_rpt_Clinic)
	pres.transition("mld_new_ED","mld_rpt_GP",moc.mild_ED_rpt_GP)
	pres.transition("mld_rpt_ED","mld_rpt_GP",moc.mild_ED_rpt_GP)
	pres.transition("mld_new_Clinic","mld_rpt_GP",moc.mild_Clinic_rpt_GP)
	pres.transition("mld_rpt_Clinic","mld_rpt_GP",moc.mild_Clinic_rpt_GP)
	pres.transition("di_sev","sev_new_early",moc.sev_frac_early)
	pres.transition("di_sev","sev_new_early_GP",moc.sev_frac_early * moc.sev_early_to_GP)
	pres.transition("di_sev","sev_new_early_ED",moc.sev_frac_early * moc.sev_early_to_ED)
	pres.transition("di_sev","sev_new_early_Clinic",moc.sev_frac_early * moc.sev_early_to_Clinic)
	pres.transition("di_sev","sev_new_late",moc.sev_frac_late)
	pres.transition("di_sev","sev_new_late_ED",moc.sev_frac_late * moc.sev_late_to_ED)
	pres.transition("di_sev","sev_new_late_Clinic",moc.sev_frac_late * moc.sev_late_to_Clinic)
	pres.transition("sev_new_early","sev_rpt_late_ED",moc.sev_late_to_ED)
	pres.transition("sev_new_early","yest_sev_rpt_Clinic",moc.sev_late_to_Clinic)

	for d in range(num_days):
		pres['di_mild'] = di_mild[:, d]
		pres['di_sev'] = di_sev[:, d]
		pres.apply()

		want_beds, avail_clinic, admit_clinic_sev, excess_clinic, admit_ed_sev, excess_ed_sev, avail_ed = step23(moc,num_strata,pres['sev_rpt_late_Clinic'], pres['sev_new_late_Clinic'], pres['sev_rpt_late_ED'], pres['sev_new_late_ED'], frac_ward_avail)

		try_ward, req_ward, admit_icu, avail_icu, excess_icu, deaths = step4(d, moc, num_days, num_strata, want_beds, risk)

		admit_ward, avail_ward, excess_ward = step5(d, moc, num_days, num_strata, try_ward)

		#% Update the ward availability, which affects tomorrow's ED capacity.
		frac_ward_avail = avail_ward[d] / moc.cap_Ward

		admit_gp, avail_gp, excess_gp, admit_clinic_mld, avail_clinic, admit_ed_mld, avail_ed, excess_ed_mld, excess_clinic = step6(moc, num_days, num_strata, pres['mld_new_Clinic'], pres['mld_rpt_Clinic'], pres['mld_new_ED'], pres['mld_rpt_ED'], pres['mld_new_GP'], pres['mld_rpt_GP'], avail_clinic, avail_ed, excess_ed_sev, excess_clinic)

	out = {};
	#additional outputs of unprocessed data
	out['deaths'] = deaths;

	out['excess_icu'] = excess_icu;
	out['excess_ward'] = excess_ward;
	out['excess_ed_sev'] = excess_ed_sev;
	out['excess_ed_mld'] = excess_ed_mld;
	out['excess_clinic'] = excess_clinic;
	out['excess_gp'] = excess_gp;

	out['admit_icu'] = admit_icu;
	out['admit_ward'] = admit_ward;
	out['admit_ed_sev'] = admit_ed_sev;
	out['admit_ed_mld'] = admit_ed_mld;
	out['admit_clinic_sev'] = admit_clinic_sev;
	out['admit_clinic_mld'] = admit_clinic_mld;
	out['admit_gp'] = admit_gp;

	out['avail_icu'] = avail_icu;
	out['avail_ward'] = avail_ward;
	out['avail_ed'] = avail_ed;
	out['avail_clinic'] = avail_clinic;
	out['avail_gp'] = avail_gp;

	return out



