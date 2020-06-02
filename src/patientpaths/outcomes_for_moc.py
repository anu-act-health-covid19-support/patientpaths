# OUTCOMES_FOR_MOC
import numpy as np

from .components import allocate, allocate_duration
from .Presentation_Matrix import Presentation_Matrix


def outcomes_for_moc(moc, di_mild, di_sev, risk):
    # Define dimensions that affect variable sizes.
    num_strata = di_mild.shape[0]
    num_days = di_mild.shape[1]

    # Identify cohorts with increased risk of ICU admission and death.
    frac_ward_to_ICU = moc.ward_to_ICU * np.ones([num_strata])
    frac_ward_to_ICU[risk > 1] = moc.ward_to_ICU_highrisk
    frac_ICU_to_death = moc.ICU_to_death * np.ones([num_strata])
    frac_ICU_to_death[risk > 1] = moc.ICU_to_death_highrisk
    # Halve the survival rate for cases that require ICU admission but cannot
    # be admitted into an ICU.
    frac_noICU_to_death = 1 - 0.5 * (1 - frac_ICU_to_death)
    # misc stuff
    frac_ward_avail = 1
    avail_icu = np.tile(moc.cap_ICU, [num_days])
    avail_ward = np.tile(moc.cap_Ward, [num_days])

    # construct the matrix calculating what presentations appear before the healthsystem
    pres = Presentation_Matrix()
    pres.set_default(np.zeros([num_strata]))
    pres.transition("di_mild", "mld_new_GP", moc.mild_to_GP)
    pres.transition("di_mild", "mld_new_ED", moc.mild_to_ED)
    pres.transition("di_mild", "mld_new_Clinic", moc.mild_to_Clinic)
    pres.transition("mld_new_GP", "mld_rpt_ED", moc.mild_GP_rpt_ED)
    pres.transition("mld_new_GP", "mld_rpt_Clinic", moc.mild_GP_rpt_Clinic)
    pres.transition("mld_new_ED", "mld_rpt_GP", moc.mild_ED_rpt_GP)
    pres.transition("mld_rpt_ED", "mld_rpt_GP", moc.mild_ED_rpt_GP)
    pres.transition("mld_new_Clinic", "mld_rpt_GP", moc.mild_Clinic_rpt_GP)
    pres.transition("mld_rpt_Clinic", "mld_rpt_GP", moc.mild_Clinic_rpt_GP)
    pres.transition("di_sev", "sev_new_early", moc.sev_frac_early)
    pres.transition(
        "di_sev", "sev_new_early_GP", moc.sev_frac_early * moc.sev_early_to_GP
    )
    pres.transition(
        "di_sev", "sev_new_early_ED", moc.sev_frac_early * moc.sev_early_to_ED
    )
    pres.transition(
        "di_sev", "sev_new_early_Clinic", moc.sev_frac_early * moc.sev_early_to_Clinic
    )
    pres.transition("di_sev", "sev_new_late", moc.sev_frac_late)
    pres.transition("di_sev", "sev_new_late_ED", moc.sev_frac_late * moc.sev_late_to_ED)
    pres.transition(
        "di_sev", "sev_new_late_Clinic", moc.sev_frac_late * moc.sev_late_to_Clinic
    )
    pres.transition("sev_new_early", "sev_rpt_late_ED", moc.sev_late_to_ED)

    output_data = {}
    for s in ["deaths","excess_icu","excess_ward","excess_ed_sev","excess_ed_mld","excess_clinic_mld","excess_clinic_sev","excess_gp","admit_icu","admit_ward","admit_ed_sev","admit_ed_mld","admit_clinic_sev","admit_clinic_mld","admit_gp","avail_ed","avail_clinic","avail_gp"]:
        output_data[s] = []

    for d in range(num_days):
        # Daily presentations in each setting. (steps1 and steps1a)
        pres["di_mild"] = di_mild[:, d]
        pres["di_sev"] = di_sev[:, d]
        pres.apply()

        # ED consultation capacity, given ward utilisation. (step2)
        avail_ed = moc.cap_ED * np.minimum(
            moc.lm_ED_cap_E1
            + (1 - moc.lm_ED_cap_E1) * frac_ward_avail / moc.lm_ED_cap_W0,
            1,
        )
        # Hospital admissions -- how many can we admit? (step3)
        admit_clinic_sev, excess_clinic_sev, avail_clinic = allocate(
            num_strata,
            pres["sev_rpt_late_Clinic"] + pres["sev_new_late_Clinic"],
            moc.cap_Clinic,
        )
        admit_ed_sev, excess_ed_sev, avail_ed = allocate(
            num_strata, pres["sev_rpt_late_ED"] + pres["sev_new_late_ED"], moc.cap_ED
        )
        # Hospital admissions -- how many can we put in ICU beds? (step4)
        req_icu = (pres["admit_clinic_sev"] + pres["admit_ed_sev"]) * frac_ward_to_ICU
        try_ward = (pres["admit_clinic_sev"] + pres["admit_ed_sev"]) - req_icu
        admit_icu, excess_icu = allocate_duration(
            num_strata, num_days, avail_icu, d, moc.LoS_ICU, req_icu
        )
        try_ward = try_ward + excess_icu
        deaths = admit_icu * frac_ICU_to_death + excess_icu * frac_noICU_to_death
        # Hospital admissions -- how many can we put in ward beds? (step5)
        admit_ward, excess_ward = allocate_duration(
            num_strata, num_days, avail_ward, d, moc.LoS_Ward, try_ward
        )
        frac_ward_avail = avail_ward[d] / moc.cap_Ward
        # Out-patient presentations and treatment. (step6)
        admit_clinic_mld, excess_clinic_mld, avail_clinic = allocate(
            num_strata, pres["mld_new_Clinic"] + pres["mld_rpt_Clinic"], avail_clinic
        )
        admit_ed_mld, excess_ed_mld, avail_ed = allocate(
            num_strata, pres["mld_new_ED"] + pres["mld_rpt_ED"], avail_ed
        )
        admit_gp, excess_gp, avail_gp = allocate(
            num_strata,
            pres["mld_new_GP"]
            + pres["mld_rpt_GP"]
            + pres["excess_clinic_mld"]
            + pres["excess_clinic_sev"]
            + pres["excess_ed_mld"]
            + pres["excess_ed_sev"],
            moc.cap_GP,
        )

        output_data["deaths"].append(deaths)
        output_data["excess_icu"].append(excess_icu)
        output_data["excess_ward"].append(excess_ward)
        output_data["excess_ed_sev"].append(excess_ed_sev)
        output_data["excess_ed_mld"].append(excess_ed_mld)
        output_data["excess_clinic_mld"].append(excess_clinic_mld)
        output_data["excess_clinic_sev"].append(excess_clinic_sev)
        output_data["excess_gp"].append(excess_gp)
        output_data["admit_icu"].append(admit_icu)
        output_data["admit_ward"].append(admit_ward)
        output_data["admit_ed_sev"].append(admit_ed_sev)
        output_data["admit_ed_mld"].append(admit_ed_mld)
        output_data["admit_clinic_sev"].append(admit_clinic_sev)
        output_data["admit_clinic_mld"].append(admit_clinic_mld)
        output_data["admit_gp"].append(admit_gp)
        output_data["avail_ed"].append(avail_ed)
        output_data["avail_clinic"].append(avail_clinic)
        output_data["avail_gp"].append(avail_gp)
    output_data['avail_icu'] = avail_icu
    output_data['avail_ward'] = avail_ward

    return output_data
