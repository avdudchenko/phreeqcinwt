from phreeqcinwt.phreeqc_wt_api import phreeqcWTapi


if __name__ == "__main__":
    phreeqcWT = phreeqcWTapi(
        database="pitzer.dat",
        ignore_phase_list=[
            "Dolomite",
            "Magnesite",
            "Huntite",
            "Goergeyite",
            "CO2(g)",
            "H2O(g)",
        ],
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

    phreeqcWT.build_water_composition(
        input_composotion=input_composotion,
        charge_balance="Cl",
        pH=7,
        pe=0,
        units="g/kgw",
        pressure=1,
        temperature=20,
        assume_alkalinity=True,
    )

    print("-----------------------get intial solution state-----------------------")
    phreeqcWT.get_solution_state(report=True)
    print("-----------------------soften water useing soda ash-----------------------")
    phreeqcWT.perform_reaction(reactants={"Na2CO3": 550}, report=True)
    # phreeqcWT.get_solution_state(report=True)
    phreeqcWT.form_phases(report=True)
    print("-----------------------solution after softeing-----------------------")
    print("-----------------------add CO2 softeing-----------------------")
    phreeqcWT.perform_reaction(reactants={"CO2": 120}, report=True)
    print("-----------------------solution after CO2-----------------------")
    phreeqcWT.get_solution_state(report=True)
    phreeqcWT.form_phases(report=True)
    phreeqcWT.perform_reaction(
        evaporate_water_mass_percent=90, pressure=10
    )  # , pressure=1)
    phreeqcWT.get_solution_state(report=True)
    phreeqcWT.form_phases(report=True)
    # phreeqcWT.print_log()
    phreeqcWT.get_vapor_pressure(report=True)
    print("-----------------------heat up solution to 50 C-----------------------")

    phreeqcWT.perform_reaction(temperature=50)
    vapor_pressure = phreeqcWT.get_vapor_pressure(report=True)
    print(vapor_pressure)
