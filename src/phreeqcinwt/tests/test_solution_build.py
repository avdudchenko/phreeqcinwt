import json
import os

import numpy as np
import pytest

from phreeqcinwt.phreeqc_wt_api import phreeqcWTapi

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")

# Standard brackish water composition (from simple_ph_adjust example)
INPUT_COMPOSITION = {
    "Na": 0.739,
    "K": 0.009,
    "Cl": 1.109231,
    "Ca": 0.258,
    "Mg": 0.090,
    "HCO3": 0.385,
    "SO4": 1.011,
}

# Second composition for mix tests (higher salinity)
SECOND_COMPOSITION = {
    "Na": 5.0,
    "K": 0.009,
    "Cl": 7.0,
    "Ca": 0.258,
    "Mg": 0.090,
    "HCO3": 0.770,
    "SO4": 1.011,
}

BUILD_KWARGS = dict(
    charge_balance="Cl",
    pH=7,
    pe=4,
    units="g/L",
    pressure=1,
    temperature=20,
    assume_alkalinity=False,
)

FORM_PHASES_LIST = ["Calcite", "Gypsum", "Aragonite"]

DATABASES = [
    "phreeqc.dat",
    "pitzer.dat",
    "llnl.dat",
    "minteq.dat",
    "minteq.v4.dat",
    "wateq4f.dat",
]


def _db_stem(db_name):
    return db_name.replace(".dat", "").replace(".", "_")


def _load_reference(db_name, suffix="solution"):
    path = os.path.join(TEST_DATA_DIR, f"{_db_stem(db_name)}_{suffix}.json")
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(params=DATABASES, ids=[_db_stem(db) for db in DATABASES])
def solution_result(request):
    """Build a standard brackish-water solution for each database and return (result, reference, db)."""
    db = request.param
    wt = phreeqcWTapi(database=db)
    result = wt.build_water_composition(
        input_composition=INPUT_COMPOSITION.copy(),
        **BUILD_KWARGS,
    )
    reference = _load_reference(db)
    return result, reference, db


@pytest.fixture(params=DATABASES, ids=[_db_stem(db) for db in DATABASES])
def reaction_result(request):
    """Perform pH adjustment and return (reaction_dict, state_after, reference, db)."""
    db = request.param
    wt = phreeqcWTapi(database=db)
    wt.build_water_composition(
        input_composition=INPUT_COMPOSITION.copy(),
        **BUILD_KWARGS,
    )
    rx = wt.perform_reaction(ph_adjust={"pH": 5.0, "reactant": "HCl"}, pressure=1)
    state_after = wt.get_solution_state()
    reference = _load_reference(db, "reaction")
    return rx, state_after, reference, db


@pytest.fixture(params=DATABASES, ids=[_db_stem(db) for db in DATABASES])
def form_phases_result(request):
    """Precipitate explicit phases and return (result, reference, db)."""
    db = request.param
    wt = phreeqcWTapi(database=db)
    wt.build_water_composition(
        input_composition=INPUT_COMPOSITION.copy(),
        **BUILD_KWARGS,
    )
    fp = wt.form_phases(phases=FORM_PHASES_LIST)
    reference = _load_reference(db, "form_phases")
    return fp, reference, db


@pytest.fixture(params=DATABASES, ids=[_db_stem(db) for db in DATABASES])
def mix_result(request):
    """Mix two solutions and return (state, reference, db)."""
    db = request.param
    wt = phreeqcWTapi(database=db)
    wt.build_water_composition(
        input_composition=INPUT_COMPOSITION.copy(),
        charge_balance="Cl",
        pH=7,
        pe=4,
        units="g/L",
        pressure=1,
        temperature=20,
        assume_alkalinity=False,
        solution_number=1,
        water_mass=0.75,
    )
    wt.build_water_composition(
        input_composition=SECOND_COMPOSITION.copy(),
        charge_balance="Cl",
        pH=8,
        pe=4,
        units="g/L",
        pressure=1,
        temperature=20,
        assume_alkalinity=False,
        solution_number=2,
        water_mass=0.25,
    )
    wt.mix_solutions({1: 1, 2: 1}, new_solution_number=3)
    state = wt.get_solution_state()
    reference = _load_reference(db, "mix")
    return state, reference, db


