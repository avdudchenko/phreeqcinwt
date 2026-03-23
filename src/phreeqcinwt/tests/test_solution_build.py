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

BUILD_KWARGS = dict(
    charge_balance="Cl",
    pH=7,
    pe=4,
    units="g/L",
    pressure=1,
    temperature=20,
    assume_alkalinity=False,
)

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


def _load_reference(db_name):
    path = os.path.join(TEST_DATA_DIR, f"{_db_stem(db_name)}_solution.json")
    with open(path) as f:
        return json.load(f)


@pytest.fixture(params=DATABASES, ids=[_db_stem(db) for db in DATABASES])
def solution_result(request):
    """Build a standard brackish-water solution for each database and return (result, reference)."""
    db = request.param
    wt = phreeqcWTapi(database=db)
    result = wt.build_water_composition(
        input_composition=INPUT_COMPOSITION.copy(),
        **BUILD_KWARGS,
    )
    reference = _load_reference(db)
    return result, reference, db


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


def _approx(expected, rel=1e-3):
    """Return a pytest.approx with a default 0.1 % relative tolerance."""
    return pytest.approx(expected, rel=rel)


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
            assert act_val == _approx(ref_val), f"{db}: solution_state[{key}] mismatch"

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
