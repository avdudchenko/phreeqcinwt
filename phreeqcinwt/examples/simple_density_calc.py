from phreeqcinwt.phreeqc_wt_api import phreeqcWTapi


if __name__ == "__main__":
    # only pitzer/phreeqc and amm data support density
    phreeqcWT = phreeqcWTapi(database="pitzer.dat")
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

    density = []
    concetration_solutes = []
    print("-----------------------get intial solution state-----------------------")
    for wr in [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99]:
        phreeqcWT.current_solution = 1
        phreeqcWT.get_solution_state(report=False)
        phreeqcWT.perform_reaction(evaporate_water_mass_percent=wr)
        # phreeqcWT.form_phases()
        state = phreeqcWT.get_solution_state(report=False)

        print(
            "Water recovery",
            wr,
            "%",
            state["solution_state"]["Water mass"]["value"],
            "Total concetration",
            state["solution_state"]["Total solids (volume basis)"]["value"],
            "density",
            state["solution_state"]["Solution density"]["value"],
        )
