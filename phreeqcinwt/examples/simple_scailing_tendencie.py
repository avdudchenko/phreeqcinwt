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
    for ca in [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1]:
        input_composotion = {
            "Na": 0.739,
            "K": 0.009,
            "Cl": 0.870,
            "Ca": ca,
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
            assume_alkalinity=False,
        )

        print("-----------------------get intial solution state-----------------------")
        result = phreeqcWT.get_solution_state(report=False)
        print("Calcite", result["scaling_tendencies"]["Calcite"])
