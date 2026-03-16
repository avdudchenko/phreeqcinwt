from phreeqcinwt.phreeqc_wt_api import phreeqcWTapi


if __name__ == "__main__":
    # ignore list can be provided here, but for the example we will use exlude_phase function
    # below
    phreeqcWT = phreeqcWTapi(
        database="pitzer.dat",
        track_phase_list=[
            "Calcite",
            "Gypsum",
            "Anhydrite",
            "Glauberite",
            "Halite",
            "Brucite",
        ],
        ignore_gas_phase_list=["CO2(g)"],
    )
    # phreeqcWT = phreeqcWTapi(database="phreeqc.dat")
    # phreeqcWT = phreeqcWTapi(database="minteq.v4.dat")
    # basic brackish water
    input_composition = {
        "Na": 9.557,
        "K": 0.0903,
        "Cl": 9.0066,
        "Ca": 0.566,
        "Mg": 0.9038,
        "HCO3": 7.4521,
        "SO4": 10.121,
        # "C": 0.258,
        # "C": {"value": 0.385, "compound": "HCO3-"},
        # "Alkalinity": {"value": 0.381, "compound": "HCO3-"},
    }

    phreeqcWT.build_water_composition(
        input_composition=input_composition,
        charge_balance="Cl",
        pH=6.01,
        pe=0,
        units="g/kgw",
        pressure=1,
        temperature=20,
        assume_alkalinity=False,
        water_mass=0.9996,
    )

    print("-----------------------get intial solution state-----------------------")
    phreeqcWT.get_solution_state(report=False)
    print("-----------------------soften water useing soda ash-----------------------")
    phreeqcWT.perform_reaction(
        temperature=90, evaporate_water_mass_percent=95, report=True
    )
    # phreeqcWT.get_solution_state(report=True)
    all_percipitatnts = phreeqcWT.form_phases(report=True)
    vapor_pressure = phreeqcWT.get_vapor_pressure(report=True)
    phreeqcWT.get_solution_state(report=True)
    # phreeqcWT.print_log()
