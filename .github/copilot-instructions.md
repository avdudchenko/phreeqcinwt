# Project Guidelines

## Overview

phreeqcinwt is a Python wrapper around PHREEQC (via `phreeqpy`) for aqueous geochemistry modeling in water treatment applications. It provides a dict-driven API for simulating water chemistry, predicting mineral scaling, and calculating solution properties.

## Code Style

- **Formatter**: Black 24.8.0 — all code must pass `black --check .`
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes (note: existing classes like `phreeqcWTapi` and `dataBaseManagment` use non-standard casing — follow existing patterns when modifying those classes)
- **Private methods**: Prefix with `_` (e.g., `_get_solution_comp()`)
- **Data interchange**: Use dicts with `{"value": X, "units": "..."}` structure for API outputs

## Architecture

The main class `phreeqcWTapi` in `src/phreeqcinwt/phreeqc_wt_api.py` uses **mixin inheritance**:

| Mixin | File | Purpose |
|-------|------|---------|
| `dataBaseManagment` | `core/data_base_utils.py` | Database loading, metadata management |
| `utilities` | `core/utility_functions.py` | Ion lookup, solution management, logging |
| `reaction_utils` | `core/reaction_utils.py` | Evaporation, pH adjust, mixing, reactions |
| `solution_utils` | `core/solution_state_utils.py` | Extract state: activities, osmotic pressure, scaling |

Database metadata lives in `databases/metadata/` as YAML files. Reactant definitions are in `databases/defined_reactants.yaml`.

## Build and Test

- **Python**: 3.10–3.13
- **Install (dev)**: `conda env create -f phreeqcinwt.yml && pip install -e .`
- **Install (pip)**: `pip install git+<repo_url>`
- **Build system**: setuptools + setuptools_scm (version from git tags)
- **Test**: `pytest --pyargs phreeqcinwt`
- **Format check**: `black --check .`
- **Dependencies**: `numpy`, `pyyaml`, `molmass`, `phreeqpy`

## Conventions

- PHREEQC commands are built as strings and executed via `run_string()` with optional command logging (`self.command_log`)
- Input compositions accept both scalar values and dicts with `value`/`formula`/`mw` keys
- The project targets **Windows** primarily (PHREEQC COM DLL); Linux/Mac support is aspirational
- Example scripts in `examples/` serve as informal integration tests
- Keep YAML metadata files in sync when modifying database handling logic
