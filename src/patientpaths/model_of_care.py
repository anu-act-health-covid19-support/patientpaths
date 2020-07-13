# MODEL_OF_CARE(moc_name, jurisdiction)
#
# Returns the model of care parameters that characterise each healthcare
# setting, for the given model of care ('default', 'cohort', 'clinics',
# 'phone').
#
# By default, this returns national capacities. To use jurisdiction capacities
# specify one of 'ACT', 'NSW', 'NT', 'QLD', 'SA', 'TAS', 'VIC', 'WA'.
#
from types import SimpleNamespace

def model_of_care(moc_name, jurisdiction=None):
    NaN = float("NaN")

    national_ICU = NaN
    national_Ward = NaN
    national_ED = NaN
    national_GP = NaN

    # NOTE: define the model of care capacities for the specified jurisdiction.
    if jurisdiction is None:
        # Default to national capacity.
        jurisdiction = "National"
        popn_frac = 1.0
        cap_ICU = national_ICU
        cap_Ward = national_Ward
        cap_ED = national_ED
        cap_GP = national_GP
    else:
        if jurisdiction == "ACT":
            popn_frac = 426.7 / 25359.7
            cap_ICU = 22
            cap_Ward = 448
            cap_ED = 202
            cap_GP = 2607
        elif jurisdiction == "NSW":
            popn_frac = 8089.5 / 25359.7
            cap_ICU = NaN
            cap_Ward = NaN
            cap_ED = NaN
            cap_GP = NaN
        elif jurisdiction == "NT":
            popn_frac = 245.9 / 25359.7
            cap_ICU = NaN
            cap_Ward = NaN
            cap_ED = NaN
            cap_GP = NaN
        elif jurisdiction == "QLD":
            popn_frac = 5095.1 / 25359.7
            cap_ICU = NaN
            cap_Ward = NaN
            cap_ED = NaN
            cap_GP = NaN
        elif jurisdiction == "SA":
            popn_frac = 1751.7 / 25359.7
            cap_ICU = NaN
            cap_Ward = NaN
            cap_ED = NaN
            cap_GP = NaN
        elif jurisdiction == "TAS":
            popn_frac = 534.3 / 25359.7
            cap_ICU = NaN
            cap_Ward = NaN
            cap_ED = NaN
            cap_GP = NaN
        elif jurisdiction == "VIC":
            popn_frac = 6594.8 / 25359.7
            cap_ICU = NaN
            cap_Ward = NaN
            cap_ED = NaN
            cap_GP = NaN
        elif jurisdiction == "WA":
            popn_frac = 2621.7 / 25359.7
            cap_ICU = NaN
            cap_Ward = NaN
            cap_ED = NaN
            cap_GP = NaN
        else:
            raise Exception("Unknown jurisdiction: {}.".format(jurisdiction))

    # Define the default model of care parameters; no cohorting, no clinics.
    moc = SimpleNamespace()

    moc.model_of_care = moc_name
    moc.jurisdiction = jurisdiction
    moc.popn_frac = popn_frac
    moc.cap_Clinic = 0
    moc.cap_GP = cap_GP
    moc.cap_ED = cap_ED
    moc.cap_Ward = cap_Ward
    moc.cap_ICU = cap_ICU
    moc.mild_to_GP = 0.8
    moc.mild_to_ED = 0.2
    moc.mild_to_Clinic = 0.0
    moc.mild_GP_rpt_ED = 0.1
    moc.mild_GP_rpt_Clinic = 0.0
    moc.mild_ED_rpt_GP = 0.05
    moc.mild_Clinic_rpt_GP = 0.0
    moc.sev_frac_early = 0.5
    moc.sev_frac_late = 0.5
    moc.sev_early_to_GP = 0.8
    moc.sev_early_to_ED = 0.2
    moc.sev_early_to_Clinic = 0.0
    moc.sev_late_to_ED = 1.0
    moc.sev_late_to_Clinic = 0.0
    moc.ward_to_ICU = 0.125
    moc.ward_to_ICU_highrisk = 0.250
    moc.ICU_to_death = 0.4
    moc.ICU_to_death_highrisk = 0.6
    moc.LoS_ICU = 10
    moc.LoS_Ward = 5
    moc.lm_ED_cap_W0 = 0.2
    moc.lm_ED_cap_E1 = 0.1

    # NOTE: lm_ED_cap_W0 and lm_ED_cap_E1 are used to calculate the effective
    # ED consultation capacity, given ward bed utilisation.
    # If ward availability is W0 or higher, the ED effective capacity is 100%.
    # If ward availability is < W0, ED effective capacity decreases linearly
    # from 100% to a minimum of E1.

    if moc_name == "default":
        # Nothing more to do.
        pass
    elif moc_name == "cohort":
        # Nothing more to do.
        pass
    elif moc_name == "clinics":
        # NOTE: use 10% of the ED and GP staff, at twice the efficacy.
        moc.cap_Clinic = 2 * 0.1 * (moc.cap_GP + moc.cap_ED)
        moc.cap_GP = 0.9 * moc.cap_GP
        moc.cap_ED = 0.9 * moc.cap_ED
        # Redirect 25% of mild cases to this service.
        moc.mild_to_Clinic = 0.25
        moc.mild_to_GP = 0.75 * moc.mild_to_GP
        moc.mild_to_ED = 0.75 * moc.mild_to_ED
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
    elif moc_name == "phone":
        moc.cap_Clinic = 100000 * moc.popn_frac
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
    else:
        raise NotImplementedError("Unknown model of care")
    return moc
