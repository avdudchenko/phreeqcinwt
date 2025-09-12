from phreeqcinwt.phreeqc_wt_api import phreeqcWTapi


if __name__ == "__main__":
    # ignore list can be provided here, but for the example we will use exlude_phase function
    # below
    phreeqcWT = phreeqcWTapi(
        database="pitzer.dat",
        ignore_phase_list=[
            "Dolomite",
            # "Goergeyite",
            "Magnesite",
            "Huntite",
            # "CO2(g)",
            # "H2O(g)",
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
        pe=4,
        units="g/L",
        pressure=1,
        temperature=25,
        assume_alkalinity=True,
    )

    print("-----------------------get intial solution state-----------------------")
    # phreeqcWT.get_solution_state(report=False)
    print("-----------------------soften water useing soda ash-----------------------")
    phreeqcWT.perform_reaction(
        reactants={"Na2CO3": 150},
        # evaporate_water_mass_percent=80,
        pressure=1,
        report=False,
    )
    all_percipitatnts = phreeqcWT.form_phases(report=True)
    phreeqcWT.perform_reaction(
        reactants={"CO2": 20},
        # evaporate_water_mass_percent=80,
        pressure=1,
        report=False,
    )
    all_percipitatnts = phreeqcWT.form_phases(report=True)
    phreeqcWT.perform_reaction(
        evaporate_water_mass_percent=94, pressure=110, report=False
    )
    state = phreeqcWT.get_solution_state(report=True)
    for ion, mass in state["composition"].items():
        print(ion, mass["value"])
    all_percipitatnts = phreeqcWT.form_phases(report=True)
    # phreeqcWT.get_solution_state(report=True)

    # phreeqcWT.current_solution = 1
    # phreeqcWT.exclude_phases(["Dolomite"])
    # print("-----------------------get intial solution state-----------------------")
    # phreeqcWT.get_solution_state(report=False)
    # print("-----------------------soften water useing soda ash-----------------------")
    # phreeqcWT.perform_reaction(reactants={"Na2CO3": 63.22}, report=False)
    # # phreeqcWT.get_solution_state(report=True)
    # all_percipitatnts = phreeqcWT.form_phases(report=True)

    # # remove excluded phase from list
    # phreeqcWT.exclude_phases(None)
    # # chcek if it will percipitae in new soution
    # phreeqcWT.get_solution_state(report=True)
    # all_percipitatnts = phreeqcWT.form_phases(report=True)
    # phreeqcWT.get_solution_state(report=True)
