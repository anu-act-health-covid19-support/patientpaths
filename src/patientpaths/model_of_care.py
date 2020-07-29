# MODEL_OF_CARE(moc_name, jurisdiction)
#
# Returns the model of care parameters that characterise each healthcare
# setting, for the given model of care ('default', 'cohort', 'clinics',
# 'phone').
#
# By default, this returns national capacities. To use jurisdiction capacities
# specify one of 'ACT', 'NSW', 'NT', 'QLD', 'SA', 'TAS', 'VIC', 'WA'.
#
from math import nan
from types import SimpleNamespace
from typing import NamedTuple


class Jurisdiction(NamedTuple):
    name: str
    population: int
    # TODO: convert to int without default value after filling out table below
    cap_ICU: float = nan
    cap_Ward: float = nan
    cap_ED: float = nan
    cap_GP: float = nan

    @property
    def popn_frac(self):
        return self.population / NATIONAL.population


NATIONAL = Jurisdiction(name="National", population=25_359_700)
JURISTICTIONS = (
    NATIONAL,
    Jurisdiction(
        name="ACT",
        population=426_700,
        cap_ICU=22,
        cap_Ward=448,
        cap_ED=202,
        cap_GP=2607,
    ),
    # Jurisdiction(name="NSW", population=8_089_500),
    # Jurisdiction(name="NT", population=245_900),
    # Jurisdiction(name="QLD", population=5_095_100),
    # Jurisdiction(name="SA", population=1_751_700),
    # Jurisdiction(name="TAS", population=534_300),
    # Jurisdiction(name="VIC", population=6_594_800),
    # Jurisdiction(name="WA", population=2_621_700),
)

MOC_NAMES = ("default", "cohort", "clinics", "phone")


def model_of_care(moc_name, jurisdiction=NATIONAL):
    assert moc_name in MOC_NAMES

    if isinstance(jurisdiction, str):
        by_name = {j.name: j for j in JURISTICTIONS}
        jurisdiction = by_name[jurisdiction]
    assert isinstance(jurisdiction, Jurisdiction)

    # Define the default model of care parameters; no cohorting, no clinics.
    moc = SimpleNamespace(
        model_of_care=moc_name,
        jurisdiction=jurisdiction.name,
        popn_frac=jurisdiction.popn_frac,
        cap_Clinic=0,
        cap_GP=jurisdiction.cap_GP,
        cap_ED=jurisdiction.cap_ED,
        cap_Ward=jurisdiction.cap_Ward,
        cap_ICU=jurisdiction.cap_ICU,
        mild_to_GP=0.8,
        mild_to_ED=0.2,
        mild_to_Clinic=0.1,
        mild_GP_rpt_ED=0.1,
        mild_GP_rpt_Clinic=0.1,
        mild_ED_rpt_GP=0.05,
        mild_Clinic_rpt_GP=0.05,
        sev_frac_early=0.5,
        sev_frac_late=0.5,
        sev_early_to_GP=0.8,
        sev_early_to_ED=0.2,
        sev_early_to_Clinic=0.1,
        sev_late_to_ED=1.0,
        sev_late_to_Clinic=0.05,
        ward_to_ICU=0.125,
        ward_to_ICU_highrisk=0.250,
        ICU_to_death=0.4,
        ICU_to_death_highrisk=0.6,
        LoS_ICU=10,
        LoS_Ward=5,
        lm_ED_cap_W0=0.2,
        lm_ED_cap_E1=0.1,
    )

    # NOTE: lm_ED_cap_W0 and lm_ED_cap_E1 are used to calculate the effective
    # ED consultation capacity, given ward bed utilisation.
    # If ward availability is W0 or higher, the ED effective capacity is 100%.
    # If ward availability is < W0, ED effective capacity decreases linearly
    # from 100% to a minimum of E1.

    if moc_name in ("phone", "clinics"):
        if moc_name == "clinics":
            # NOTE: use 10% of the ED and GP staff, at twice the efficacy.
            moc.cap_Clinic = 2 * 0.1 * (moc.cap_GP + moc.cap_ED)
            moc.cap_GP *= 0.9
            moc.cap_ED *= 0.9
            # Redirect cases that use this service as per the ED rate.
            moc.mild_Clinic_rpt_GP = moc.mild_ED_rpt_GP
        else:
            # Setting phone capacity to population size, ie no cap.
            moc.cap_Clinic = jurisdiction.population
            # Redirect cases that use this service at *TWICE* the ED rate.
            moc.mild_Clinic_rpt_GP = 2.0 * moc.mild_ED_rpt_GP
        # Redirect 25% of mild cases to this service.
        moc.mild_to_Clinic = 0.25
        moc.mild_to_GP *= 0.75
        moc.mild_to_ED *= 0.75
        # Redirect GP cases to this service, as well as to the EDs.
        moc.mild_GP_rpt_ED *= 0.5
        moc.mild_GP_rpt_Clinic = moc.mild_GP_rpt_ED
        # Redirect 25% of early severe cases to this service.
        # Redirect 25% of early severe cases to this service.
        moc.sev_early_to_Clinic = 0.25
        moc.sev_early_to_GP *= 0.75
        moc.sev_early_to_ED *= 0.75
        # Redirect 50% of late severe cases to this service.
        moc.sev_late_to_ED *= 0.5
        moc.sev_late_to_Clinic = moc.sev_late_to_ED

    return moc
