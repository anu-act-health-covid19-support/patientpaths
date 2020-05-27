#% MODEL_OF_CARE(moc_name, ppe_rec, jurisdiction)
#
# Returns the model of care parameters that characterise each healthcare
# setting, for the given model of care ('default', 'cohort', 'clinics',
# 'phone') and PPE recommendations ('moderate', 'high').
#
# By default, this returns national capacities. To use jurisdiction capacities
# specify one of 'ACT', 'NSW', 'NT', 'QLD', 'SA', 'TAS', 'VIC', 'WA'.
#
from Struct import Struct
from ppe_usage import ppe_usage
def model_of_care(moc_name, ppe_rec, jurisdiction=None):
  ppe = ppe_usage(moc_name, ppe_rec)
  NaN = float('NaN')

  national_ICU = NaN
  national_Ward = NaN
  national_ED = NaN
  national_GP = NaN

  #% NOTE: define the model of care capacities for the specified jurisdiction.
  if jurisdiction is None:
    #% Default to national capacity.
    jurisdiction = 'National'
    popn_frac = 1.0
    cap_ICU = national_ICU
    cap_Ward = national_Ward
    cap_ED = national_ED
    cap_GP = national_GP
  else:
    if jurisdiction == 'ACT':
      popn_frac = 426.7 / 25359.7
      cap_ICU = 22
      cap_Ward = 448
      cap_ED = 202
      cap_GP = 2607
    elif jurisdiction == 'NSW':
      popn_frac = 8089.5 / 25359.7
      cap_ICU = NaN
      cap_Ward = NaN
      cap_ED = NaN
      cap_GP = NaN
    elif jurisdiction == 'NT':
      popn_frac = 245.9 / 25359.7
      cap_ICU = NaN
      cap_Ward = NaN
      cap_ED = NaN
      cap_GP = NaN
    elif jurisdiction == 'QLD':
      popn_frac = 5095.1 / 25359.7
      cap_ICU = NaN
      cap_Ward = NaN
      cap_ED = NaN
      cap_GP = NaN
    elif jurisdiction == 'SA':
      popn_frac = 1751.7 / 25359.7
      cap_ICU = NaN
      cap_Ward = NaN
      cap_ED = NaN
      cap_GP = NaN
    elif jurisdiction == 'TAS':
      popn_frac = 534.3 / 25359.7
      cap_ICU = NaN
      cap_Ward = NaN
      cap_ED = NaN
      cap_GP = NaN
    elif jurisdiction == 'VIC':
      popn_frac = 6594.8 / 25359.7
      cap_ICU = NaN
      cap_Ward = NaN
      cap_ED = NaN
      cap_GP = NaN
    elif jurisdiction == 'WA':
      popn_frac = 2621.7 / 25359.7
      cap_ICU = NaN
      cap_Ward = NaN
      cap_ED = NaN
      cap_GP = NaN
    else:
      raise Exception('Unknown jurisdiction: {}.'.format(jurisdiction))

    # NOTE: scale the PPE overheads by the capacity fractions.
    ppe.daily_bg_ICU = ppe.daily_bg_ICU * cap_ICU / national_ICU
    ppe.daily_bg_Ward = ppe.daily_bg_Ward * cap_Ward / national_Ward
    ppe.daily_bg_ED = ppe.daily_bg_ED * cap_ED / national_ED
    ppe.daily_bg_GP = ppe.daily_bg_GP * cap_GP / national_GP

  # Define the default model of care parameters; no cohorting, no clinics.
  moc = {
    'model_of_care': moc_name,
    'ppe_usage': ppe,
    'jurisdiction': jurisdiction,
    'popn_frac': popn_frac,
    'cap_Clinic': 0,
    'cap_GP': cap_GP,
    'cap_ED': cap_ED,
    'cap_Ward': cap_Ward,
    'cap_ICU': cap_ICU,
    'mild_to_GP': 0.8,
    'mild_to_ED': 0.2,
    'mild_to_Clinic': 0.0,
    'mild_GP_rpt_ED': 0.1,
    'mild_GP_rpt_Clinic': 0.0,
    'mild_ED_rpt_GP': 0.05,
    'mild_Clinic_rpt_GP': 0.0,
    'sev_frac_early': 0.5,
    'sev_frac_late': 0.5,
    'sev_early_to_GP': 0.8,
    'sev_early_to_ED': 0.2,
    'sev_early_to_Clinic': 0.0,
    'sev_late_to_ED': 1.0,
    'sev_late_to_Clinic': 0.0,
    'ward_to_ICU': 0.125,
    'ward_to_ICU_highrisk': 0.250,
    'ICU_to_death': 0.4,
    'ICU_to_death_highrisk': 0.6,
    'LoS_ICU': 10,
    'LoS_Ward': 5,
    'lm_ED_cap_W0': 0.2,
    'lm_ED_cap_E1': 0.1
  }
  # NOTE: lm_ED_cap_W0 and lm_ED_cap_E1 are used to calculate the effective
  # ED consultation capacity, given ward bed utilisation.
  # If ward availability is W0 or higher, the ED effective capacity is 100%.
  # If ward availability is < W0, ED effective capacity decreases linearly
  # from 100% to a minimum of E1.

  if moc_name == 'default':
    # Nothing more to do.
    pass
  elif moc_name == 'cohort':
    # Nothing more to do, only affects PPE usage.
    pass
  elif moc_name == 'clinics':
    # NOTE: use 10% of the ED and GP staff, at twice the efficacy.
    moc.cap_Clinic = 2 * 0.1 * (moc.cap_GP + moc.cap_ED)
    moc.cap_GP = 0.9 * moc.cap_GP
    moc.cap_ED = 0.9 * moc.cap_ED
    # Reduce background PPE consumption in EDs and GPs accordingly.
    moc.ppe_usage.daily_bg_GP = 0.9 * moc.ppe_usage.daily_bg_GP
    moc.ppe_usage.daily_bg_Ward = 0.9 * moc.ppe_usage.daily_bg_Ward
    # Redirect 25% of mild cases to this service.
    moc.mild_to_Clinic = 0.25
    moc.mild_to_GP = 0.75 * moc.mild_to_GP
    moc.mild_to_ED = 0.75 * moc.mild_to_ED
    # This service will consume PPE; assume that the background rate is
    # *HALF* that of GPs.
    moc.ppe_usage.daily_bg_Clinic = moc.ppe_usage.daily_bg_GP * 0.1 * 0.5
    moc_pp_usage.daily_case_Clinic = moc.ppe_usage.daily_case_GP
    # Redirect cases that use this service as per the ED rate.
    moc.mild_Clinic_rpt_GP = moc.mild_ED_rpt_GP
    # Redirect GP cases to this service, as well as to the EDs.
    moc.mild_GP_rpt_ED = 0.5 * moc.mild_GP_rpt_ED
    moc.mild_GP_rpt_Clinic = moc.mild_GP_rpt_ED
    # Redirect 25% of early severe cases to this service.
    moc.sev_early_to_Clinic = 0.25
    moc.sev_early_to_GP = 0.75 * moc.sev_early_to_GP
    moc.sev_early_to_ED = 0.75 * moc.sev_early_to_ED
    # Redirect 50% of late severe cases to this service.
    moc.sev_late_to_ED = 0.5 * moc.sev_late_to_ED
    moc.sev_late_to_Clinic = moc.sev_late_to_ED
    # NOTE: adjust the jurisdiction overhead consumption.
    ppe.daily_bg_Clinic = ppe.daily_bg_Clinic * (cap_ED + cap_GP) / (national_ED + national_GP)
  elif moc_name == 'phone':
    # NOTE: all-hours phone consultations; does not consume PPE, nor does
    # it affect PPE usage in other settings.
    moc.cap_Clinic = 100000 * moc.popn_frac;
    # Redirect 25% of mild cases to this service.
    moc.mild_to_Clinic = 0.25
    moc.mild_to_GP = 0.75 * moc.mild_to_GP
    moc.mild_to_ED = 0.75 * moc.mild_to_ED
    # Redirect cases that use this service at *TWICE* the ED rate.
    moc.mild_Clinic_rpt_GP = 2.0 * moc.mild_ED_rpt_GP
    # Redirect GP cases to this service, as well as to the EDs.
    moc.mild_GP_rpt_ED = 0.5 * moc.mild_GP_rpt_ED
    moc.mild_GP_rpt_Clinic = moc.mild_GP_rpt_ED
    # Redirect 25% of early severe cases to this service.
    moc.sev_early_to_Clinic = 0.25
    moc.sev_early_to_GP = 0.75 * moc.sev_early_to_GP
    moc.sev_early_to_ED = 0.75 * moc.sev_early_to_ED
    # Redirect 50% of late severe cases to this service.
    moc.sev_late_to_ED = 0.5 * moc.sev_late_to_ED
    moc.sev_late_to_Clinic = moc.sev_late_to_ED
    # NOTE: adjust the jurisdiction overhead consumption.
    ppe.daily_bg_Clinic = ppe.daily_bg_Clinic * moc.popn_frac
  else:
    raise Exception('Unknown model of care: {}.'.format(name))
  return [Struct(moc)]



