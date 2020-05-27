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
def outcomes_for_moc(moc, di_mild, di_sev, risk):

  #% Define dimensions that affect variable sizes.
  num_strata = di_mild.shape[0]
  num_days = di_mild.shape[1]

  #% Identify cohorts with increased risk of ICU admission and death.
  frac_ward_to_ICU = moc.ward_to_ICU * np.ones([num_strata, 1])
  frac_ward_to_ICU[risk > 1] = moc.ward_to_ICU_highrisk
  frac_ICU_to_death = moc.ICU_to_death * np.ones([num_strata, 1])
  frac_ICU_to_death[risk > 1] = moc.ICU_to_death_highrisk
  #% Halve the survival rate for cases that require ICU admission but cannot
  #% be admitted into an ICU.
  frac_noICU_to_death = 1 - 0.5 * (1 - frac_ICU_to_death)

  #% Mild presentations in each setting.
  mld_new_GP = np.zeros([num_strata])
  mld_new_ED = np.zeros([num_strata])
  mld_new_Clinic = np.zeros([num_strata])
  mld_rpt_GP = np.zeros([num_strata])
  mld_rpt_ED = np.zeros([num_strata])
  mld_rpt_Clinic = np.zeros([num_strata])
  mld_GP = np.zeros([1])
  mld_ED = np.zeros([1])
  mld_Clinic = np.zeros([1])

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

  req_hosp_via_Clinic = np.zeros([1])
  req_hosp_via_ED = np.zeros([1])
  clinic_cs = np.zeros([1])
  ed_cs = np.zeros([1])
  cap_treat = np.zeros([1])

  #% Yesterday's (fractional) ward availability.
  frac_ward_avail = np.ones([num_days + 1])

  #% The fractional ED availability.
  frac_ed_avail = np.zeros([1])
  numer = np.zeros([1])

  #% The daily demand for bed occupancy for each strata.
  req_ward = np.zeros(di_sev.shape)
  req_icu = np.zeros(di_sev.shape)

  #% Baseline daily capacities.
  avail_icu = np.tile(moc.cap_ICU, [num_days])
  avail_ward = np.tile(moc.cap_Ward, [num_days])
  avail_ed = np.tile(moc.cap_ED, [num_days])
  avail_clinic = np.tile(moc.cap_Clinic, [num_days])
  avail_gp = np.tile(moc.cap_GP, [num_days])

  #% Record the baseline capacities, in addition to remaining capacities.
  cap_icu = avail_icu
  cap_ward = avail_ward
  cap_ed = avail_ed
  cap_clinic = avail_clinic
  cap_gp = avail_gp

  #% Daily admissions / consultations.
  admit_icu = np.zeros(di_sev.shape)
  admit_ward = np.zeros(di_sev.shape)
  admit_ed = np.zeros(di_sev.shape)
  admit_clinic = np.zeros(di_sev.shape)
  admit_gp = np.zeros(di_sev.shape)

  #% Daily excess admissions / consultations.
  excess_icu = np.zeros(di_sev.shape)
  excess_ward = np.zeros(di_sev.shape)
  excess_ed = np.zeros(di_sev.shape)
  excess_clinic = np.zeros(di_sev.shape)
  excess_gp = np.zeros(di_sev.shape)

  #% Daily deaths.
  deaths = np.zeros(di_sev.shape)

  #% Daily number of cases we want to admit to hospital.
  want_beds = np.zeros([num_strata])
  #% Daily number of cases we want to admit to wards.
  try_ward = np.zeros([num_strata])

  #% Daily demand for hospital admission and for ICU beds.
  cases = np.zeros([1])
  icu_cases = np.zeros([1])

  #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  #%%
  #%% Daily loop of presentations.
  #%%
  #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

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
    mld_new_GP[:] = np.tile(moc.mild_to_GP, [1, num_strata]) * di_mild[:, d]
    mld_new_ED[:] = np.tile(moc.mild_to_ED, [1, num_strata]) * di_mild[:, d]
    mld_new_Clinic[:] = np.tile(moc.mild_to_Clinic, [1, num_strata]) * di_mild[:, d]
    #% Daily incidence of repeat mild cases in each setting.
    mld_rpt_ED[:] = np.tile(moc.mild_GP_rpt_ED, [1, num_strata]) * yest_mld_new_GP
    mld_rpt_Clinic[:] = np.tile(moc.mild_GP_rpt_Clinic, [1, num_strata]) * yest_mld_new_GP
    mld_rpt_GP[:] = np.tile(moc.mild_ED_rpt_GP, [1, num_strata]) * (yest_mld_new_ED + yest_mld_rpt_ED) + np.tile(moc.mild_Clinic_rpt_GP, [1, num_strata]) * (yest_mld_new_Clinic + yest_mld_rpt_Clinic)
    #% Record these presentations for use tomorrow.
    yest_mld_new_GP[:] = mld_new_GP
    yest_mld_new_ED[:] = mld_new_ED
    yest_mld_new_Clinic[:] = mld_new_Clinic
    yest_mld_rpt_ED[:] = mld_rpt_ED
    yest_mld_rpt_Clinic[:] = mld_rpt_Clinic

    #% Daily incidence of severe cases that present early in each setting.
    sev_new_early[:] = np.tile(moc.sev_frac_early, [1, num_strata]) * di_sev[:, d]
    sev_new_early_GP[:] = np.tile(moc.sev_early_to_GP, [1, num_strata]) * sev_new_early
    sev_new_early_ED[:] = np.tile(moc.sev_early_to_ED, [1, num_strata]) * sev_new_early
    sev_new_early_Clinic[:] = np.tile(moc.sev_early_to_Clinic, [1, num_strata]) * sev_new_early
    #% Daily incidence of severe cases that present late in each setting.
    sev_new_late[:] = np.tile(moc.sev_frac_late, [1, num_strata]) * di_sev[:, d]
    sev_new_late_ED[:] = np.tile(moc.sev_late_to_ED, [1, num_strata]) * sev_new_late
    sev_new_late_Clinic[:] = np.tile(moc.sev_late_to_Clinic, [1, num_strata]) * sev_new_late
    #% Daily incidence of repeat severe cases that require hospitalisation.
    sev_rpt_late_ED[:] = yest_sev_rpt_ED
    sev_rpt_late_Clinic[:] = yest_sev_rpt_Clinic

    #%
    #% Step 1a: Determine what number of severe cases that present early will
    #%          require hospitalisation **tomorrow**.
    #%

    #% Daily incidence of repeat severe cases in EDs and Clinics.
    sev_rpt_tmrw[:] = sev_new_early
    yest_sev_rpt_ED[:] = np.tile(moc.sev_late_to_ED, [1, num_strata]) * sev_rpt_tmrw
    yest_sev_rpt_Clinic[:] = np.tile(moc.sev_late_to_Clinic, [1, num_strata]) * sev_rpt_tmrw

    #% Daily incidence of ED and Clinic cases that require hospitalisation.
    req_hosp[:, d] = sev_new_late + sev_rpt_late_ED + sev_rpt_late_Clinic

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
    numer = frac_ward_avail[d] / moc.lm_ED_cap_W0
    frac_ed_avail = moc.lm_ED_cap_E1 + (1 - moc.lm_ED_cap_E1) * numer
    frac_ed_avail = np.minimum(frac_ed_avail, 1)
    avail_ed[d] = avail_ed[d] * frac_ed_avail
    #% Record the actual ED consultation capacity.
    cap_ed[d] = avail_ed[d]

    #%
    #% Step 3: Hospital admissions -- how many can we admit?
    #%
    want_beds[:] = 0
    for s in range(num_strata):
      #% Clinic admissions.
      req_hosp_via_Clinic = sev_rpt_late_Clinic[s] + sev_new_late_Clinic[s]

      clinic_cs = np.minimum(req_hosp_via_Clinic, avail_clinic[d])
      avail_clinic[d] = avail_clinic[d] - clinic_cs
      want_beds[s] = clinic_cs
      admit_clinic[s, d] = clinic_cs
      excess_clinic[s, d] = req_hosp_via_Clinic - clinic_cs

      #% ED admissions.
      req_hosp_via_ED = sev_rpt_late_ED[s] + sev_new_late_ED[s]
      ed_cs = np.minimum(req_hosp_via_ED, avail_ed[d])
      avail_ed[d] = avail_ed[d] - ed_cs
      want_beds[s] = want_beds[s] + ed_cs
      #% NOTE: here we record ED presentations that lead to admissions.
      #% Mild ED presentations are accounted for later on.
      admit_ed[s, d] = ed_cs
      excess_ed[s, d] = req_hosp_via_ED - ed_cs

    #%
    #% Step 4: Hospital admissions -- how many can we put in ICU beds?
    #%
    try_ward[:] = 0
    for s in range(num_strata):
      #% Determine who needs ward beds and ICU beds.
      cases = want_beds[s]
      req_icu[s, d] = cases * frac_ward_to_ICU[s]
      try_ward[s] = cases - req_icu[s, d]
      req_ward[s, d] = try_ward[s]

      #% Determine who gets ICU beds.
      admit_icu[s, d] = min(avail_icu[d], req_icu[s, d])
      excess_icu[s, d] = req_icu[s, d] - admit_icu[s, d]
      try_ward[s] = try_ward[s] + excess_icu[s, d]

      #% Schedule patients to occupy beds for multiple days.
      x = np.minimum(d + moc.LoS_ICU - 1, num_days);
      avail_icu[d:x] = avail_icu[d:x] - admit_icu[s, d] #Originally: bsxfun(@minus, avail_icu[:, d:x], admit_icu[:, s, d])
      avail_icu[d:x] = np.max(avail_icu[d:x], 0)

      #% Calculate deaths, on the assumption that not getting an ICU
      #% bed halves the survival rate.
      deaths[s, d] = np.squeeze(admit_icu[s, d]) * frac_ICU_to_death[s] + np.squeeze(excess_icu[s, d]) * frac_noICU_to_death[s]

    #%
    #% Step 5: Hospital admissions -- how many can we put in ward beds?
    #%
    for s in range(num_strata):
      #% Determine who gets ward beds (second priority).
      #% Note: excess cases have *already* presented to an ED or Clinic, so
      #% we're done with them!
      admit_ward[s, d] = np.minimum(avail_ward[d], try_ward[s])
      excess_ward[s, d] = try_ward[s] - admit_ward[s, d]
      #% Schedule patients to occupy beds for multiple days.
      x = np.minimum(d + moc.LoS_Ward - 1, num_days)
      avail_ward[d:x] = avail_ward[d:x] - admit_ward[s, d] #Originally: bsxfun(@minus, avail_ward[:, d:x], admit_ward[:, s, d])
      avail_ward[d:x] = np.max(avail_ward[d:x], 0)

    #% Update the ward availability, which affects tomorrow's ED capacity.
    frac_ward_avail[d + 1] = avail_ward[d] / moc.cap_Ward

    #%
    #% Step 6: Out-patient presentations and treatment.
    #%
    for s in range(num_strata):
      #% Calculate mild clinic consultations.
      mld_Clinic[:] = mld_new_Clinic[:, s] + mld_rpt_Clinic[:, s]
      admit_clinic[:, s, d] = np.minimum(avail_clinic[:, d], mld_Clinic)
      excess_clinic[:, s, d] = excess_clinic[:, s, d] + (mld_Clinic - admit_clinic[:, s, d])
      avail_clinic[:, d] = avail_clinic[:, d] - admit_clinic[:, s, d]

      #% Calculate mild ED consultations.
      mld_ED[:] = mld_new_ED[:, s] + mld_rpt_ED[:, s]
      #% NOTE: here we overwrite ED presentations that lead to admissions,
      #% which is stored in admit_ed(:, s, d), so we need to record its
      #% current value before proceeding.
      ed_to_ward = admit_ed[:, s, d]
      admit_ed[:, s, d] = np.minimum(avail_ed[:, d], mld_ED)
      excess_ed[:, s, d] = excess_ed[:, s, d] + (mld_ED - admit_ed[:, s, d])
      avail_ed[:, d] = avail_ed[:, d] - admit_ed[:, s, d]
      #% NOTE: add the ED presentations that lead to admissions, and remove
      #% the temporary variable.
      admit_ed[:, s, d] = admit_ed[:, s, d] + ed_to_ward
      del ed_to_ward

      #% Calculate mild GP consultations.
      mld_GP[:] = mld_new_GP[:, s] + mld_rpt_GP[:, s]
      #% Assume that excess ED and Clinic consultations present to GPs.
      mld_GP[:] = mld_GP + excess_clinic[:, s, d] + excess_ed[:, s, d]
      admit_gp[:, s, d] = np.minimum(avail_gp[:, d], mld_GP)
      excess_gp[:, s, d] = excess_gp[:, s, d] + (mld_GP - admit_gp[:, s, d])
      avail_gp[:, d] = avail_gp[:, d] - admit_gp[:, s, d]


  #% NOTE: now that we've calculated the daily number of severe cases that are
  #% presenting (but not presenting early with mild symptoms) we can calculate
  #% the true demand for ward and ICU beds, as opposed to req_ward and req_icu
  #% that reflect the bed demand amongst *triaged cases*.
  true_req_icu = []
  for i in range(req_hosp.shape[0]):
    true_req_icu.append((frac_ward_to_ICU * req_hosp[i]))
  true_req_icu = np.array(true_req_icu)
  true_req_ward = req_hosp - true_req_icu
  #% Calculate net daily demand (i.e., sum over all strata).
  daily_true_req_icu = np.squeeze(np.sum(true_req_icu, 1))
  daily_true_req_ward = np.squeeze(np.sum(true_req_ward, 1))
  #% Identify the peak in net (true) daily demand.
  peak_true_req_icu = np.max(daily_true_req_icu, 0)
  peak_true_req_ward = np.max(daily_true_req_ward, 0)

  #% Similarly, calculate the peak in net (true) daily demand for EDs and GPs
  true_req_ed = admit_ed + excess_ed
  true_req_gp = admit_gp + excess_gp
  daily_true_req_ed = np.squeeze(np.sum(true_req_ed, 1))
  daily_true_req_gp = np.squeeze(np.sum(true_req_gp, 1))
  peak_true_req_ed = np.max(daily_true_req_ed, 0)
  peak_true_req_gp = np.max(daily_true_req_gp, 0)


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





