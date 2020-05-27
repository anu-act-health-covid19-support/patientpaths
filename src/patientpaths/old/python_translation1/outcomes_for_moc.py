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
# - 'frac_sev': a [S 1] column vector that defines the proportion of clinical
#   presentations that are severe cases; you may choose to calculate this from
#   the total number of mild and severe presentations for each simulation.
# - 'ppe_stop': a [S 1] column vector that defines when to stop using PPE for
#   each simulation; you may want to define this as the time at which a
#   certain proportion of clinical presentations have occurred (e.g., 99%).
#
#See also model_of_care, ppe_usage
import numpy as np
import pdb
def outcomes_for_moc(moc, di_mild, di_sev, risk, frac_sev, ppe_stop):
  #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  #%%
  #%% Allocate matrices for daily demand, capacity, and outcomes.
  #%%
  #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

  if di_mild.shape != di_sev.shape:
    raise Exception('Daily mild and severe presentations have different sizes')

  #% Define dimensions that affect variable sizes.
  num_sims = di_mild.shape[0]
  num_strata = di_mild.shape[1]
  num_days = di_mild.shape[2]
  num_settings = 5

  #% Convenient shorthand for PPE usage rates (used in Step 7).
  PPE = moc.ppe_usage

  frac_presns_severe = frac_sev

  #% Identify cohorts with increased risk of ICU admission and death.
  frac_ward_to_ICU = moc.ward_to_ICU * np.ones([num_strata, 1])
  frac_ward_to_ICU[risk > 1] = moc.ward_to_ICU_highrisk
  frac_ICU_to_death = moc.ICU_to_death * np.ones([num_strata, 1])
  frac_ICU_to_death[risk > 1] = moc.ICU_to_death_highrisk
  #% Halve the survival rate for cases that require ICU admission but cannot
  #% be admitted into an ICU.
  frac_noICU_to_death = 1 - 0.5 * (1 - frac_ICU_to_death)

  #% Mild presentations in each setting.
  mld_new_GP = np.zeros([num_sims, num_strata])
  mld_new_ED = np.zeros([num_sims, num_strata])
  mld_new_Clinic = np.zeros([num_sims, num_strata])
  mld_rpt_GP = np.zeros([num_sims, num_strata])
  mld_rpt_ED = np.zeros([num_sims, num_strata])
  mld_rpt_Clinic = np.zeros([num_sims, num_strata])
  mld_GP = np.zeros([num_sims, 1])
  mld_ED = np.zeros([num_sims, 1])
  mld_Clinic = np.zeros([num_sims, 1])

  #% Severe presentations in each setting.
  sev_new_early = np.zeros([num_sims, num_strata])
  sev_new_early_GP = np.zeros([num_sims, num_strata])
  sev_new_early_ED = np.zeros([num_sims, num_strata])
  sev_new_early_Clinic = np.zeros([num_sims, num_strata])
  #% Daily incidence of severe cases that present late in each setting.
  sev_new_late = np.zeros([num_sims, num_strata])
  sev_new_late_ED = np.zeros([num_sims, num_strata])
  sev_new_late_Clinic = np.zeros([num_sims, num_strata])
  #% Daily incidence of repeat severe cases that present in each setting.
  sev_rpt_late_ED = np.zeros([num_sims, num_strata])
  sev_rpt_late_Clinic = np.zeros([num_sims, num_strata])

  #% Daily incidence of severe cases that present early; they will present
  #% with more severe disease and require hospitalisation.
  sev_rpt_tmrw = np.zeros([num_sims, num_strata])

  #% The daily demand for hospitalisation.
  #% NOTE: this is the presenting severe proportion, ignoring "early" severe
  #% cases and counting "late" repeat presentations.
  #% Multiply this by frac_ward_to_ICU to determine the ward/ICU split.
  req_hosp = np.zeros(di_sev.shape)

  req_hosp_via_Clinic = np.zeros([num_sims, 1])
  req_hosp_via_ED = np.zeros([num_sims, 1])
  clinic_cs = np.zeros([num_sims, 1])
  ed_cs = np.zeros([num_sims, 1])
  cap_treat = np.zeros([num_sims, 1])

  #% Yesterday's (fractional) ward availability.
  frac_ward_avail = np.ones([num_sims, num_days + 1])

  #% The fractional ED availability.
  frac_ed_avail = np.zeros([num_sims, 1])
  numer = np.zeros([num_sims, 1])

  #% The daily demand for bed occupancy for each strata.
  req_ward = np.zeros(di_sev.shape)
  req_icu = np.zeros(di_sev.shape)

  #% Baseline daily capacities.
  avail_icu = np.tile(moc.cap_ICU, [num_sims, num_days])
  avail_ward = np.tile(moc.cap_Ward, [num_sims, num_days])
  avail_ed = np.tile(moc.cap_ED, [num_sims, num_days])
  avail_clinic = np.tile(moc.cap_Clinic, [num_sims, num_days])
  avail_gp = np.tile(moc.cap_GP, [num_sims, num_days])

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
  want_beds = np.zeros([num_sims, num_strata])
  #% Daily number of cases we want to admit to wards.
  try_ward = np.zeros([num_sims, num_strata])

  #% Daily PPE consumption.
  ppe_bg = np.zeros([num_sims, num_days])
  ppe_case = np.zeros([num_sims, num_days])
  #% Daily PPE consumption in each setting.
  ppe_icu = np.zeros([num_sims, num_days])
  ppe_ward = np.zeros([num_sims, num_days])
  ppe_ed = np.zeros([num_sims, num_days])
  ppe_gp = np.zeros([num_sims, num_days])
  ppe_clinic = np.zeros([num_sims, num_days])
  #% Daily P2 mask consumption.
  p2_case = np.zeros([num_sims, num_days])
  #% Daily P2 mask consumption in each setting.
  p2_icu = np.zeros([num_sims, num_days])
  p2_ward = np.zeros([num_sims, num_days])
  p2_ed = np.zeros([num_sims, num_days])
  p2_gp = np.zeros([num_sims, num_days])
  p2_clinic = np.zeros([num_sims, num_days])

  #% Stop PPE consumption when we reach 99% of the final CAR.
  ppe_use = np.full([num_sims, 1],True)

  #% Cumulative overhead and per-patient consumption in each setting.
  ppe_bg_ph_locn = np.zeros([num_sims, num_settings])
  ppe_case_ph_locn = np.zeros([num_sims, num_settings])

  #% Daily demand for hospital admission and for ICU beds.
  cases = np.zeros([num_sims, 1])
  icu_cases = np.zeros([num_sims, 1])

  #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  #%%
  #%% Daily loop of presentations.
  #%%
  #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

  #% Yesterday's presentations, used to calculate repeat presentation.
  yest_mld_new_GP = np.zeros([num_sims, num_strata])
  yest_mld_new_ED = np.zeros([num_sims, num_strata])
  yest_mld_new_Clinic = np.zeros([num_sims, num_strata])
  yest_mld_rpt_ED = np.zeros([num_sims, num_strata])
  yest_mld_rpt_Clinic = np.zeros([num_sims, num_strata])
  #% Early severe presentations that will still require hospitalisation.
  yest_sev_rpt_ED = np.zeros([num_sims, num_strata])
  yest_sev_rpt_Clinic = np.zeros([num_sims, num_strata])

  #% NOTE: used to compare variables before and after the daily loop, to
  #% ensure that:
  #% 1. No new variables are created, except those listed in "ignore"; and
  #% 2. No existing variables have changed in size.
  S0 = dir()

  for d in range(num_days):

    #%
    #% Step 1: Daily presentations in each setting.
    #%

    #% Daily incidence of new mild cases in each setting.
    mld_new_GP[:,:] = np.tile(moc.mild_to_GP, [1, num_strata]) * di_mild[:, :, d]
    mld_new_ED[:,:] = np.tile(moc.mild_to_ED, [1, num_strata]) * di_mild[:, :, d]
    mld_new_Clinic[:,:] = np.tile(moc.mild_to_Clinic, [1, num_strata]) * di_mild[:, :, d]
    #% Daily incidence of repeat mild cases in each setting.
    mld_rpt_ED[:,:] = np.tile(moc.mild_GP_rpt_ED, [1, num_strata]) * yest_mld_new_GP
    mld_rpt_Clinic[:,:] = np.tile(moc.mild_GP_rpt_Clinic, [1, num_strata]) * yest_mld_new_GP
    mld_rpt_GP[:,:] = np.tile(moc.mild_ED_rpt_GP, [1, num_strata]) * (yest_mld_new_ED + yest_mld_rpt_ED) + np.tile(moc.mild_Clinic_rpt_GP, [1, num_strata]) * (yest_mld_new_Clinic + yest_mld_rpt_Clinic)
    #% Record these presentations for use tomorrow.
    yest_mld_new_GP[:,:] = mld_new_GP
    yest_mld_new_ED[:,:] = mld_new_ED
    yest_mld_new_Clinic[:,:] = mld_new_Clinic
    yest_mld_rpt_ED[:,:] = mld_rpt_ED
    yest_mld_rpt_Clinic[:,:] = mld_rpt_Clinic

    #% Daily incidence of severe cases that present early in each setting.
    sev_new_early[:,:] = np.tile(moc.sev_frac_early, [1, num_strata]) * di_sev[:, :, d]
    sev_new_early_GP[:,:] = np.tile(moc.sev_early_to_GP, [1, num_strata]) * sev_new_early
    sev_new_early_ED[:,:] = np.tile(moc.sev_early_to_ED, [1, num_strata]) * sev_new_early
    sev_new_early_Clinic[:,:] = np.tile(moc.sev_early_to_Clinic, [1, num_strata]) * sev_new_early
    #% Daily incidence of severe cases that present late in each setting.
    sev_new_late[:,:] = np.tile(moc.sev_frac_late, [1, num_strata]) * di_sev[:, :, d]
    sev_new_late_ED[:,:] = np.tile(moc.sev_late_to_ED, [1, num_strata]) * sev_new_late
    sev_new_late_Clinic[:,:] = np.tile(moc.sev_late_to_Clinic, [1, num_strata]) * sev_new_late
    #% Daily incidence of repeat severe cases that require hospitalisation.
    sev_rpt_late_ED[:,:] = yest_sev_rpt_ED
    sev_rpt_late_Clinic[:,:] = yest_sev_rpt_Clinic

    #%
    #% Step 1a: Determine what number of severe cases that present early will
    #%          require hospitalisation **tomorrow**.
    #%

    #% Daily incidence of repeat severe cases in EDs and Clinics.
    sev_rpt_tmrw[:,:] = sev_new_early
    yest_sev_rpt_ED[:,:] = np.tile(moc.sev_late_to_ED, [1, num_strata]) * sev_rpt_tmrw
    yest_sev_rpt_Clinic[:,:] = np.tile(moc.sev_late_to_Clinic, [1, num_strata]) * sev_rpt_tmrw

    #% Daily incidence of ED and Clinic cases that require hospitalisation.
    req_hosp[:, :, d] = sev_new_late + sev_rpt_late_ED + sev_rpt_late_Clinic

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
    numer[:] = frac_ward_avail[:, d] / moc.lm_ED_cap_W0
    frac_ed_avail[:] = moc.lm_ED_cap_E1 + (1 - moc.lm_ED_cap_E1) * numer
    frac_ed_avail[:] = np.minimum(frac_ed_avail, 1)
    avail_ed[:, d] = avail_ed[:, d] * frac_ed_avail
    #% Record the actual ED consultation capacity.
    cap_ed[:, d] = avail_ed[:, d]

    #%
    #% Step 3: Hospital admissions -- how many can we admit?
    #%
    want_beds[:,:] = 0
    for s in range(num_strata):
      #% Clinic admissions.
      req_hosp_via_Clinic[:] = sev_rpt_late_Clinic[:, s] + sev_new_late_Clinic[:, s]

      clinic_cs[:] = np.minimum(req_hosp_via_Clinic, avail_clinic[:, d])
      avail_clinic[:, d] = avail_clinic[:, d] - clinic_cs
      want_beds[:, s] = clinic_cs
      admit_clinic[:, s, d] = clinic_cs
      excess_clinic[:, s, d] = req_hosp_via_Clinic - clinic_cs

      #% ED admissions.
      req_hosp_via_ED[:] = sev_rpt_late_ED[:, s] + sev_new_late_ED[:, s]
      ed_cs[:] = np.minimum(req_hosp_via_ED, avail_ed[:, d])
      avail_ed[:, d] = avail_ed[:, d] - ed_cs
      want_beds[:, s] = want_beds[:, s] + ed_cs
      #% NOTE: here we record ED presentations that lead to admissions.
      #% Mild ED presentations are accounted for later on.
      admit_ed[:, s, d] = ed_cs
      excess_ed[:, s, d] = req_hosp_via_ED - ed_cs

    #%
    #% Step 4: Hospital admissions -- how many can we put in ICU beds?
    #%
    try_ward[:, :] = 0
    for s in range(num_strata):
      #% Determine who needs ward beds and ICU beds.
      cases[:] = want_beds[:, s]
      req_icu[:, s, d] = cases * frac_ward_to_ICU[s]
      try_ward[:, s] = cases - req_icu[:, s, d]
      req_ward[:, s, d] = try_ward[:, s]

      #% Determine who gets ICU beds.
      admit_icu[:, s, d] = min(avail_icu[:, d], req_icu[:, s, d])
      excess_icu[:, s, d] = req_icu[:, s, d] - admit_icu[:, s, d]
      try_ward[:, s] = try_ward[:, s] + excess_icu[:, s, d]

      #% Schedule patients to occupy beds for multiple days.
      x = np.minimum(d + moc.LoS_ICU - 1, num_days);
      avail_icu[:, d:x] = avail_icu[:, d:x] - admit_icu[:, s, d] #Originally: bsxfun(@minus, avail_icu[:, d:x], admit_icu[:, s, d])
      avail_icu[:, d:x] = np.max(avail_icu[:, d:x], 0)

      #% Calculate deaths, on the assumption that not getting an ICU
      #% bed halves the survival rate.
      deaths[:, s, d] = np.squeeze(admit_icu[:, s, d]) * frac_ICU_to_death[s] + np.squeeze(excess_icu[:, s, d]) * frac_noICU_to_death[s]

    #%
    #% Step 5: Hospital admissions -- how many can we put in ward beds?
    #%
    for s in range(num_strata):
      #% Determine who gets ward beds (second priority).
      #% Note: excess cases have *already* presented to an ED or Clinic, so
      #% we're done with them!
      admit_ward[:, s, d] = np.minimum(avail_ward[:, d], try_ward[:, s])
      excess_ward[:, s, d] = try_ward[:, s] - admit_ward[:, s, d]
      #% Schedule patients to occupy beds for multiple days.
      x = np.minimum(d + moc.LoS_Ward - 1, num_days)
      avail_ward[:, d:x] = avail_ward[:, d:x] - admit_ward[:, s, d] #Originally: bsxfun(@minus, avail_ward[:, d:x], admit_ward[:, s, d])
      avail_ward[:, d:x] = np.max(avail_ward[:, d:x], 0)

    #% Update the ward availability, which affects tomorrow's ED capacity.
    frac_ward_avail[:, d + 1] = avail_ward[:, d] / moc.cap_Ward

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

    #%
    #% Step 7: background and per-patient PPE usage in each setting.
    #%

    #% Stop PPE consumption when we reach 100% of the final CAR.
    ppe_use[ppe_stop == d] = False
    flat_ppe_use = ppe_use.flatten()

    #% Background PPE usage in each setting.
    ppe_bg[flat_ppe_use, d] = PPE.daily_bg_ICU + PPE.daily_bg_Ward + PPE.daily_bg_ED + PPE.daily_bg_GP + PPE.daily_bg_Clinic

    #% Per-patient PPE usage in each setting.
    n_icu = cap_icu[flat_ppe_use, d] - avail_icu[flat_ppe_use, d]
    n_ward = cap_ward[flat_ppe_use, d] - avail_ward[flat_ppe_use, d]
    n_ed = cap_ed[flat_ppe_use, d] - avail_ed[flat_ppe_use, d]
    n_gp = cap_gp[flat_ppe_use, d] - avail_gp[flat_ppe_use, d]
    n_clinic = cap_clinic[flat_ppe_use, d] - avail_clinic[flat_ppe_use, d]
    ppe_case[flat_ppe_use, d] = PPE.daily_case_ICU * n_icu + PPE.daily_case_Ward * n_ward + PPE.daily_case_ED * n_ed + PPE.daily_case_GP * n_gp + PPE.daily_case_Clinic * n_clinic

    #% Net PPE consumption in each setting.
    ppe_icu[flat_ppe_use, d] = PPE.daily_bg_ICU + PPE.daily_case_ICU * n_icu
    ppe_ward[flat_ppe_use, d] = PPE.daily_bg_Ward + PPE.daily_case_Ward * n_ward
    ppe_ed[flat_ppe_use, d] = PPE.daily_bg_ED + PPE.daily_case_ED * n_ed
    ppe_gp[flat_ppe_use, d] = PPE.daily_bg_GP + PPE.daily_case_GP * n_gp
    ppe_clinic[flat_ppe_use, d] = PPE.daily_bg_Clinic + PPE.daily_case_Clinic * n_clinic

    #% Calculate P2 mask consumption (per-case basis only).
    #% NOTE: in EDs, GPs and clinics, P2 masks might only be consumed when
    #% dealing with a severe case.
    #% Here, we use the mean proportion of presentations that are severe as a
    #% proxy for keeping track of daily presentations in each setting
    #% separately for mild and severe cases, in addition to the general demand
    #% placed on each setting.
    p2_icu[flat_ppe_use, d] = PPE.p2_case_icu * n_icu
    p2_ward[flat_ppe_use, d] = PPE.p2_case_ward * n_ward
    if PPE.p2_case_ed_severe > 0:
        p2_ed[flat_ppe_use, d] = PPE.p2_case_ed_severe * n_ed * frac_presns_severe[flat_ppe_use]
    else:
        p2_ed[flat_ppe_use, d] = PPE.p2_case_ed * n_ed
    if PPE.p2_case_gp_severe > 0:
        p2_gp[flat_ppe_use, d] = PPE.p2_case_gp_severe * n_gp * frac_presns_severe[flat_ppe_use]
    else:
        p2_gp[flat_ppe_use, d] = PPE.p2_case_gp * n_gp
    if PPE.p2_case_clinic_severe > 0:
        p2_clinic[flat_ppe_use, d] = PPE.p2_case_clinic_severe * n_clinic * frac_presns_severe[flat_ppe_use]
    else:
        p2_clinic[flat_ppe_use, d] = PPE.p2_case_clinic * n_clinic

    p2_case[flat_ppe_use, d] = p2_icu[flat_ppe_use, d] + p2_ward[flat_ppe_use, d] + p2_ed[flat_ppe_use, d] + p2_gp[flat_ppe_use, d] + p2_clinic[flat_ppe_use, d]

    #% Record the cumulative background consumption in each setting.
    ppe_bg_ph_locn[flat_ppe_use, 0] = ppe_bg_ph_locn[flat_ppe_use, 0] + PPE.daily_bg_ICU
    ppe_bg_ph_locn[flat_ppe_use, 1] = ppe_bg_ph_locn[flat_ppe_use, 1] + PPE.daily_bg_Ward
    ppe_bg_ph_locn[flat_ppe_use, 2] = ppe_bg_ph_locn[flat_ppe_use, 2] + PPE.daily_bg_ED
    ppe_bg_ph_locn[flat_ppe_use, 3] = ppe_bg_ph_locn[flat_ppe_use, 3] + PPE.daily_bg_GP
    ppe_bg_ph_locn[flat_ppe_use, 4] = ppe_bg_ph_locn[flat_ppe_use, 4] + PPE.daily_bg_Clinic

    #% Record the cumulative per-patient consumption in each setting.
    ppe_case_ph_locn[flat_ppe_use, 0] = ppe_case_ph_locn[flat_ppe_use, 0] + PPE.daily_case_ICU * n_icu
    ppe_case_ph_locn[flat_ppe_use, 1] = ppe_case_ph_locn[flat_ppe_use, 1] + PPE.daily_case_Ward * n_ward
    ppe_case_ph_locn[flat_ppe_use, 2] = ppe_case_ph_locn[flat_ppe_use, 2] + PPE.daily_case_ED * n_ed
    ppe_case_ph_locn[flat_ppe_use, 3] = ppe_case_ph_locn[flat_ppe_use, 3] + PPE.daily_case_GP * n_gp
    ppe_case_ph_locn[flat_ppe_use, 4] = ppe_case_ph_locn[flat_ppe_use, 4] + PPE.daily_case_Clinic * n_clinic

  #% Compare variables before and after the daily loop, to ensure that:
  #% 1. No new variables are created, except those listed in "ignore"; and
  #% 2. No existing variables have changed in size.
  '''S1 = dir()
  for ix in range(len(S1)):
    vname = S1[ix]

    ignore = ['S0', 'd', 's', 'x', 'moc_ixs', 'n_icu', 'n_ward', 'n_ed', 'n_gp', 'n_clinic', 'p', 'mask', 'pmask', 'nmask']
    if vname in ignore:
      continue

    vsize = locals(vname).shape #TODO
    ssize = str(vsize)
    match = strmatch(vname, char(S0.name), 'exact')
    if length(match) == 0:
      fprintf('New variable "%s" with size %s\n', vname, ssize)
    elif len(match) == 1:
      oname = S0(match).name
      osize = S0(match).size
      if any(vsize ~= osize):
        osize = sprintf(repmat('%dx', [1, length(osize)]), osize)
        osize = osize(1:end - 1)
        fprintf('Variable "%s" changed from %s to %s\n', vname, osize, ssize)
    else:
      fprintf('Odd, multiple matches for "%s" ...\n', vname);'''


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

  #% Record outcomes of interest.
  out = {};
  out['strata_deaths'] = np.sum(deaths, 2);
  out['total_deaths'] = np.sum(out['strata_deaths'], 1);
  out['strata_excess_icu'] = np.sum(excess_icu, 2);
  out['strata_excess_ward'] = np.sum(excess_ward, 2);
  out['strata_excess_ed'] = np.sum(excess_ed, 2);
  out['strata_excess_clinic'] = np.sum(excess_clinic, 2);
  out['strata_excess_gp'] = np.sum(excess_gp, 2);
  out['daily_icu_excess'] = np.squeeze(np.sum(excess_icu, 1));
  out['daily_ward_excess'] = np.squeeze(np.sum(excess_ward, 1));
  out['daily_ed_excess'] = np.squeeze(np.sum(excess_ed, 1));
  out['daily_clinic_excess'] = np.squeeze(np.sum(excess_clinic, 1));
  out['daily_gp_excess'] = np.squeeze(np.sum(excess_gp, 1));
  out['net_icu_excess'] = np.squeeze(np.sum(out['daily_icu_excess']));
  out['net_ward_excess'] = np.squeeze(np.sum(out['daily_ward_excess']));
  out['net_ed_excess'] = np.squeeze(np.sum(out['daily_ed_excess']));
  out['net_clinic_excess'] = np.squeeze(np.sum(out['daily_clinic_excess']));
  out['net_gp_excess'] = np.squeeze(np.sum(out['daily_gp_excess']));
  out['peak_icu_excess'] = np.max(out['daily_icu_excess']);
  out['peak_ward_excess'] = np.max(out['daily_ward_excess']);
  out['peak_ed_excess'] = np.max(out['daily_ed_excess']);
  out['peak_clinic_excess'] = np.max(out['daily_clinic_excess']);
  out['peak_gp_excess'] = np.max(out['daily_gp_excess']);
  out['icu_excess_durn'] = np.sum(out['daily_icu_excess'] > 0);
  out['ward_excess_durn'] = np.sum(out['daily_ward_excess'] > 0);
  out['ed_excess_durn'] = np.sum(out['daily_ed_excess'] > 0);
  out['clinic_excess_durn'] = np.sum(out['daily_clinic_excess'] > 0);
  out['gp_excess_durn'] = np.sum(out['daily_gp_excess'] > 0);
  out['daily_icu'] = cap_icu - avail_icu;
  out['daily_ward'] = cap_ward - avail_ward;
  out['daily_ed'] = cap_ed - avail_ed;
  out['daily_clinic'] = cap_clinic - avail_clinic;
  out['daily_gp'] = cap_gp - avail_gp;
  out['peak_icu'] = np.max(out['daily_icu']);
  out['peak_ward'] = np.max(out['daily_ward']);
  out['peak_ed'] = np.max(out['daily_ed']);
  out['peak_clinic'] = np.max(out['daily_clinic']);
  out['peak_gp'] = np.max(out['daily_gp']);
  out['strata_icu'] = np.sum(admit_icu, 2);
  out['strata_ward'] = np.sum(admit_ward, 2);
  out['strata_ed'] = np.sum(admit_ed, 2);
  out['strata_clinic'] = np.sum(admit_clinic, 2);
  out['strata_gp'] = np.sum(admit_gp, 2);
  out['total_icu'] = np.sum(out['strata_icu'], 1);
  out['total_ward'] = np.sum(out['strata_ward'], 1);
  out['total_ed'] = np.sum(out['strata_ed'], 1);
  out['total_clinic'] = np.sum(out['strata_clinic'], 1);
  out['total_gp'] = np.sum(out['strata_gp'], 1);
  out['want_hosp'] = np.sum(np.sum(req_hosp, 2), 1);
  out['want_icu'] = np.sum(np.sum(req_icu, 2), 1);
  out['want_ward'] = np.sum(np.sum(req_ward, 2), 1);
  out['true_want_icu'] = np.sum(np.sum(true_req_icu, 2), 1);
  out['true_want_ward'] = np.sum(np.sum(true_req_ward, 2), 1);
  out['peak_true_req_icu'] = peak_true_req_icu;
  out['peak_true_req_ward'] = peak_true_req_ward;
  out['peak_true_req_ed'] = peak_true_req_ed;
  out['peak_true_req_gp'] = peak_true_req_gp;

  #% PPE (surgical mask) usage.
  out['ppe_bg'] = np.sum(ppe_bg, 1);
  out['ppe_case'] = np.sum(ppe_case, 1);
  out['ppe_total'] = out['ppe_bg'] + out['ppe_case'];
  out['ppe_icu'] = np.sum(ppe_icu, 1);
  out['ppe_ward'] = np.sum(ppe_ward, 1);
  out['ppe_ed'] = np.sum(ppe_ed, 1);
  out['ppe_gp'] = np.sum(ppe_gp, 1);
  out['ppe_clinic'] = np.sum(ppe_clinic, 1);

  #% P2 mask usage.
  out['p2_total'] = np.sum(p2_case, 1);
  out['p2_icu'] = np.sum(p2_icu, 1);
  out['p2_ward'] = np.sum(p2_ward, 1);
  out['p2_ed'] = np.sum(p2_ed, 1);
  out['p2_gp'] = np.sum(p2_gp, 1);
  out['p2_clinic'] = np.sum(p2_clinic, 1);

  #% NOTE: calculate surgical mask and P2 mask usage over 4-week intervals,
  #% and report as a percentage of the net mask usage.
  ppe_net = ppe_bg + ppe_case;
  denom = np.sum(ppe_net, 1);
  out['ppe_4wk_1'] = np.sum(ppe_net[:, 0*28+1:1*28], 1) * 100 / denom;
  out['ppe_4wk_2'] = np.sum(ppe_net[:, 1*28+1:2*28], 1) * 100 / denom;
  out['ppe_4wk_3'] = np.sum(ppe_net[:, 2*28+1:3*28], 1) * 100 / denom;
  out['ppe_4wk_4'] = np.sum(ppe_net[:, 3*28+1:4*28], 1) * 100 / denom;
  out['ppe_4wk_5'] = np.sum(ppe_net[:, 4*28+1:5*28], 1) * 100 / denom;
  out['ppe_4wk_6'] = np.sum(ppe_net[:, 5*28+1:6*28], 1) * 100 / denom;
  out['ppe_4wk_7'] = np.sum(ppe_net[:, 6*28+1:7*28], 1) * 100 / denom;
  out['ppe_4wk_8'] = np.sum(ppe_net[:, 7*28+1:8*28], 1) * 100 / denom;
  out['ppe_4wk_9'] = np.sum(ppe_net[:, 8*28+1:9*28], 1) * 100 / denom;
  out['ppe_4wk_10'] = np.sum(ppe_net[:, 9*28+1:10*28], 1) * 100 / denom;
  out['ppe_4wk_11'] = np.sum(ppe_net[:, 10*28+1:11*28], 1) * 100 / denom;
  out['ppe_4wk_12'] = np.sum(ppe_net[:, 11*28+1:12*28], 1) * 100 / denom;
  out['ppe_4wk_13'] = np.sum(ppe_net[:, 12*28+1:13*28], 1) * 100 / denom;

  denom = np.sum(p2_case, 1);
  out['p2_4wk_1'] = np.sum(p2_case[:, 0*28+1:1*28], 1) * 100 / denom;
  out['p2_4wk_2'] = np.sum(p2_case[:, 1*28+1:2*28], 1) * 100 / denom;
  out['p2_4wk_3'] = np.sum(p2_case[:, 2*28+1:3*28], 1) * 100 / denom;
  out['p2_4wk_4'] = np.sum(p2_case[:, 3*28+1:4*28], 1) * 100 / denom;
  out['p2_4wk_5'] = np.sum(p2_case[:, 4*28+1:5*28], 1) * 100 / denom;
  out['p2_4wk_6'] = np.sum(p2_case[:, 5*28+1:6*28], 1) * 100 / denom;
  out['p2_4wk_7'] = np.sum(p2_case[:, 6*28+1:7*28], 1) * 100 / denom;
  out['p2_4wk_8'] = np.sum(p2_case[:, 7*28+1:8*28], 1) * 100 / denom;
  out['p2_4wk_9'] = np.sum(p2_case[:, 8*28+1:9*28], 1) * 100 / denom;
  out['p2_4wk_10'] = np.sum(p2_case[:, 9*28+1:10*28], 1) * 100 / denom;
  out['p2_4wk_11'] = np.sum(p2_case[:, 10*28+1:11*28], 1) * 100 / denom;
  out['p2_4wk_12'] = np.sum(p2_case[:, 11*28+1:12*28], 1) * 100 / denom;
  out['p2_4wk_13'] = np.sum(p2_case[:, 12*28+1:13*28], 1) * 100 / denom;

  return out





