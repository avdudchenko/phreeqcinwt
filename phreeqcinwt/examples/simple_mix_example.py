from phreeqcinwt.phreeqc_wt_api import phreeqcWTapi


if __name__ == "__main__":
    phreeqcWT = phreeqcWTapi(database="pitzer.dat")  # , ignore_phase_list=["Dolomite"])
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

    phreeqcWT.build_water_composition(
        input_composotion=input_composotion,
        charge_balance="Cl",
        pH=7,
        pe=4,
        units="g/kgw",
        pressure=1,
        temperature=20,
        assume_alkalinity=False,
        solution_number=1,
        water_mass=0.75,
    )
    input_composotion = {
        "Na": 0.739 * 50,
        "K": 0.009,
        "Cl": 0.870 * 50,
        "Ca": 0.258,
        "Mg": 0.090,
        "HCO3": 0.385 * 2,
        "SO4": 1.011,
        # "C": 0.258,
        # "C": {"value": 0.385, "compound": "HCO3-"},
        # "Alkalinity": {"value": 0.381, "compound": "HCO3-"},
    }
    phreeqcWT.build_water_composition(
        input_composotion=input_composotion,
        charge_balance="Cl",
        pH=11,
        pe=4,
        units="g/kgw",
        pressure=1,
        temperature=20,
        assume_alkalinity=False,
        solution_number=2,
        water_mass=0.25,
    )
    solutin_dict = {1: 1, 2: 1}
    phreeqcWT.mix_solutions(solutin_dict, new_solution_number=3)
    phreeqcWT.get_solution_state(report=True)
    # titrant_dict = phreeqcWT.perform_reaction(
    #     ph_adjust={"pH": 5.0, "reactant": "HCl"}, pressure=1, report=True
    # )
    # phreeqcWT.get_solution_state(report=True)
    # titrant_dict = phreeqcWT.perform_reaction(
    #     ph_adjust={"pH": 4.5, "reactant": "HCl"}, pressure=1, report=True
    # )
    # # titrant_dict = phreeqcWT.perform_reaction(pressure=100, report=True)
    # # # print(titrant_dict)
    # # titrant_dict = phreeqcWT.perform_reaction(
    # #     ph_adjust={"pH": 7, "reactant": "NaOH"}, report=True
    # # )
    # phreeqcWT.get_solution_state(report=True)
