from phreeqcinwt.phreeqc_wt_api import phreeqcWTapi


if __name__ == "__main__":
    phreeqcWT = phreeqcWTapi(
        database="pitzer.dat",
    )
    # phreeqcWT = phreeqcWTapi(database="phreeqc.dat")
    # phreeqcWT = phreeqcWTapi(database="minteq.v4.dat")
    # basic brackish water
    input_composotion = {
        "Na": 0.739,
        "K": 0.009,
        "Cl": 0.870,
        "Ca": 0.258,
        "Mg": 0.090,
        "HCO3": 0.385,
        "SO4": 1.011,
        # "C": 0.258,
        # "C": {"value": 0.385, "compound": "HCO3-"},
        # "Alkalinity": {"value": 0.381, "compound": "HCO3-"},
    }
    # This will build solution, and charge balance on Cl
    result = phreeqcWT.build_water_composition(
        solution_name="reconciled solution",
        input_composotion=input_composotion,
        charge_balance="Cl",
        pH=7,
        pe=0,
        units="g/L",
        pressure=1,
        temperature=20,
        assume_alkalinity=True,
        report=True,
    )
    for k in [0, 20, 40, 60, 80, 100]:
        # reset state to original solution
        phreeqcWT.load_solution("reconciled solution")
        phreeqcWT.perform_reaction(reactants={"CO2": k})
        # get solution state, this will be before any phases are precipitated out
        result = phreeqcWT.get_solution_state()
        ST = result["scaling_tendencies"]
        osmotic_pressure = result["solution_state"]["Osmotic pressure"]
        # this returns fugacities which at low pressures equal to partial pressures
        parital_pressures = phreeqcWT.get_vapor_pressure(report=True)

        # this will cause solids to form and percipiate out, saving new solution state
        formed_phases = phreeqcWT.form_phases()
        # get solution state after solids formed
        result_post = phreeqcWT.get_solution_state()
        ST_post = result["scaling_tendencies"]
        osmotic_pressure_post = result["solution_state"]["Osmotic pressure"]
        #
        parital_pressures_post = phreeqcWT.get_vapor_pressure(report=True)
