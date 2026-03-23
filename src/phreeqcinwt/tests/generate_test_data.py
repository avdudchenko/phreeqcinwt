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


def generate():
    out_dir = os.path.join(os.path.dirname(__file__), "test_data")
    os.makedirs(out_dir, exist_ok=True)

    for db in DATABASES:
        print(f"Generating for {db}...")
        wt = phreeqcWTapi(database=db)
        result = wt.build_water_composition(
            input_composition=INPUT_COMPOSITION.copy(),
            **BUILD_KWARGS,
        )
        result = make_serializable(result)
        db_stem = db.replace(".dat", "").replace(".", "_")
        out_path = os.path.join(out_dir, f"{db_stem}_solution.json")
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"  -> {out_path}")

    print("Done.")


if __name__ == "__main__":
    generate()
