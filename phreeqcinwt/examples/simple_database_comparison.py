from phreeqcinwt.phreeqc_wt_api import phreeqcWTapi


if __name__ == "__main__":
    # only pitzer/phreeqc and amm data support density
    db_apis = {
        "pitzer": phreeqcWTapi(database="pitzer.dat"),
        "phreeqc": phreeqcWTapi(database="phreeqc.dat"),
    }

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
    for name, db in db_apis.items():
        db.build_water_composition(
            input_composotion=input_composotion,
            charge_balance="Cl",
            pH=7,
            pe=0,
            units="g/kgw",
            pressure=1,
            temperature=20,
            assume_alkalinity=False,
        )

    density = []
    concetration_solutes = []
    print("-----------------------get intial solution state-----------------------")
    states = {}
    for wr in [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99]:
        states[wr] = {}
        for name, db in db_apis.items():
            db.current_solution = 1

            db.get_solution_state(report=False)
            db.perform_reaction(
                ph_adjust={"pH": 6.5, "reactant": "CO2"},
                evaporate_water_mass_percent=wr,
            )

            state = db.get_solution_state(report=False)
            states[wr][name] = state

    for wr in [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99]:
        state = states[wr]
        pitzer_phases = state["pitzer"]["scaling_tendencies"].keys()
        print("------------------WR {}%---------------------".format(wr))
        for pp in pitzer_phases:
            if pp in state["phreeqc"]["scaling_tendencies"]:
                p_SI = state["pitzer"]["scaling_tendencies"][pp]["value"]
                ph_SI = state["phreeqc"]["scaling_tendencies"][pp]["value"]
                print(
                    "Pitzer SI for {}={} phreeqc={}, diff {}%".format(
                        pp, p_SI, ph_SI, (p_SI - ph_SI) / p_SI * 100
                    )
                )
