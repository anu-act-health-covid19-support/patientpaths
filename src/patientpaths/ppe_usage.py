# PPE_USAGE(moc_name, ppe_rec)
#
# Returns the background and per-patient PPE rates in each healthcare setting,
# for the given model of care ('default', 'cohort', 'clinics', 'phone') and
# PPE recommendations ('moderate', 'high').
#
from .Struct import Struct


def ppe_usage(moc_name, ppe_rec):
    NaN = float("NaN")
    # Define the PPE usage as per the moderate-use recommendations.
    if ppe_rec == "moderate":
        ppe_bg_icu = NaN
        if moc_name == "cohort":
            ppe_bg_ward = NaN
        else:
            ppe_bg_ward = NaN
        ppe_bg_ed = NaN  # NOTE: not affected by cohorting.
        ppe_bg_gp = NaN
        if moc_name == "clinics":
            ppe_bg_clinic = NaN
        else:
            ppe_bg_clinic = 0
        ppe_case_icu = NaN
        ppe_case_ward = NaN
        ppe_case_ed = NaN
        ppe_case_gp = NaN
        if moc_name == "clinics":
            ppe_case_clinic = NaN
        else:
            # NOTE: the phone/online model uses the clinic setting to track
            # consultations, but uses no PPE in doing so.
            ppe_case_clinic = 0

        # P2 mask consumption (per-patient only, no overheads).
        p2_case_icu = NaN
        p2_case_ward = NaN
        p2_case_ed = NaN
        p2_case_ed_severe = NaN
        p2_case_gp = NaN
        p2_case_gp_severe = NaN
        if moc_name == "clinics":
            p2_case_clinic = NaN
            p2_case_clinic_severe = NaN
        else:
            p2_case_clinic = 0
            p2_case_clinic_severe = 0

    # Define the PPE usage as per the high-use recommendations.
    elif ppe_rec == "high":
        ppe_bg_icu = NaN
        if moc_name == "cohort":
            ppe_bg_ward = NaN
            ppe_bg_ed = NaN
        else:
            ppe_bg_ward = NaN
            ppe_bg_ed = NaN

        ppe_bg_gp = NaN
        if moc_name == "clinics":
            ppe_bg_clinic = NaN
        else:
            ppe_bg_clinic = 0

        ppe_case_icu = 0  # NOTE: assumption is *all patients* are wearing
        ppe_case_ward = 0  # surgical masks; only need the background rate.
        ppe_case_ed = NaN
        ppe_case_gp = NaN
        if moc_name == "clinics":
            ppe_case_clinic = NaN
        else:
            # NOTE: the phone/online model uses the clinic setting to track
            # consultations, but uses no PPE in doing so.
            ppe_case_clinic = 0

        # P2 mask consumption (per-patient only, no overheads).
        p2_case_icu = NaN
        p2_case_ward = NaN
        p2_case_ed = NaN
        p2_case_ed_severe = NaN
        p2_case_gp = NaN
        p2_case_gp_severe = NaN
        if moc_name == "clinics":
            p2_case_clinic = NaN
            p2_case_clinic_severe = NaN
        else:
            p2_case_clinic = 0
            p2_case_clinic_severe = 0
    else:
        raise Exception("Invalid PPE recommendations: {}.".format(ppe_rec))

    # Return the PPE usage parameters.
    usage = {
        "recommendation": ppe_rec,
        "daily_bg_ICU": ppe_bg_icu,
        "daily_bg_Ward": ppe_bg_ward,
        "daily_bg_ED": ppe_bg_ed,
        "daily_bg_GP": ppe_bg_gp,
        "daily_bg_Clinic": ppe_bg_clinic,
        "daily_case_ICU": ppe_case_icu,
        "daily_case_Ward": ppe_case_ward,
        "daily_case_ED": ppe_case_ed,
        "daily_case_GP": ppe_case_gp,
        "daily_case_Clinic": ppe_case_clinic,
        "p2_case_icu": p2_case_icu,
        "p2_case_ward": p2_case_ward,
        "p2_case_ed": p2_case_ed,
        "p2_case_ed_severe": p2_case_ed_severe,
        "p2_case_gp": p2_case_gp,
        "p2_case_gp_severe": p2_case_gp_severe,
        "p2_case_clinic": p2_case_clinic,
        "p2_case_clinic_severe": p2_case_clinic_severe,
    }
    return Struct(usage)