@pytest.fixture(params=DATABASES, ids=[_db_stem(db) for db in DATABASES])
def vapor_pressure_result(request):
    """Get vapor pressure and return (result, reference, db)."""
    db = request.param
    wt = phreeqcWTapi(database=db)
    wt.build_water_composition(
        input_composition=INPUT_COMPOSITION.copy(),
        **BUILD_KWARGS,
    )
    vp = wt.get_vapor_pressure()
    reference = _load_reference(db, "vapor_pressure")
    return vp, reference, db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SOLUTION_STATE_KEYS = [
    "pH",
    "pe",
    "Temperature",
    "Alkalinity",
    "Charge balance",
    "Error in charge",
    "Water mass",
    "Solution density",
    "Ionic strength",
    "Solution conductivity",
    "Solution volume",
    "Total dissolved solids",
    "Solution mass",
    "Osmotic pressure",
]


# Per-key relative tolerance overrides for cross-platform sensitive quantities
_KEY_REL_TOL = {
    "pe": 5e-2,
}


def _approx(expected, rel=1e-3, abs=1e-8, key=None):
    """Return a pytest.approx with a default 0.1 % relative tolerance
    and a 1e-8 absolute tolerance floor for near-zero values.
    If *key* is provided, look up a per-key override in _KEY_REL_TOL."""
    if key is not None:
        rel = _KEY_REL_TOL.get(key, rel)
    return pytest.approx(expected, rel=rel, abs=abs)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestBuildSolution:
    """Verify that build_water_composition returns the expected results across databases."""

    def test_solution_state(self, solution_result):
        """Solution-state properties should match the stored reference."""
        result, reference, db = solution_result
        for key in SOLUTION_STATE_KEYS:
            ref_val = reference["solution_state"][key]["value"]
            act_val = result["solution_state"][key]["value"]
            assert act_val == _approx(
                ref_val, key=key
            ), f"{db}: solution_state[{key}] mismatch"

    def test_scaling_tendencies(self, solution_result):
        """Scaling tendency values should match the stored reference."""
        result, reference, db = solution_result
        for phase, ref_data in reference["scaling_tendencies"].items():
            assert phase in result["scaling_tendencies"], f"{db}: missing phase {phase}"
            if phase == "max":
                assert (
                    result["scaling_tendencies"]["max"]["scalant"]
                    == ref_data["scalant"]
                ), f"{db}: max scalant mismatch"
                assert result["scaling_tendencies"]["max"]["value"] == _approx(
                    ref_data["value"]
                ), f"{db}: max ST value mismatch"
            else:
                assert result["scaling_tendencies"][phase]["value"] == _approx(
                    ref_data["value"]
                ), f"{db}: ST[{phase}] mismatch"

    def test_composition_elements(self, solution_result):
        """Elemental composition should match the stored reference."""
        result, reference, db = solution_result
        ref_elements = reference["composition"]["elements"]
        act_elements = result["composition"]["elements"]
        for element, ref_data in ref_elements.items():
            assert element in act_elements, f"{db}: missing element {element}"
            assert act_elements[element]["mols"] == _approx(
                ref_data["mols"]
            ), f"{db}: element {element} mols mismatch"


