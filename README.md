# phreeqcinwt

A Python wrapper around [PHREEQC](https://www.usgs.gov/software/phreeqc-version-3) (via [phreeqpy](https://www.phreeqpy.com/)) for aqueous geochemistry modeling in water treatment applications.

**Key capabilities:**

- Build water compositions and compute solution properties (density, ionic strength, TDS, conductivity, osmotic pressure)
- Predict mineral scaling tendencies (saturation indices)
- Perform pH adjustment and chemical dosing simulations
- Calculate vapor pressures (gas-phase fugacities)
- Simulate mineral precipitation (form phases)
- Mix solutions at arbitrary ratios
- Directly modify solution composition, temperature, and pressure
- Compare results across multiple thermodynamic databases

## Prerequisites

- **Windows** (PHREEQC COM DLL; Linux SO is included, but MAC is not)
- **Conda** (recommended) or any Python 3.10–3.13 environment

## Installation

### Option A — Conda environment (recommended)

Create a dedicated environment with all dependencies:

```bash
conda env create -f phreeqcinwt.yml
conda activate phreeqcinwt
pip install -e .
```

To update an existing environment:

```bash
conda env update -n phreeqcinwt --file phreeqcinwt.yml
```

Or install into a different conda environment:

```bash
conda env update -n YOUR_ENV --file phreeqcinwt.yml
```

### Option B — pip only

```bash
pip install -e .
```

Dependencies (`numpy`, `pyyaml`, `molmass`, `phreeqpy`) are installed automatically.

## Bundled databases

The following PHREEQC databases are included in `databases/`:

| Database | Description |
|---|---|
| `phreeqc.dat` | Standard PHREEQC database |
| `pitzer.dat` | Pitzer ion-interaction model (high ionic strength) |
| `llnl.dat` | Lawrence Livermore National Laboratory database |
| `minteq.dat` | MINTEQA2 database |
| `minteq.v4.dat` | MINTEQA2 v4 database |
| `wateq4f.dat` | WATEQ4F database |
| `sit.dat` | Specific Ion Interaction Theory |
| `pitzer.dat` | Pitzer model |
| `frezchem.dat` | Cold-region geochemistry |
| `Amm.dat` | Ammonia-focused database |

## Quick start

```python
from phreeqcinwt.phreeqc_wt_api import phreeqcWTapi

# Initialize with a thermodynamic database
wt = phreeqcWTapi(database="phreeqc.dat")

# Define a water composition (values in g/L)
composition = {
    "Na": 0.739,
    "K": 0.009,
    "Ca": 0.258,
    "Mg": 0.090,
    "Cl": 1.109,
    "HCO3": 0.385,
    "SO4": 1.011,
}

# Build the solution
result = wt.build_water_composition(
    input_composition=composition,
    charge_balance="Cl",
    pH=7,
    pe=4,
    units="g/L",
    pressure=1,
    temperature=20,
)

# Inspect the solution state
state = wt.get_solution_state(report=True)
```

### pH adjustment

```python
titrant = wt.perform_reaction(
    ph_adjust={"pH": 5.0, "reactant": "HCl"},
    pressure=1,
    report=True,
)
# titrant["HCl"]["value"] gives the required dose in mg/kgw
```

### Scaling tendencies

Scaling tendencies (saturation indices) are returned automatically in the
`build_water_composition` result:

```python
result["scaling_tendencies"]
# {"Calcite": {"value": 0.46, ...}, "Gypsum": {"value": -0.53, ...}, ...}
```

### Mineral precipitation

```python
precipitated = wt.form_phases(
    phases=["Calcite", "Gypsum", "Aragonite"],
    report=True,
)
# precipitated["Calcite"]["value"] gives moles precipitated per kgw
```

### Vapor pressure

```python
vp = wt.get_vapor_pressure(report=True)
# vp["H2O(g)"]["value"]          -> partial pressure in atm
# vp["total_fugacity"]["value"]   -> total vapor pressure in atm
```

### Mixing solutions

```python
wt = phreeqcWTapi(database="pitzer.dat")

wt.build_water_composition(
    input_composition=water_a,
    charge_balance="Cl", pH=7, pe=4,
    units="g/kgw", pressure=1, temperature=20,
    solution_number=1, water_mass=0.75,
)
wt.build_water_composition(
    input_composition=water_b,
    charge_balance="Cl", pH=8, pe=4,
    units="g/kgw", pressure=1, temperature=20,
    solution_number=2, water_mass=0.25,
)

wt.mix_solutions({1: 1, 2: 1}, new_solution_number=3)
mixed_state = wt.get_solution_state(report=True)
```

### Modifying a solution

Directly manipulate an existing solution's elemental totals (in moles),
temperature, or pressure using PHREEQC's `SOLUTION_MODIFY`:

```python
# Absolute: set Na to exactly 0.05 mol and change temperature to 40 °C
result = wt.solution_modify(absolute={"Na": 0.05}, temperature=40)

# Relative: add 0.01 mol Ca to the current amount
result = wt.solution_modify(relative={"Ca": 0.01})

# Both at once
result = wt.solution_modify(
    absolute={"Na": 0.05},
    relative={"Ca": 0.01},
    pressure=2,
)
```

## Testing

```bash
pytest --pyargs phreeqcinwt
```

## Additional examples

See the `examples/` directory for more usage patterns including treatment trains,
database comparisons, density calculations, and osmotic pressure estimation.