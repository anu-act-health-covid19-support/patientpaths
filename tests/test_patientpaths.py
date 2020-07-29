import numpy as np
from hypothesis import given, strategies as st
from hypothesis.extra import numpy as npst

import patientpaths
from patientpaths.model_of_care import JURISTICTIONS, MOC_NAMES, Jurisdiction

days = st.shared(st.integers(1, 10))
strata = st.shared(st.integers(1, 3))
daily_incidences = npst.arrays(
    dtype=np.int32, shape=st.tuples(strata, days), elements=st.integers(0, 10_000)
)


@given(
    moc_name=st.sampled_from(MOC_NAMES),
    # TODO: remove `if` clause after adding other juristictions data
    jurisdiction=st.sampled_from([j.name for j in JURISTICTIONS if j.name == "ACT"])
    | st.builds(
        Jurisdiction,
        name=st.just("<generated place>"),
        population=st.integers(1, 20_000_000),
        cap_ICU=st.integers(1, 1_000),
        cap_Ward=st.integers(1, 10_000),
        cap_ED=st.integers(1, 10_000),
        cap_GP=st.integers(1, 10_000),
    ),
    di_mild=daily_incidences,
    di_sev=daily_incidences,
    # "risk" quantised to boolean `x>1` or not, so don't waste any entropy here
    risk=npst.arrays(dtype=np.uint8, shape=strata, elements=st.integers(1, 2)),
)
def test_conservation_laws(moc_name, jurisdiction, di_mild, di_sev, risk):
    """Check that the total population is moved between states but never changed."""
    moc = patientpaths.model_of_care.model_of_care(moc_name, jurisdiction)
    patientpaths.outcomes_for_moc(moc, di_mild, di_sev, risk)
    # TODO: add assertions about results, in addition to calling the code