class TestPerformReaction:
    """Verify perform_reaction (pH adjustment with HCl)."""

    def test_target_ph_reached(self, reaction_result):
        """Resulting pH should match the target."""
        rx, state_after, reference, db = reaction_result
        assert rx["pH"]["value"] == _approx(5.0), f"{db}: target pH not reached"

    def test_titrant_amount(self, reaction_result):
        """HCl titrant amount should match reference."""
        rx, state_after, reference, db = reaction_result
        ref_hcl = reference["reaction"]["HCl"]["value"]
        assert rx["HCl"]["value"] == _approx(ref_hcl), f"{db}: HCl amount mismatch"

    def test_solution_state_after_reaction(self, reaction_result):
        """Solution state after reaction should match reference."""
        rx, state_after, reference, db = reaction_result
        for key in SOLUTION_STATE_KEYS:
            ref_val = reference["solution_state_after"][key]["value"]
            act_val = state_after["solution_state"][key]["value"]
            assert act_val == _approx(
                ref_val, key=key
            ), f"{db}: post-reaction solution_state[{key}] mismatch"


class TestFormPhases:
    """Verify form_phases with explicit phase list."""

    def test_expected_phases_returned(self, form_phases_result):
        """All requested phases should be in the result."""
        fp, reference, db = form_phases_result
        for phase in FORM_PHASES_LIST:
            assert phase in fp, f"{db}: missing phase {phase}"

    def test_phase_amounts(self, form_phases_result):
        """Precipitated amounts should match reference."""
        fp, reference, db = form_phases_result
        for phase, ref_data in reference.items():
            ref_val = ref_data["value"]
            act_val = fp[phase]["value"]
            if abs(ref_val) < 1e-12:
                assert abs(act_val) < 1e-10, f"{db}: {phase} expected ~0, got {act_val}"
            else:
                assert act_val == _approx(ref_val), f"{db}: {phase} amount mismatch"


class TestVaporPressure:
    """Verify get_vapor_pressure returns correct fugacities."""

    def test_total_fugacity(self, vapor_pressure_result):
        """Total fugacity should match reference."""
        vp, reference, db = vapor_pressure_result
        assert vp["total_fugacity"]["value"] == _approx(
            reference["total_fugacity"]["value"]
        ), f"{db}: total_fugacity mismatch"

    def test_individual_gas_phases(self, vapor_pressure_result):
        """Each gas-phase fugacity should match reference."""
        vp, reference, db = vapor_pressure_result
        for gas, ref_data in reference.items():
            if gas == "total_fugacity":
                continue
            assert gas in vp, f"{db}: missing gas {gas}"
            ref_val = ref_data["value"]
            act_val = vp[gas]["value"]
            if abs(ref_val) < 1e-12:
                assert abs(act_val) < 1e-10, f"{db}: {gas} expected ~0, got {act_val}"
            else:
                assert act_val == _approx(ref_val), f"{db}: {gas} fugacity mismatch"

    def test_total_equals_sum(self, vapor_pressure_result):
        """Total fugacity should equal the sum of individual gas fugacities."""
        vp, reference, db = vapor_pressure_result
        individual_sum = sum(v["value"] for k, v in vp.items() if k != "total_fugacity")
        assert individual_sum == _approx(
            vp["total_fugacity"]["value"]
        ), f"{db}: total_fugacity != sum of individual fugacities"


class TestMixSolutions:
    """Verify mix_solutions produces correct mixed state."""

    def test_mixed_solution_state(self, mix_result):
        """Solution state after mixing should match reference."""
        state, reference, db = mix_result
        for key in SOLUTION_STATE_KEYS:
            ref_val = reference["solution_state"][key]["value"]
            act_val = state["solution_state"][key]["value"]
            assert act_val == _approx(
                ref_val, key=key
            ), f"{db}: mixed solution_state[{key}] mismatch"

    def test_mixed_composition_elements(self, mix_result):
        """Elemental composition after mixing should match reference."""
        state, reference, db = mix_result
        ref_elements = reference["composition"]["elements"]
        act_elements = state["composition"]["elements"]
        for element, ref_data in ref_elements.items():
            assert element in act_elements, f"{db}: missing element {element}"
            assert act_elements[element]["mols"] == _approx(
                ref_data["mols"]
            ), f"{db}: mixed element {element} mols mismatch"
