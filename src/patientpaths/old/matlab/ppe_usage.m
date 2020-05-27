%% PPE_USAGE(moc_name, ppe_rec)
%
% Returns the background and per-patient PPE rates in each healthcare setting,
% for the given model of care ('default', 'cohort', 'clinics', 'phone') and
% PPE recommendations ('moderate', 'high').
%
function [usage] = ppe_usage(moc_name, ppe_rec)
  switch ppe_rec

    %% Define the PPE usage as per the moderate-use recommendations.
    case 'moderate'
      ppe_bg_icu = 38304;
      if strcmp(moc_name, 'cohort')
        ppe_bg_ward = 128880;
      else
        ppe_bg_ward = 644352;
      end
      ppe_bg_ed = 6864;  %% NOTE: not affected by cohorting.
      ppe_bg_gp = 78696;
      if strcmp(moc_name, 'clinics')
          ppe_bg_clinic = 6400;
      else
          ppe_bg_clinic = 0;
      end
      ppe_case_icu = 32;
      ppe_case_ward = 50;
      ppe_case_ed = 10.5;
      ppe_case_gp = 2.5;
      if strcmp(moc_name, 'clinics')
          ppe_case_clinic = 2.5;
      else
          %% NOTE: the phone/online model uses the clinic setting to track
          %% consultations, but uses no PPE in doing so.
          ppe_case_clinic = 0;
      end

      %% P2 mask consumption (per-patient only, no overheads).
      p2_case_icu = 14;
      p2_case_ward = 14;
      p2_case_ed = 0;
      p2_case_ed_severe = 3;
      p2_case_gp = 0;
      p2_case_gp_severe = 3;
      if strcmp(moc_name, 'clinics')
          p2_case_clinic = 0;
          p2_case_clinic_severe = 3;
      else
          p2_case_clinic = 0;
          p2_case_clinic_severe = 0;
      end

    %% Define the PPE usage as per the high-use recommendations.
    case 'high'
      ppe_bg_icu = 63360;
      if strcmp(moc_name, 'cohort')
        ppe_bg_ward = 709044;
        ppe_bg_ed = 40848;
      else
        ppe_bg_ward = 3545169;
        ppe_bg_ed = 149392;
      end
      ppe_bg_gp = 484696;
      if strcmp(moc_name, 'clinics')
          ppe_bg_clinic = 6400;
      else
          ppe_bg_clinic = 0;
      end
      ppe_case_icu = 0;   %% NOTE: assumption is *all patients* are wearing
      ppe_case_ward = 0;  %% surgical masks; only need the background rate.
      ppe_case_ed = 4.5;
      ppe_case_gp = 1.5;
      if strcmp(moc_name, 'clinics')
          ppe_case_clinic = 2.5;
      else
          %% NOTE: the phone/online model uses the clinic setting to track
          %% consultations, but uses no PPE in doing so.
          ppe_case_clinic = 0;
      end

      %% P2 mask consumption (per-patient only, no overheads).
      p2_case_icu = 14;
      p2_case_ward = 14;
      p2_case_ed = 5;
      p2_case_ed_severe = 0;
      p2_case_gp = 1;
      p2_case_gp_severe = 0;
      if strcmp(moc_name, 'clinics')
          p2_case_clinic = 1;
          p2_case_clinic_severe = 0;
      else
          p2_case_clinic = 0;
          p2_case_clinic_severe = 0;
      end

    otherwise
      error('Invalid PPE recommendations: "%s".', ppe_rec);
    end

    %% Return the PPE usage parameters.
    usage = struct(...
      'recommendation', ppe_rec, ...
      'daily_bg_ICU', ppe_bg_icu, ...
      'daily_bg_Ward', ppe_bg_ward, ...
      'daily_bg_ED', ppe_bg_ed, ...
      'daily_bg_GP', ppe_bg_gp, ...
      'daily_bg_Clinic', ppe_bg_clinic, ...
      'daily_case_ICU', ppe_case_icu, ...
      'daily_case_Ward', ppe_case_ward, ...
      'daily_case_ED', ppe_case_ed, ...
      'daily_case_GP', ppe_case_gp, ...
      'daily_case_Clinic', ppe_case_clinic, ...
      'p2_case_icu', p2_case_icu, ...
      'p2_case_ward', p2_case_ward, ...
      'p2_case_ed', p2_case_ed, ...
      'p2_case_ed_severe', p2_case_ed_severe, ...
      'p2_case_gp', p2_case_gp, ...
      'p2_case_gp_severe', p2_case_gp_severe, ...
      'p2_case_clinic', p2_case_clinic, ...
      'p2_case_clinic_severe', p2_case_clinic_severe);
end
