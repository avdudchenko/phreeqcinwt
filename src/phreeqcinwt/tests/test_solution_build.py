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


# ---------------------------------------------------------------------------
# solution_modify helpers
# ---------------------------------------------------------------------------


def _build_base_solution(db):
    """Build a standard solution, call get_solution_state, return (wt, state)."""
    wt = phreeqcWTapi(database=db)
    wt.build_water_composition(
        input_composition=INPUT_COMPOSITION.copy(),
        **BUILD_KWARGS,
    )
    state = wt.get_solution_state()
    return wt, state


@pytest.fixture(params=DATABASES, ids=[_db_stem(db) for db in DATABASES])
def modify_base(request):
    """Provide a ready-to-modify (wt, initial_state, db) tuple."""
    db = request.param
    wt, state = _build_base_solution(db)
    return wt, state, db


class TestSolutionModify:
    """Verify solution_modify for absolute, relative, temperature and pressure changes.

    Compositional changes always pair a cation with an anion so that charge
    neutrality is preserved and PHREEQC can converge even for large steps.
    """

    # -- small charge-balanced steps ----------------------------------------

    def test_absolute_sets_element(self, modify_base):
        """Absolute Na+Cl change should set both totals (charge-balanced)."""
        wt, initial_state, db = modify_base
        elems = initial_state["composition"]["elements"]
        na_before = elems["Na"]["mols"]
        cl_before = elems["Cl"]["mols"]
        delta = na_before * 0.02  # small 2 % bump
        target_na = na_before + delta
        target_cl = cl_before + delta  # Na+ and Cl- are both monovalent
        result = wt.solution_modify(absolute={"Na": target_na, "Cl": target_cl})
        assert result["composition"]["elements"]["Na"]["mols"] == _approx(
            target_na
        ), f"{db}: absolute Na mols mismatch"
        assert result["composition"]["elements"]["Cl"]["mols"] == _approx(
            target_cl
        ), f"{db}: absolute Cl mols mismatch"

    def test_relative_adds_to_element(self, modify_base):
        """Relative Ca+Cl change should add to both totals (charge-balanced)."""
        wt, initial_state, db = modify_base
        elems = initial_state["composition"]["elements"]
        ca_before = elems["Ca"]["mols"]
        cl_before = elems["Cl"]["mols"]
        ca_delta = ca_before * 0.02
        cl_delta = ca_delta * 2  # Ca2+ needs 2 Cl- for balance
        result = wt.solution_modify(relative={"Ca": ca_delta, "Cl": cl_delta})
        assert result["composition"]["elements"]["Ca"]["mols"] == _approx(
            ca_before + ca_delta
        ), f"{db}: relative Ca mols mismatch"
        assert result["composition"]["elements"]["Cl"]["mols"] == _approx(
            cl_before + cl_delta
        ), f"{db}: relative Cl mols mismatch"

    def test_temperature_change(self, modify_base):
        """Temperature should update to the specified value."""
        wt, initial_state, db = modify_base
        new_temp = 50.0
        result = wt.solution_modify(temperature=new_temp)
        assert result["solution_state"]["Temperature"]["value"] == _approx(
            new_temp
        ), f"{db}: temperature mismatch"

    def test_pressure_change(self, modify_base):
        """Pressure should update when specified."""
        wt, initial_state, db = modify_base
        new_pressure = 5.0
        result = wt.solution_modify(pressure=new_pressure)
        assert (
            "solution_state" in result
        ), f"{db}: no solution_state after pressure change"

    def test_combined_absolute_and_relative(self, modify_base):
        """Absolute and relative changes in a single call should both apply."""
        wt, initial_state, db = modify_base
        elems = initial_state["composition"]["elements"]
        # Absolute: set Na to +3 % of current, balance with Cl
        na_before = elems["Na"]["mols"]
        cl_before = elems["Cl"]["mols"]
        na_delta = na_before * 0.03
        target_na = na_before + na_delta
        target_cl = cl_before + na_delta  # monovalent balance
        # Relative: bump Mg, balance with additional Cl
        mg_before = elems["Mg"]["mols"]
        mg_delta = mg_before * 0.02
        cl_extra = mg_delta * 2  # Mg2+ needs 2 Cl-
        result = wt.solution_modify(
            absolute={"Na": target_na, "Cl": target_cl + cl_extra},
            relative={"Mg": mg_delta},
        )
        assert result["composition"]["elements"]["Na"]["mols"] == _approx(
            target_na
        ), f"{db}: combined absolute Na mismatch"
        assert result["composition"]["elements"]["Mg"]["mols"] == _approx(
            mg_before + mg_delta
        ), f"{db}: combined relative Mg mismatch"

    def test_unmodified_elements_unchanged(self, modify_base):
        """Elements not mentioned should remain unchanged."""
        wt, initial_state, db = modify_base
        elems = initial_state["composition"]["elements"]
        ca_before = elems["Ca"]["mols"]
        na_before = elems["Na"]["mols"]
        cl_before = elems["Cl"]["mols"]
        na_delta = na_before * 0.02
        # Charge-balanced Na+Cl bump; Ca should stay the same
        wt.solution_modify(
            absolute={"Na": na_before + na_delta, "Cl": cl_before + na_delta}
        )
        state = wt.get_solution_state()
        assert state["composition"]["elements"]["Ca"]["mols"] == _approx(
            ca_before
        ), f"{db}: Ca should be unchanged"

    # -- large charge-balanced steps ----------------------------------------

    def test_large_absolute_nacl_step(self, modify_base):
        """Large NaCl increase (~50 %) should converge when charge-balanced."""
        wt, initial_state, db = modify_base
        elems = initial_state["composition"]["elements"]
        na_before = elems["Na"]["mols"]
        cl_before = elems["Cl"]["mols"]
        delta = na_before * 0.5  # 50 % increase
        target_na = na_before + delta
        target_cl = cl_before + delta
        result = wt.solution_modify(absolute={"Na": target_na, "Cl": target_cl})
        assert result["composition"]["elements"]["Na"]["mols"] == _approx(
            target_na
        ), f"{db}: large absolute Na mismatch"
        assert result["composition"]["elements"]["Cl"]["mols"] == _approx(
            target_cl
        ), f"{db}: large absolute Cl mismatch"

    def test_large_relative_cacl2_step(self, modify_base):
        """Large CaCl2 increase (~50 %) should converge when charge-balanced."""
        wt, initial_state, db = modify_base
        elems = initial_state["composition"]["elements"]
        ca_before = elems["Ca"]["mols"]
        cl_before = elems["Cl"]["mols"]
        ca_delta = ca_before * 0.5
        cl_delta = ca_delta * 2  # Ca2+ balanced by 2 Cl-
        result = wt.solution_modify(relative={"Ca": ca_delta, "Cl": cl_delta})
        assert result["composition"]["elements"]["Ca"]["mols"] == _approx(
            ca_before + ca_delta
        ), f"{db}: large relative Ca mismatch"
        assert result["composition"]["elements"]["Cl"]["mols"] == _approx(
            cl_before + cl_delta
        ), f"{db}: large relative Cl mismatch"

    def test_large_combined_step(self, modify_base):
        """Large combined Na+Ca+Cl change should converge when charge-balanced."""
        wt, initial_state, db = modify_base
        elems = initial_state["composition"]["elements"]
        na_before = elems["Na"]["mols"]
        ca_before = elems["Ca"]["mols"]
        cl_before = elems["Cl"]["mols"]
        na_delta = na_before * 0.5
        ca_delta = ca_before * 0.3
        # Cl- must absorb: 1*na_delta (for Na+) + 2*ca_delta (for Ca2+)
        cl_delta = na_delta + 2 * ca_delta
        result = wt.solution_modify(
            absolute={
                "Na": na_before + na_delta,
                "Ca": ca_before + ca_delta,
                "Cl": cl_before + cl_delta,
            }
        )
        assert result["composition"]["elements"]["Na"]["mols"] == _approx(
            na_before + na_delta
        ), f"{db}: large combined Na mismatch"
        assert result["composition"]["elements"]["Ca"]["mols"] == _approx(
            ca_before + ca_delta
        ), f"{db}: large combined Ca mismatch"
        assert result["composition"]["elements"]["Cl"]["mols"] == _approx(
            cl_before + cl_delta
        ), f"{db}: large combined Cl mismatch"

    # -- error handling (single-database, no fixture) -----------------------

    def test_relative_without_state_raises(self):
        """Using relative changes without prior get_solution_state should raise."""
        wt = phreeqcWTapi(database="phreeqc.dat")
        wt.build_water_composition(
            input_composition=INPUT_COMPOSITION.copy(),
            **BUILD_KWARGS,
        )
        wt.current_state = None
        with pytest.raises(ValueError, match="No stored solution state"):
            wt.solution_modify(relative={"Na": 0.01})

    def test_negative_result_raises(self):
        """Relative change that would produce negative moles should raise."""
        wt = phreeqcWTapi(database="phreeqc.dat")
        wt.build_water_composition(
            input_composition=INPUT_COMPOSITION.copy(),
            **BUILD_KWARGS,
        )
        wt.get_solution_state()
        with pytest.raises(ValueError, match="negative moles"):
            wt.solution_modify(relative={"Na": -999})
