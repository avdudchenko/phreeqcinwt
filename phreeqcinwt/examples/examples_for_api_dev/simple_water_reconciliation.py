from phreeqcinwt.phreeqc_wt_api import phreeqcWTapi


if __name__ == "__main__":
    phreeqcWT = phreeqcWTapi(
        database="pitzer.dat",
    )
    # phreeqcWT = phreeqcWTapi(database="phreeqc.dat")
    # phreeqcWT = phreeqcWTapi(database="minteq.v4.dat")
    # basic brackish water
    input_composotion = {
        "Na": 2.41946539,
        "K": 0.0292754431760118,
        "Cl": 2.80474778171597,
        "Ca": 0.887990135,
        "Mg": 0.309680796546278,
        "HCO3": 1.24545247990302,
        "SO4": 3.66288111503226,
        # "C": 0.258,
        # "C": {"value": 0.385, "compound": "HCO3-"},
        # "Alkalinity": {"value": 0.381, "compound": "HCO3-"},
    }
    # This will build solution, and charge balance on Cl

    result = phreeqcWT.build_water_composition(
        input_composotion=input_composotion,
        charge_balance="Cl",
        pH=7,
        pe=0,
        units="g/kgw",
        pressure=4.662126827,
        temperature=20,
        assume_alkalinity=True,
        report=True,
    )
    phreeqcWT.perform_reaction(reactants={"HCl": 500})
    result = phreeqcWT.get_solution_state(report=True)
    ST = result["scaling_tendencies"]
    osmotic_pressure = result["solution_state"]["Osmotic pressure"]
    # this returns fugacities which at low pressures equal to partial pressures
    parital_pressures = phreeqcWT.get_vapor_pressure(report=True)
