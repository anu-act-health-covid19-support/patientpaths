A = '''mld_new_GP = di_mild [label=mild_to_GP]
mld_new_ED = di_mild [label=mild_to_ED]
mld_new_Clinic = di_mild [label=mild_to_Clinic]
mld_rpt_ED = yest_mld_new_GP [label=mild_GP_rpt_ED]
mld_rpt_Clinic = yest_mld_new_GP [label=mild_GP_rpt_Clinic]
mld_rpt_GP = yest_mld_new_ED [label=mild_ED_rpt_GP]
mld_rpt_GP = yest_mld_rpt_ED [label=mild_ED_rpt_GP]
mld_rpt_GP = yest_mld_new_Clinic [label=mild_Clinic_rpt_GP]
mld_rpt_GP = yest_mld_rpt_Clinic [label=mild_Clinic_rpt_GP]
sev_new_early = di_sev [label=sev_frac_early]
sev_new_early_GP = sev_new_early [label=sev_early_to_GP]
sev_new_early_ED = sev_new_early [label=sev_early_to_ED]
sev_new_early_Clinic = sev_new_early [label=sev_early_to_Clinic]
sev_new_late = di_sev [label=sev_frac_late]
sev_new_late_ED = sev_new_late [label=sev_late_to_ED]
sev_new_late_Clinic = sev_new_late [label=sev_late_to_Clinic]
yest_sev_rpt_ED = sev_rpt_tmrw [label=sev_late_to_ED]
yest_sev_rpt_Clinic = sev_rpt_tmrw [label=sev_late_to_Clinic]
sev_rpt_tmrw = sev_new_early
sev_rpt_late_ED = yest_sev_rpt_ED
sev_rpt_late_Clinic = yest_sev_rpt_Clinic
yest_mld_new_GP = mld_new_GP
yest_mld_new_ED = mld_new_ED
yest_mld_new_Clinic = mld_new_Clinic
yest_mld_rpt_ED = mld_rpt_ED
yest_mld_rpt_Clinic = mld_rpt_Clinic'''
for l in A.split('\n'):
	a = l.split(' = ')
	b = a[1].split(' ')
	if len(b)==1:
		print(" -> ".join([b[0],a[0]])+ ";")
	elif len(b)==2:
		print(" -> ".join([b[0],a[0]]) + " " + b[1]+ ";")
	else:
		print("rawr")
