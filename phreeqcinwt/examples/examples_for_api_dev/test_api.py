from phreeqcinwt.phreeqc_wt_api import phreeqcWTapi


if __name__ == "__main__":
    phreeqcWT = phreeqcWTapi(
        database="pitzer.dat",
        track_phase_list=[
            "Calcite",
            "Brucite",
            "Artinite",
            "Barite",
            "Celestite",
            "SiO2(a)",
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
    # This will build solution, and charge balance on Cl

    result = phreeqcWT.build_water_composition(
        # solution_name="reconciled solution",
        input_composotion=input_composotion,
        charge_balance="Cl",
        pH=7,
        pe=0,
        units="g/L",
        pressure=1,
        temperature=20,
        assume_alkalinity=False,
        report=True,
    )
    # reset state to original solution
    phreeqcWT.perform_reaction(reactants={"Na2CO3": 500})
    formed_phases = phreeqcWT.form_phases()
    phreeqcWT.perform_reaction(evaporate_water_mass_percent=50)
    phreeqcWT.perform_reaction(reactants={"HCl": 100})
    sol_1 = phreeqcWT.get_solution_state(report=True)

    r = phreeqcWT.build_water_composition(
        # solution_name="reconciled solution",
        input_composotion=input_composotion,
        charge_balance="Cl",
        pH=7,
        pe=0,
        units="g/L",
        pressure=1,
        temperature=20,
        assume_alkalinity=False,
        report=True,
    )
    # reset state to original solution
    phreeqcWT.perform_reaction(reactants={"Na2CO3": 500})
    pre_form_result = phreeqcWT.get_solution_state(report=False)
    formed_phases = phreeqcWT.form_phases()
    post_form_result = phreeqcWT.get_solution_state(report=False)

    pH = post_form_result["solution_state"]["pH"]["value"]
    new_sol = {}
    for ion in input_composotion.keys():
        new_sol[ion] = post_form_result["composition"][ion]["value"]

    r = phreeqcWT.build_water_composition(
        # solution_name="reconciled solution",
        input_composotion=new_sol,
        charge_balance="Cl",
        pH=pH,
        pe=0,
        units="g/L",
        pressure=1,
        temperature=20,
        assume_alkalinity=False,
        report=True,
    )
    phreeqcWT.perform_reaction(evaporate_water_mass_percent=50)
    phreeqcWT.perform_reaction(reactants={"HCl": 100})
    sol_2 = phreeqcWT.get_solution_state(report=True)
    for t in ["solution_state", "scaling_tendencies"]:
        for key in sol_2[t]:
            print(
                "{} direct {}, seqential {}".format(
                    key,
                    sol_1[t][key]["value"],
                    sol_2[t][key]["value"],
                )
            )
