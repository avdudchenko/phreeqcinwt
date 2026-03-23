"""Generate reference JSON test data for each supported database."""

import json
import os
import sys

from phreeqcinwt.phreeqc_wt_api import phreeqcWTapi

# Standard brackish water composition from simple_ph_adjust example
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


def make_serializable(obj):
    """Recursively convert numpy types to native Python types."""
    import numpy as np

    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(v) for v in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


SECOND_COMPOSITION = {
    "Na": 5.0,
    "K": 0.009,
    "Cl": 7.0,
    "Ca": 0.258,
    "Mg": 0.090,
    "HCO3": 0.770,
    "SO4": 1.011,
}

FORM_PHASES_LIST = ["Calcite", "Gypsum", "Aragonite"]


def _db_stem(db_name):
    return db_name.replace(".dat", "").replace(".", "_")


def _write_json(out_dir, name, data):
    path = os.path.join(out_dir, name)
    with open(path, "w") as f:
        json.dump(make_serializable(data), f, indent=2)
    print(f"  -> {path}")


def generate():
    out_dir = os.path.join(os.path.dirname(__file__), "test_data")
    os.makedirs(out_dir, exist_ok=True)

    for db in DATABASES:
        stem = _db_stem(db)
        print(f"Generating for {db}...")

        # --- build_water_composition ---
        wt = phreeqcWTapi(database=db)
        result = wt.build_water_composition(
            input_composition=INPUT_COMPOSITION.copy(),
            **BUILD_KWARGS,
        )
        _write_json(out_dir, f"{stem}_solution.json", result)

        # --- perform_reaction (pH adjust) ---
        wt2 = phreeqcWTapi(database=db)
        wt2.build_water_composition(
            input_composition=INPUT_COMPOSITION.copy(),
            **BUILD_KWARGS,
        )
        rx = wt2.perform_reaction(ph_adjust={"pH": 5.0, "reactant": "HCl"}, pressure=1)
        state_after_rx = wt2.get_solution_state()
        _write_json(
            out_dir,
            f"{stem}_reaction.json",
            {"reaction": rx, "solution_state_after": state_after_rx["solution_state"]},
        )

        # --- form_phases ---
        wt3 = phreeqcWTapi(database=db)
        wt3.build_water_composition(
            input_composition=INPUT_COMPOSITION.copy(),
            **BUILD_KWARGS,
        )
        fp = wt3.form_phases(phases=FORM_PHASES_LIST)
        _write_json(out_dir, f"{stem}_form_phases.json", fp)

        # --- get_vapor_pressure ---
        wt_vp = phreeqcWTapi(database=db)
        wt_vp.build_water_composition(
            input_composition=INPUT_COMPOSITION.copy(),
            **BUILD_KWARGS,
        )
        vp = wt_vp.get_vapor_pressure()
        _write_json(out_dir, f"{stem}_vapor_pressure.json", vp)

        # --- mix_solutions ---
        wt4 = phreeqcWTapi(database=db)
        wt4.build_water_composition(
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
        wt4.build_water_composition(
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
        wt4.mix_solutions({1: 1, 2: 1}, new_solution_number=3)
        mix_state = wt4.get_solution_state()
        _write_json(out_dir, f"{stem}_mix.json", mix_state)

    print("Done.")


if __name__ == "__main__":
    generate()
