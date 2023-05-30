from phreeqcinwt.phreeqc_wt_api import phreeqcWTapi


if __name__ == "__main__":
    # ignore list can be provided here, but for the example we will use exlude_phase function
    # below
    phreeqcWT = phreeqcWTapi(database="pitzer.dat", ignore_phase_list=None)
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
    phreeqcWT.get_solution_state(report=False)
    print("-----------------------soften water useing soda ash-----------------------")
    phreeqcWT.perform_reaction(reactants={"Na2CO3": 63.22}, report=False)
    # phreeqcWT.get_solution_state(report=True)
    all_percipitatnts = phreeqcWT.form_phases(report=True)

    # go back to orignal solution
    phreeqcWT.current_solution = 1
    phreeqcWT.exclude_phases(["Dolomite"])
    print("-----------------------get intial solution state-----------------------")
    phreeqcWT.get_solution_state(report=False)
    print("-----------------------soften water useing soda ash-----------------------")
    phreeqcWT.perform_reaction(reactants={"Na2CO3": 63.22}, report=False)
    # phreeqcWT.get_solution_state(report=True)
    all_percipitatnts = phreeqcWT.form_phases(report=True)

    # remove excluded phase from list
    phreeqcWT.exclude_phases(None)
    # chcek if it will percipitae in new soution
    phreeqcWT.get_solution_state(report=True)
    all_percipitatnts = phreeqcWT.form_phases(report=True)
    phreeqcWT.get_solution_state(report=True)
