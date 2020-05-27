%% OUTCOMES_FOR_MOC(moc, data, strata_fracs)
%
% Calculate the population outcomes and healthcare impact of an nCoV scenario
% for the provided model of care 'moc'. Note that 'data' should be the result
% of loading the scenario results with MOST_RECENT().
%
% The optional argument 'strata_fracs' can be used to define new model strata.
% It should have size [A B] where the epidemic model has B strata, and the
% intent is to have A strata.
%
% Example:
%   >> data = most_recent('some_scenario');
%   >> moc = model_of_care('default', 'high');
%   >> outcomes = outcomes_for_moc(moc, data);
%
%See also model_of_care, most_recent
function out = outcomes_for_moc(moc, data, strata_fracs)
  %% Retrieve the daily numbers of new mild and severe cases.
  di_mild = get_stat(data, 'DailyPresentationsMild');
  di_sev = get_stat(data, 'DailyPresentationsSevere');

  %% NOTE: scale daily incidence by the population fraction.
  if abs(1.0 - moc.popn_frac) > 1e-7
      di_mild = round(moc.popn_frac * di_mild);
      di_sev = round(moc.popn_frac * di_sev);
  end

  if nargin > 2
      %% Check that the strata fractions matrix has appropriate dimensions.
      dims = size(strata_fracs);
      if length(dims) ~= 2
          error('strata_fracs must be a matrix');
      end
      if dims(2) ~= size(di_mild, 2)
          error('strata_fracs has incorrect dimensions');
      end

      %% Check that the columns sum to 1; i.e., that the total population is
      %% conserved.
      if ~ all(abs(sum(fracs) - 1) < 1e-12)
          error('strata_fracs does not conserve the population');
      end
      %% Check that all values lie in [0, 1].
      if (min(strata_fracs(:)) < 0) || (max(strata_fracs(:)) > 1)
          error('strata_fracs contains values outside of [0 1]');
      end

      %% Determine the new number of strata and define the dimensions of the
      %% daily mild and severe presentations.
      new_size = size(di_mild);
      new_size(2) = dims(1);

      %% Allocate new arrays for the daily mild and severe presentations.
      new_mild = zeros(new_size);
      new_sev = zeros(new_size);

      %% Calculate the numbers of mild and severe presentations for each of
      %% the new strata.
      %% TODO: allow the model of care to override these proportions and
      %% instead calculate mild and severe presentations based on the daily
      %% incidence?
      for i = 1:dims(1)
          new_mild(:, i, :) = sum(di_mild .* strata_fracs(i, :), 2);
          new_sev(:, i, :) = sum(di_sev .* strata_fracs(i, :), 2);
      end

      %% Replace the original arrays.
      di_mild = new_mild;
      di_sev = new_sev;
  end

  %% TODO: add a frac_visible argument, or make it a model_of_care parameter?
  %% Or simply relax the restriction that columns sum to 1?

  %% Define some frequently-used dimension sizes.
  num_strata = size(di_mild, 2);
  num_days = size(di_mild, 3);

  %% NOTE: override moc.ward_to_ICU when params.propn_icu exists.
  if isfield(data.lhs_data.unsampled_params, 'propn_icu')
      %% fprintf('Setting ward_to_ICU = params.propn_ICU\n');
      moc.ward_to_ICU = data.lhs_data.unsampled_params.propn_icu;
  end

  %% NOTE: check that the number of strata match the dimensions of the case
  %% severity parameters in the model of care.
  need_moc_size = [num_strata 1];
  if ~ isequal(need_moc_size, size(moc.ward_to_ICU))
      error('Number of strata does not match moc.ward_to_ICU')
  end
  if ~ isequal(need_moc_size, size(moc.ICU_to_death))
      error('Number of strata does not match moc.ICU_to_death')
  end
  if ~ isequal(need_moc_size, size(moc.noICU_to_death))
      error('Number of strata does not match moc.noICU_to_death')
  end

  PPE = moc.ppe_usage;

  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  %%
  %% Allocate matrices for daily demand, capacity, and outcomes.
  %%
  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

  %% Mild presentations in each setting.
  mld_new_GP = zeros([data.lhs_data.samples num_strata]);
  mld_new_ED = zeros([data.lhs_data.samples num_strata]);
  mld_new_Clinic = zeros([data.lhs_data.samples num_strata]);
  mld_rpt_GP = zeros([data.lhs_data.samples num_strata]);
  mld_rpt_ED = zeros([data.lhs_data.samples num_strata]);
  mld_rpt_Clinic = zeros([data.lhs_data.samples num_strata]);
  mld_GP = zeros([data.lhs_data.samples 1]);
  mld_ED = zeros([data.lhs_data.samples 1]);
  mld_Clinic = zeros([data.lhs_data.samples 1]);

  %% Severe presentations in each setting.
  sev_new_early = zeros([data.lhs_data.samples num_strata]);
  sev_new_early_GP = zeros([data.lhs_data.samples num_strata]);
  sev_new_early_ED = zeros([data.lhs_data.samples num_strata]);
  sev_new_early_Clinic = zeros([data.lhs_data.samples num_strata]);
  %% Daily incidence of severe cases that present late in each setting.
  sev_new_late = zeros([data.lhs_data.samples num_strata]);
  sev_new_late_ED = zeros([data.lhs_data.samples num_strata]);
  sev_new_late_Clinic = zeros([data.lhs_data.samples num_strata]);
  %% Daily incidence of repeat severe cases that present in each setting.
  sev_rpt_late_ED = zeros([data.lhs_data.samples num_strata]);
  sev_rpt_late_Clinic = zeros([data.lhs_data.samples num_strata]);

  %% Daily incidence of severe cases that present early; they will present
  %% with more severe disease and require hospitalisation.
  sev_rpt_tmrw = zeros([data.lhs_data.samples num_strata]);

  %% The daily demand for hospitalisation.
  %% NOTE: this is the presenting severe proportion, ignoring "early" severe
  %% cases and counting "late" repeat presentations.
  %% Multiply this by frac_ward_to_ICU to determine the ward/ICU split.
  req_hosp = zeros(size(di_sev));

  req_hosp_via_Clinic = zeros([data.lhs_data.samples 1]);
  req_hosp_via_ED = zeros([data.lhs_data.samples 1]);
  clinic_cs = zeros([data.lhs_data.samples 1]);
  ed_cs = zeros([data.lhs_data.samples 1]);

  %% Yesterday's (fractional) ward availability.
  frac_ward_avail = ones([data.lhs_data.samples num_days + 1]);

  %% The fractional ED availability.
  frac_ed_avail = zeros([data.lhs_data.samples 1]);
  numer = zeros([data.lhs_data.samples 1]);

  %% The daily demand for bed occupancy for each strata.
  req_ward = zeros(size(di_sev));
  req_icu = zeros(size(di_sev));

  %% Baseline daily capacities.
  avail_icu = repmat(moc.cap_ICU, [data.lhs_data.samples num_days]);
  avail_ward = repmat(moc.cap_Ward, [data.lhs_data.samples num_days]);
  avail_ed = repmat(moc.cap_ED, [data.lhs_data.samples num_days]);
  avail_clinic = repmat(moc.cap_Clinic, [data.lhs_data.samples num_days]);
  avail_gp = repmat(moc.cap_GP, [data.lhs_data.samples num_days]);

  %% Record the baseline capacities, in addition to remaining capacities.
  cap_icu = avail_icu;
  cap_ward = avail_ward;
  cap_ed = avail_ed;
  cap_clinic = avail_clinic;
  cap_gp = avail_gp;

  %% Daily admissions / consultations.
  admit_icu = zeros(size(di_sev));
  admit_ward = zeros(size(di_sev));
  admit_ed = zeros(size(di_sev));
  admit_clinic = zeros(size(di_sev));
  admit_gp = zeros(size(di_sev));

  %% Daily excess admissions / consultations.
  excess_icu = zeros(size(di_sev));
  excess_ward = zeros(size(di_sev));
  excess_ed = zeros(size(di_sev));
  excess_clinic = zeros(size(di_sev));
  excess_gp = zeros(size(di_sev));

  %% Daily deaths.
  deaths = zeros(size(di_sev));

  %% Daily number of cases we want to admit to hospital.
  want_beds = zeros([data.lhs_data.samples num_strata]);
  %% Daily number of cases we want to admit to wards.
  try_ward = zeros([data.lhs_data.samples num_strata]);

  %% Daily PPE consumption.
  ppe_bg = zeros([data.lhs_data.samples num_days]);
  ppe_case = zeros([data.lhs_data.samples num_days]);
  %% Daily PPE consumption in each setting.
  ppe_icu = zeros([data.lhs_data.samples num_days]);
  ppe_ward = zeros([data.lhs_data.samples num_days]);
  ppe_ed = zeros([data.lhs_data.samples num_days]);
  ppe_gp = zeros([data.lhs_data.samples num_days]);
  ppe_clinic = zeros([data.lhs_data.samples num_days]);
  %% Daily P2 mask consumption.
  p2_case = zeros([data.lhs_data.samples num_days]);
  %% Daily P2 mask consumption in each setting.
  p2_icu = zeros([data.lhs_data.samples num_days]);
  p2_ward = zeros([data.lhs_data.samples num_days]);
  p2_ed = zeros([data.lhs_data.samples num_days]);
  p2_gp = zeros([data.lhs_data.samples num_days]);
  p2_clinic = zeros([data.lhs_data.samples num_days]);

  %% Stop PPE consumption when we reach 99% of the final CAR.
  tCAR_99 = get_stat(data, 'CAR99');
  ppe_stop = ceil(squeeze(tCAR_99));
  ppe_use = true([data.lhs_data.samples, 1]);

  %% Cumulative overhead and per-patient consumption in each setting.
  num_settings = 5;
  ppe_bg_ph_locn = zeros([data.lhs_data.samples num_settings]);
  ppe_case_ph_locn = zeros([data.lhs_data.samples num_settings]);

  %% Daily demand for hospital admission.
  cases = zeros([data.lhs_data.samples 1]);

  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  %%
  %% Daily loop of presentations.
  %%
  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

  %% Yesterday's presentations, used to calculate repeat presentation.
  yest_mld_new_GP = zeros([data.lhs_data.samples num_strata]);
  yest_mld_new_ED = zeros([data.lhs_data.samples num_strata]);
  yest_mld_new_Clinic = zeros([data.lhs_data.samples num_strata]);
  yest_mld_rpt_ED = zeros([data.lhs_data.samples num_strata]);
  yest_mld_rpt_Clinic = zeros([data.lhs_data.samples num_strata]);
  %% Early severe presentations that will still require hospitalisation.
  yest_sev_rpt_ED = zeros([data.lhs_data.samples num_strata]);
  yest_sev_rpt_Clinic = zeros([data.lhs_data.samples num_strata]);

  %% NOTE: used to compare variables before and after the daily loop, to
  %% ensure that:
  %% 1. No new variables are created, except those listed in "ignore"; and
  %% 2. No existing variables have changed in size.
  S0 = whos();

  for d = 1:num_days

    %%
    %% Step 1: Daily presentations in each setting.
    %%

    %% Daily incidence of new mild cases in each setting.
    mld_new_GP(:, :) = repmat(moc.mild_to_GP, 1, num_strata) .* ...
                       di_mild(:, :, d);
    mld_new_ED(:, :) = repmat(moc.mild_to_ED, 1, num_strata) .* ...
                       di_mild(:, :, d);
    mld_new_Clinic(:, :) = repmat(moc.mild_to_Clinic, 1, num_strata) .* ...
                           di_mild(:, :, d);
    %% Daily incidence of repeat mild cases in each setting.
    mld_rpt_ED(:, :) = repmat(moc.mild_GP_rpt_ED, 1, num_strata) .* ...
                       yest_mld_new_GP;
    mld_rpt_Clinic(:, :) = repmat(moc.mild_GP_rpt_Clinic, 1, num_strata) .* ...
                           yest_mld_new_GP;
    mld_rpt_GP(:, :) = repmat(moc.mild_ED_rpt_GP, 1, num_strata) .* ...
                       (yest_mld_new_ED + yest_mld_rpt_ED) + ...
                       repmat(moc.mild_Clinic_rpt_GP, 1, num_strata) .* ...
                       (yest_mld_new_Clinic + yest_mld_rpt_Clinic);
    %% Record these presentations for use tomorrow.
    yest_mld_new_GP(:, :) = mld_new_GP;
    yest_mld_new_ED(:, :) = mld_new_ED;
    yest_mld_new_Clinic(:, :) = mld_new_Clinic;
    yest_mld_rpt_ED(:, :) = mld_rpt_ED;
    yest_mld_rpt_Clinic(:, :) = mld_rpt_Clinic;

    %% Daily incidence of severe cases that present early in each setting.
    sev_new_early(:, :) = repmat(moc.sev_frac_early, 1, num_strata) .* ...
                          di_sev(:, :, d);
    sev_new_early_GP(:, :) = repmat(moc.sev_early_to_GP, 1, num_strata) .* ...
                             sev_new_early;
    sev_new_early_ED(:, :) = repmat(moc.sev_early_to_ED, 1, num_strata) .* ...
                             sev_new_early;
    sev_new_early_Clinic(:, :) = repmat(moc.sev_early_to_Clinic, 1, num_strata) .* ...
                                 sev_new_early;
    %% Daily incidence of severe cases that present late in each setting.
    sev_new_late(:, :) = repmat(moc.sev_frac_late, 1, num_strata) .* ...
                         di_sev(:, :, d);
    sev_new_late_ED(:, :) = repmat(moc.sev_late_to_ED, 1, num_strata) .* ...
                            sev_new_late;
    sev_new_late_Clinic(:, :) = repmat(moc.sev_late_to_Clinic, 1, num_strata) .* ...
                                sev_new_late;
    %% Daily incidence of repeat severe cases that require hospitalisation.
    sev_rpt_late_ED(:, :) = yest_sev_rpt_ED;
    sev_rpt_late_Clinic(:, :) = yest_sev_rpt_Clinic;

    %%
    %% Step 1a: Determine what number of severe cases that present early will
    %%          require hospitalisation **tomorrow**.
    %%

    %% Daily incidence of repeat severe cases in EDs and Clinics.
    sev_rpt_tmrw(:, :) = sev_new_early;
    yest_sev_rpt_ED(:, :) = repmat(moc.sev_late_to_ED, 1, num_strata) .* ...
                            sev_rpt_tmrw;
    yest_sev_rpt_Clinic(:, :) = repmat(moc.sev_late_to_Clinic, 1, num_strata) .* ...
                             sev_rpt_tmrw;

    %% Daily incidence of ED and Clinic cases that require hospitalisation.
    req_hosp(:, :, d) = sev_new_late + sev_rpt_late_ED + sev_rpt_late_Clinic;

    %% Okay, we now know how many will *attempt* to present in each
    %% setting *today* and how many will require hospitalisation:
    %%
    %%     req_hosp(:, :, d).
    %%
    %% To account for hospital admission capacity, which depends on ED
    %% capacity, which is itself a function of *yesterday's* ward
    %% utilisation, we need to step forward day by day.
    %%
    %% Recall that arrays are 10000 x 5 x 366 (samples x strata x days).
    %%

    %%
    %% Step 2: ED consultation capacity, given ward utilisation.
    %%
    numer(:) = frac_ward_avail(:, d) / moc.lm_ED_cap_W0;
    frac_ed_avail(:) = moc.lm_ED_cap_E1 + ...
                       (1 - moc.lm_ED_cap_E1) .* numer;
    frac_ed_avail(:) = min(frac_ed_avail, 1);
    avail_ed(:, d) = avail_ed(:, d) .* frac_ed_avail;
    %% Record the actual ED consultation capacity.
    cap_ed(:, d) = avail_ed(:, d);

    %%
    %% Step 3: Hospital admissions -- how many can we admit?
    %%
    want_beds(:, :) = 0;
    for s = 1:num_strata
      %% Clinic admissions.
      req_hosp_via_Clinic(:) = sev_rpt_late_Clinic(:, s) + ...
                               sev_new_late_Clinic(:, s);
      clinic_cs(:) = min(req_hosp_via_Clinic, avail_clinic(:, d));
      avail_clinic(:, d) = avail_clinic(:, d) - clinic_cs;
      want_beds(:, s) = clinic_cs;
      admit_clinic(:, s, d) = clinic_cs;
      excess_clinic(:, s, d) = req_hosp_via_Clinic - clinic_cs;

      %% ED admissions.
      req_hosp_via_ED(:) = sev_rpt_late_ED(:, s) + ...
                           sev_new_late_ED(:, s);
      ed_cs(:) = min(req_hosp_via_ED, avail_ed(:, d));
      avail_ed(:, d) = avail_ed(:, d) - ed_cs;
      want_beds(:, s) = want_beds(:, s) + ed_cs;
      %% NOTE: here we record ED presentations that lead to admissions.
      %% Mild ED presentations are accounted for later on.
      admit_ed(:, s, d) = ed_cs;
      excess_ed(:, s, d) = req_hosp_via_ED - ed_cs;
    end

    %%
    %% Step 4: Hospital admissions -- how many can we put in ICU beds?
    %%
    try_ward(:, :) = 0;
    for s = 1:num_strata
      %% Determine who needs ward beds and ICU beds.
      cases(:) = want_beds(:, s);
      req_icu(:, s, d) = cases .* moc.ward_to_ICU(s);
      try_ward(:, s) = cases - req_icu(:, s, d);
      req_ward(:, s, d) = try_ward(:, s);

      %% Determine who gets ICU beds.
      admit_icu(:, s, d) = min(avail_icu(:, d), req_icu(:, s, d));
      excess_icu(:, s, d) = req_icu(:, s, d) - ...
                            admit_icu(:, s, d);
      try_ward(:, s) = try_ward(:, s) + excess_icu(:, s, d);

      %% Schedule patients to occupy beds for multiple days.
      x = min(d + moc.LoS_ICU - 1, num_days);
      avail_icu(:, d:x) = bsxfun(@minus, avail_icu(:, d:x), ...
                                 admit_icu(:, s, d));
      avail_icu(:, d:x) = max(avail_icu(:, d:x), 0);

      %% Calculate deaths, on the assumption that not getting an ICU
      %% bed halves the survival rate.
      deaths(:, s, d) = squeeze(admit_icu(:, s, d)) * moc.ICU_to_death(s) ...
                        + squeeze(excess_icu(:, s, d)) * moc.noICU_to_death(s);
    end

    %%
    %% Step 5: Hospital admissions -- how many can we put in ward beds?
    %%
    for s = 1:num_strata
      %% Determine who gets ward beds (second priority).
      %% Note: excess cases have *already* presented to an ED or Clinic, so
      %% we're done with them!
      admit_ward(:, s, d) = min(avail_ward(:, d), try_ward(:, s));
      excess_ward(:, s, d) = try_ward(:, s) - ...
                             admit_ward(:, s, d);
      %% Schedule patients to occupy beds for multiple days.
      x = min(d + moc.LoS_Ward - 1, num_days);
      avail_ward(:, d:x) = bsxfun(@minus, avail_ward(:, d:x), ...
                                  admit_ward(:, s, d));
      avail_ward(:, d:x) = max(avail_ward(:, d:x), 0);
    end
    %% Update the ward availability, which affects tomorrow's ED capacity.
    frac_ward_avail(:, d + 1) = avail_ward(:, d) ./ moc.cap_Ward;

    %%
    %% Step 6: Out-patient presentations and treatment.
    %%
    for s = 1:num_strata
      %% Calculate mild clinic consultations.
      mld_Clinic(:) = mld_new_Clinic(:, s) + mld_rpt_Clinic(:, s);
      admit_clinic(:, s, d) = min(avail_clinic(:, d), mld_Clinic);
      excess_clinic(:, s, d) = excess_clinic(:, s, d) + ...
                            (mld_Clinic - admit_clinic(:, s, d));
      avail_clinic(:, d) = avail_clinic(:, d) - admit_clinic(:, s, d);

      %% Calculate mild ED consultations.
      mld_ED(:) = mld_new_ED(:, s) + mld_rpt_ED(:, s);
      %% NOTE: here we overwrite ED presentations that lead to admissions,
      %% which is stored in admit_ed(:, s, d), so we need to record its
      %% current value before proceeding.
      ed_to_ward = admit_ed(:, s, d);
      admit_ed(:, s, d) = min(avail_ed(:, d), mld_ED);
      excess_ed(:, s, d) = excess_ed(:, s, d) + ...
                           (mld_ED - admit_ed(:, s, d));
      avail_ed(:, d) = avail_ed(:, d) - admit_ed(:, s, d);
      %% NOTE: add the ED presentations that lead to admissions, and remove
      %% the temporary variable.
      admit_ed(:, s, d) = admit_ed(:, s, d) + ed_to_ward;
      clear ed_to_ward;

      %% Calculate mild GP consultations.
      mld_GP(:) = mld_new_GP(:, s) + mld_rpt_GP(:, s);
      %% Assume that excess ED and Clinic consultations present to GPs.
      mld_GP(:) = mld_GP + excess_clinic(:, s, d) + excess_ed(:, s, d);
      admit_gp(:, s, d) = min(avail_gp(:, d), mld_GP);
      excess_gp(:, s, d) = excess_gp(:, s, d) + ...
                           (mld_GP - admit_gp(:, s, d));
      avail_gp(:, d) = avail_gp(:, d) - admit_gp(:, s, d);
    end

    %%
    %% Step 7: background and per-patient PPE usage in each setting.
    %%

    %% Stop PPE consumption when we reach 100% of the final CAR.
    ppe_use(ppe_stop == d) = false;

    %% Background PPE usage in each setting.
    ppe_bg(ppe_use, d) = PPE.daily_bg_ICU + ...
                         PPE.daily_bg_Ward + ...
                         PPE.daily_bg_ED + ...
                         PPE.daily_bg_GP + ...
                         PPE.daily_bg_Clinic;

    %% Per-patient PPE usage in each setting.
    n_icu = cap_icu(ppe_use, d) - avail_icu(ppe_use, d);
    n_ward = cap_ward(ppe_use, d) - avail_ward(ppe_use, d);
    n_ed = cap_ed(ppe_use, d) - avail_ed(ppe_use, d);
    n_gp = cap_gp(ppe_use, d) - avail_gp(ppe_use, d);
    n_clinic = cap_clinic(ppe_use, d) - avail_clinic(ppe_use, d);
    ppe_case(ppe_use, d) = PPE.daily_case_ICU .* n_icu + ...
                           PPE.daily_case_Ward .* n_ward + ...
                           PPE.daily_case_ED .* n_ed + ...
                           PPE.daily_case_GP .* n_gp + ...
                           PPE.daily_case_Clinic .* n_clinic;

    %% Net PPE consumption in each setting.
    ppe_icu(ppe_use, d) = PPE.daily_bg_ICU + ...
                          PPE.daily_case_ICU .* n_icu;
    ppe_ward(ppe_use, d) = PPE.daily_bg_Ward + ...
                           PPE.daily_case_Ward .* n_ward;
    ppe_ed(ppe_use, d) = PPE.daily_bg_ED + ...
                         PPE.daily_case_ED .* n_ed;
    ppe_gp(ppe_use, d) = PPE.daily_bg_GP + ...
                         PPE.daily_case_GP .* n_gp;
    ppe_clinic(ppe_use, d) = PPE.daily_bg_Clinic + ...
                             PPE.daily_case_Clinic .* n_clinic;

    %% Calculate P2 mask consumption (per-case basis only).
    %% NOTE: in EDs, GPs and clinics, P2 masks might only be consumed when
    %% dealing with a severe case.
    %% Here, we look at the proportion of presentation *demand* that is severe
    %% as a proxy for keeping track of daily presentations in each setting
    %% separately for mild and severe cases.
    p2_icu(ppe_use, d) = PPE.p2_case_icu .* n_icu;
    p2_ward(ppe_use, d) = PPE.p2_case_ward .* n_ward;

    if PPE.p2_case_ed_severe > 0
        %% Calculate the proportion of ED presentations that are severe cases,
        %% for each strata.
        sev_ED = sev_new_early_ED + sev_new_late_ED + sev_rpt_late_ED;
        frac_sev = sev_ED ./ (sev_ED + mld_ED);
        frac_sev(sev_ED == 0) = 0;
        %% Calculate the net proportion of ED presentations that are severe.
        frac_sev = squeeze(sum(frac_sev, 2));
        p2_ed(ppe_use, d) = PPE.p2_case_ed_severe .* ...
                            n_ed .* frac_sev(ppe_use);
        clear sev_ED frac_sev
    else
        p2_ed(ppe_use, d) = PPE.p2_case_ed .* ...
                            n_ed;
    end
    if PPE.p2_case_gp_severe > 0
        %% Calculate the proportion of GP presentations that are severe cases,
        %% for each strata.
        frac_sev = sev_new_early_GP ./ (sev_new_early_GP + mld_GP);
        frac_sev(sev_new_early_GP == 0) = 0;
        %% Calculate the net proportion of GP presentations that are severe.
        frac_sev = squeeze(sum(frac_sev, 2));
        p2_gp(ppe_use, d) = PPE.p2_case_gp_severe .* ...
                            n_gp .* frac_sev(ppe_use);
        clear frac_sev
    else
        p2_gp(ppe_use, d) = PPE.p2_case_gp .* ...
                            n_gp;
    end
    if PPE.p2_case_clinic_severe > 0
        %% Calculate the proportion of Clinic presentations that are severe
        %% cases, for each strata.
        sev_Clinic = sev_new_early_Clinic + sev_new_late_Clinic ...
                     + sev_rpt_late_Clinic;
        frac_sev = sev_Clinic ./ (sev_Clinic + mld_Clinic);
        frac_sev(sev_Clinic == 0) = 0;
        %% Calculate the net proportion of Clinic presentations that are
        %% severe.
        frac_sev = squeeze(sum(frac_sev, 2));
        p2_clinic(ppe_use, d) = PPE.p2_case_clinic_severe .* ...
                                n_clinic .* frac_sev(ppe_use);
        clear sev_Clinic frac_sev
    else
        p2_clinic(ppe_use, d) = PPE.p2_case_clinic .* ...
                                n_clinic;
    end
    p2_case(ppe_use, d) = p2_icu(ppe_use, d) ...
                          + p2_ward(ppe_use, d) ...
                          + p2_ed(ppe_use, d) ...
                          + p2_gp(ppe_use, d) ...
                          + p2_clinic(ppe_use, d);

    %% Record the cumulative background consumption in each setting.
    ppe_bg_ph_locn(ppe_use, 1) = ppe_bg_ph_locn(ppe_use, 1) ...
                                 + PPE.daily_bg_ICU;
    ppe_bg_ph_locn(ppe_use, 2) = ppe_bg_ph_locn(ppe_use, 2) ...
                                 + PPE.daily_bg_Ward;
    ppe_bg_ph_locn(ppe_use, 3) = ppe_bg_ph_locn(ppe_use, 3) ...
                                 + PPE.daily_bg_ED;
    ppe_bg_ph_locn(ppe_use, 4) = ppe_bg_ph_locn(ppe_use, 4) ...
                                 + PPE.daily_bg_GP;
    ppe_bg_ph_locn(ppe_use, 5) = ppe_bg_ph_locn(ppe_use, 5) ...
                                 + PPE.daily_bg_Clinic;

    %% Record the cumulative per-patient consumption in each setting.
    ppe_case_ph_locn(ppe_use, 1) = ppe_case_ph_locn(ppe_use, 1) + ...
                                   PPE.daily_case_ICU ...
                                   .* n_icu;
    ppe_case_ph_locn(ppe_use, 2) = ppe_case_ph_locn(ppe_use, 2) + ...
                                   PPE.daily_case_Ward ...
                                   .* n_ward;
    ppe_case_ph_locn(ppe_use, 3) = ppe_case_ph_locn(ppe_use, 3) + ...
                                   PPE.daily_case_ED ...
                                   .* n_ed;
    ppe_case_ph_locn(ppe_use, 4) = ppe_case_ph_locn(ppe_use, 4) + ...
                                   PPE.daily_case_GP ...
                                   .* n_gp;
    ppe_case_ph_locn(ppe_use, 5) = ppe_case_ph_locn(ppe_use, 5) + ...
                                   PPE.daily_case_Clinic ...
                                   .* n_clinic;
  end

  %% Compare variables before and after the daily loop, to ensure that:
  %% 1. No new variables are created, except those listed in "ignore"; and
  %% 2. No existing variables have changed in size.
  S1 = whos();
  for ix = 1:length(S1)
    vname = S1(ix).name;

    ignore = {'S0', 'd', 's', 'x', 'moc_ixs', 'n_icu', 'n_ward', 'n_ed', ...
              'n_gp', 'n_clinic', 'p', 'mask', 'pmask', 'nmask'};
    if any(strcmp(vname, ignore))
      continue
    end

    vsize = S1(ix).size;
    ssize = sprintf(repmat('%dx', [1, length(vsize)]), vsize);
    ssize = ssize(1:end - 1);
    match = strcmp(vname, {S0.name});
    if ~ any(match)
      fprintf('New variable "%s" with size %s\n', vname, ssize);
    elseif sum(match) == 1
      osize = S0(match).size;
      if any(vsize ~= osize)
        osize = sprintf(repmat('%dx', [1, length(osize)]), osize);
        osize = osize(1:end - 1);
        fprintf('Variable "%s" changed from %s to %s\n', ...
                vname, osize, ssize);
      end
    else
      fprintf('Odd, multiple matches for "%s" ...\n', vname);
    end
  end

  %% NOTE: now that we've calculated the daily number of severe cases that are
  %% presenting (but not presenting early with mild symptoms) we can calculate
  %% the true demand for ward and ICU beds, as opposed to req_ward and req_icu
  %% that reflect the bed demand amongst *triaged cases*.
  true_req_icu = req_hosp .* reshape(moc.ward_to_ICU, [1 size(moc.ward_to_ICU)]);
  true_req_ward = req_hosp - true_req_icu;
  %% Calculate net daily demand (i.e., sum over all strata).
  daily_true_req_icu = squeeze(sum(true_req_icu, 2));
  daily_true_req_ward = squeeze(sum(true_req_ward, 2));
  %% Identify the peak in net (true) daily demand.
  peak_true_req_icu = max(daily_true_req_icu, [], 2);
  peak_true_req_ward = max(daily_true_req_ward, [], 2);

  %% NOTE: calculate proportion of true_req_icu that are admitted to ICUs.
  true_want_icu = sum(sum(true_req_icu, 3), 2);
  net_admit_icu = sum(sum(admit_icu, 3), 2);
  icu_admit_frac = net_admit_icu ./ true_want_icu;

  %% Similarly, calculate the peak in net (true) daily demand for EDs and GPs
  true_req_ed = admit_ed + excess_ed;
  true_req_gp = admit_gp + excess_gp;
  daily_true_req_ed = squeeze(sum(true_req_ed, 2));
  daily_true_req_gp = squeeze(sum(true_req_gp, 2));
  peak_true_req_ed = max(daily_true_req_ed, [], 2);
  peak_true_req_gp = max(daily_true_req_gp, [], 2);

  %% Calculate daily ICU and ward bed demand, relative to capacity.
  %%
  %% NOTE: this currently reports *incidence*, not *prevalence*.
  %%
  %% So each excess admission only counts towards the demand *that day*, and
  %% not to the demand over subsequent days when they would have still
  %% occupied a bed, had they been admitted.
  %%
  %% This is consistent with the calculation of peak demand in each setting.
  %%
  %% 1. Calculate ICU and ward bed occupancy.
  daily_icu_demand = cap_icu - avail_icu;
  daily_ward_demand = cap_ward - avail_ward;
  %% 2a. Where there is excess demand, set occupancy to 100% of capacity, even
  %%     if true occupancy is less than 100% (due to ED bed-block preventing
  %%     new admissions).
  daily_icu_excess = squeeze(sum(excess_icu, 2));
  daily_icu_demand(daily_icu_excess > 0) = moc.cap_ICU;
  %% 2b. Add excess demand to ICU bed occupancy.
  for dt = 0:0  % (moc.LoS_ICU - 1)
      daily_icu_demand(:, 1 + dt:num_days) = daily_icu_demand(:, 1 + dt:num_days) ...
                                             + daily_icu_excess(:, 1:(num_days - dt));
  end
  %% 3a. Where there is excess demand, set occupancy to 100% of capacity, even
  %%     if true occupancy is less than 100% (due to ED bed-block preventing
  %%     new admissions).
  daily_ward_excess = squeeze(sum(excess_ward, 2));
  daily_ward_demand(daily_ward_excess > 0) = moc.cap_Ward;
  %% 3b. Add excess demand to Ward bed occupancy.
  for dt = 0:0  % (moc.LoS_Ward - 1)
      daily_ward_demand(:, 1 + dt:num_days) = daily_ward_demand(:, 1 + dt:num_days) ...
                                             + daily_ward_excess(:, 1:(num_days - dt));
  end

  %% Record outcomes of interest.
  out = struct();
  out.strata_deaths = sum(deaths, 3);
  out.total_deaths = sum(out.strata_deaths, 2);
  out.strata_excess_icu = sum(excess_icu, 3);
  out.strata_excess_ward = sum(excess_ward, 3);
  out.strata_excess_ed = sum(excess_ed, 3);
  out.strata_excess_clinic = sum(excess_clinic, 3);
  out.strata_excess_gp = sum(excess_gp, 3);
  out.daily_icu_excess = squeeze(sum(excess_icu, 2));
  out.daily_ward_excess = squeeze(sum(excess_ward, 2));
  out.daily_ed_excess = squeeze(sum(excess_ed, 2));
  out.daily_clinic_excess = squeeze(sum(excess_clinic, 2));
  out.daily_gp_excess = squeeze(sum(excess_gp, 2));
  out.daily_icu_demand = daily_icu_demand * (100 / moc.cap_ICU);
  out.daily_ward_demand = daily_ward_demand * (100 / moc.cap_Ward);
  out.daily_ed_demand = squeeze(sum(admit_ed + excess_ed, 2)) * (100 / moc.cap_ED);
  out.daily_clinic_demand = squeeze(sum(admit_clinic + excess_clinic, 2)) * (100 / moc.cap_Clinic);
  if moc.cap_Clinic == 0
      out.daily_clinic_demand(:) = 0;
  end
  out.daily_gp_demand = squeeze(sum(admit_gp + excess_gp, 2)) * (100 / moc.cap_GP);
  out.net_icu_excess = squeeze(sum(out.daily_icu_excess, 2));
  out.net_ward_excess = squeeze(sum(out.daily_ward_excess, 2));
  out.net_ed_excess = squeeze(sum(out.daily_ed_excess, 2));
  out.net_clinic_excess = squeeze(sum(out.daily_clinic_excess, 2));
  out.net_gp_excess = squeeze(sum(out.daily_gp_excess, 2));
  out.peak_icu_excess = max(out.daily_icu_excess, [], 2);
  out.peak_ward_excess = max(out.daily_ward_excess, [], 2);
  out.peak_ed_excess = max(out.daily_ed_excess, [], 2);
  out.peak_clinic_excess = max(out.daily_clinic_excess, [], 2);
  out.peak_gp_excess = max(out.daily_gp_excess, [], 2);
  out.icu_excess_durn = sum(out.daily_icu_excess > 0, 2);
  out.ward_excess_durn = sum(out.daily_ward_excess > 0, 2);
  out.ed_excess_durn = sum(out.daily_ed_excess > 0, 2);
  out.clinic_excess_durn = sum(out.daily_clinic_excess > 0, 2);
  out.gp_excess_durn = sum(out.daily_gp_excess > 0, 2);
  out.daily_icu = cap_icu - avail_icu;
  out.daily_ward = cap_ward - avail_ward;
  out.daily_ed = cap_ed - avail_ed;
  out.daily_clinic = cap_clinic - avail_clinic;
  out.daily_gp = cap_gp - avail_gp;
  out.peak_icu = max(out.daily_icu, [], 2);
  out.peak_ward = max(out.daily_ward, [], 2);
  out.peak_ed = max(out.daily_ed, [], 2);
  out.peak_clinic = max(out.daily_clinic, [], 2);
  out.peak_gp = max(out.daily_gp, [], 2);
  out.strata_icu = sum(admit_icu, 3);
  out.strata_ward = sum(admit_ward, 3);
  out.strata_ed = sum(admit_ed, 3);
  out.strata_clinic = sum(admit_clinic, 3);
  out.strata_gp = sum(admit_gp, 3);
  out.total_icu = sum(out.strata_icu, 2);
  out.total_ward = sum(out.strata_ward, 2);
  out.total_ed = sum(out.strata_ed, 2);
  out.total_clinic = sum(out.strata_clinic, 2);
  out.total_gp = sum(out.strata_gp, 2);
  out.want_hosp = sum(sum(req_hosp, 3), 2);
  out.want_icu = sum(sum(req_icu, 3), 2);
  out.want_ward = sum(sum(req_ward, 3), 2);
  out.true_want_icu = sum(sum(true_req_icu, 3), 2);
  out.true_want_ward = sum(sum(true_req_ward, 3), 2);
  out.true_strata_want_icu = sum(true_req_icu, 3);
  out.true_strata_want_ward = sum(true_req_ward, 3);
  out.peak_true_req_icu = peak_true_req_icu;
  out.peak_true_req_ward = peak_true_req_ward;
  out.peak_true_req_ed = peak_true_req_ed;
  out.peak_true_req_gp = peak_true_req_gp;
  out.icu_admit_frac = icu_admit_frac;

  %% PPE (surgical mask) usage.
  out.ppe_bg = sum(ppe_bg, 2);
  out.ppe_case = sum(ppe_case, 2);
  out.ppe_total = out.ppe_bg + out.ppe_case;
  out.ppe_icu = sum(ppe_icu, 2);
  out.ppe_ward = sum(ppe_ward, 2);
  out.ppe_ed = sum(ppe_ed, 2);
  out.ppe_gp = sum(ppe_gp, 2);
  out.ppe_clinic = sum(ppe_clinic, 2);

  %% P2 mask usage.
  out.p2_total = sum(p2_case, 2);
  out.p2_icu = sum(p2_icu, 2);
  out.p2_ward = sum(p2_ward, 2);
  out.p2_ed = sum(p2_ed, 2);
  out.p2_gp = sum(p2_gp, 2);
  out.p2_clinic = sum(p2_clinic, 2);

  %% NOTE: calculate surgical mask and P2 mask usage over 4-week intervals,
  %% and report as a percentage of the net mask usage.
  ppe_net = ppe_bg + ppe_case;
  denom = sum(ppe_net, 2);
  out.ppe_4wk_1 = sum(ppe_net(:, 0*28+1:1*28), 2) * 100 ./ denom;
  out.ppe_4wk_2 = sum(ppe_net(:, 1*28+1:2*28), 2) * 100 ./ denom;
  out.ppe_4wk_3 = sum(ppe_net(:, 2*28+1:3*28), 2) * 100 ./ denom;
  out.ppe_4wk_4 = sum(ppe_net(:, 3*28+1:4*28), 2) * 100 ./ denom;
  out.ppe_4wk_5 = sum(ppe_net(:, 4*28+1:5*28), 2) * 100 ./ denom;
  out.ppe_4wk_6 = sum(ppe_net(:, 5*28+1:6*28), 2) * 100 ./ denom;
  out.ppe_4wk_7 = sum(ppe_net(:, 6*28+1:7*28), 2) * 100 ./ denom;
  out.ppe_4wk_8 = sum(ppe_net(:, 7*28+1:8*28), 2) * 100 ./ denom;
  out.ppe_4wk_9 = sum(ppe_net(:, 8*28+1:9*28), 2) * 100 ./ denom;
  out.ppe_4wk_10 = sum(ppe_net(:, 9*28+1:10*28), 2) * 100 ./ denom;
  out.ppe_4wk_11 = sum(ppe_net(:, 10*28+1:11*28), 2) * 100 ./ denom;
  out.ppe_4wk_12 = sum(ppe_net(:, 11*28+1:12*28), 2) * 100 ./ denom;
  out.ppe_4wk_13 = sum(ppe_net(:, 12*28+1:13*28), 2) * 100 ./ denom;

  denom = sum(p2_case, 2);
  out.p2_4wk_1 = sum(p2_case(:, 0*28+1:1*28), 2) * 100 ./ denom;
  out.p2_4wk_2 = sum(p2_case(:, 1*28+1:2*28), 2) * 100 ./ denom;
  out.p2_4wk_3 = sum(p2_case(:, 2*28+1:3*28), 2) * 100 ./ denom;
  out.p2_4wk_4 = sum(p2_case(:, 3*28+1:4*28), 2) * 100 ./ denom;
  out.p2_4wk_5 = sum(p2_case(:, 4*28+1:5*28), 2) * 100 ./ denom;
  out.p2_4wk_6 = sum(p2_case(:, 5*28+1:6*28), 2) * 100 ./ denom;
  out.p2_4wk_7 = sum(p2_case(:, 6*28+1:7*28), 2) * 100 ./ denom;
  out.p2_4wk_8 = sum(p2_case(:, 7*28+1:8*28), 2) * 100 ./ denom;
  out.p2_4wk_9 = sum(p2_case(:, 8*28+1:9*28), 2) * 100 ./ denom;
  out.p2_4wk_10 = sum(p2_case(:, 9*28+1:10*28), 2) * 100 ./ denom;
  out.p2_4wk_11 = sum(p2_case(:, 10*28+1:11*28), 2) * 100 ./ denom;
  out.p2_4wk_12 = sum(p2_case(:, 11*28+1:12*28), 2) * 100 ./ denom;
  out.p2_4wk_13 = sum(p2_case(:, 12*28+1:13*28), 2) * 100 ./ denom;

  %% additional outputs of unprocessed data
  out.deaths = deaths;

  out.excess_icu = excess_icu;
  out.excess_ward = excess_ward;
  out.excess_ed = excess_ed;
  out.excess_clinic = excess_clinic;
  out.excess_gp = excess_gp;

  out.admit_icu = admit_icu;
  out.admit_ward = admit_ward;
  out.admit_ed = admit_ed;
  out.admit_clinic = admit_clinic;
  out.admit_gp = admit_gp;

  out.avail_icu = avail_icu;
  out.avail_ward = avail_ward;
  out.avail_ed = avail_ed;
  out.avail_clinic = avail_clinic;
  out.avail_gp = avail_gp;
end
