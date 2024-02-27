from phreeqcinwt.phreeqc_wt_api import phreeqcWTapi


def antoin_vapor_pressure(temp):
    return 10 ** (8.07131 - (1730.63 / (233.426 + temp))) / 760


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
        "Na": 2,
        "K": 0,
        "Cl": 2,
        "Ca": 0.0,
        "Mg": 0.0,
        "HCO3": 0.0,
        "SO4": 0,
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
    recovery = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 98, 99]
    phreeqcWT.save_solution("Ref_state")
    for r in recovery:
        phreeqcWT.load_solution("Ref_state")
        phreeqcWT.perform_reaction(evaporate_water_mass_percent=r)
        result = phreeqcWT.get_solution_state(report=True)
        # vapor_pressure = phreeqcWT.get_vapor_pressure(report=False)
        print(
            result["solution_state"]["Water mass"],
            result["solution_state"]["Total solids (volume basis)"],
            result["solution_state"]["Osmotic pressure"]["value"] * 1e-5,
        )
        # print()
