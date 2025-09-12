from phreeqcinwt.phreeqc_wt_api import phreeqcWTapi


def antoin_vapor_pressure(temp):
    return 10 ** (8.07131 - (1730.63 / (233.426 + temp))) / 760


if __name__ == "__main__":
    phreeqcWT_all_gasses = phreeqcWTapi(
        database="pitzer.dat",
        ignore_phase_list=[
            "Dolomite",
            "Magnesite",
            "Huntite",
            "Goergeyite",
        ],
    )
    phreeqcWT_selected_gasses = phreeqcWTapi(
        database="pitzer.dat",
        ignore_phase_list=[
            "Dolomite",
            "Magnesite",
            "Huntite",
            "Goergeyite",
        ],
        ignore_gas_phase_list=["CO2(g)"],
        track_gas_phase_list=["H2O(g)"],
    )
    # phreeqcWT = phreeqcWTapi(database="phreeqc.dat")
    # phreeqcWT = phreeqcWTapi(database="minteq.v4.dat")
    # basic brackish water
    input_composotion = {
        "Na": 0.5,
        "K": 0,
        "Cl": 0.5,
        "Ca": 0.0,
        "Mg": 0.0,
        "HCO3": 0.3805,
        "SO4": 0,
        # "C": 0.258,
        # "C": {"value": 0.385, "compound": "HCO3-"},
        # "Alkalinity": {"value": 0.381, "compound": "HCO3-"},
    }

    phreeqcWT_all_gasses.build_water_composition(
        input_composotion=input_composotion,
        charge_balance="Cl",
        pH=7,
        pe=0,
        units="g/kgw",
        pressure=1,
        temperature=20,
        assume_alkalinity=True,
    )
    phreeqcWT_selected_gasses.build_water_composition(
        input_composotion=input_composotion,
        charge_balance="Cl",
        pH=7,
        pe=0,
        units="g/kgw",
        pressure=1,
        temperature=20,
        assume_alkalinity=True,
    )
    temps = [20, 40, 60, 80, 99]
    for t in temps:
        print("all gasses")
        phreeqcWT_all_gasses.perform_reaction(temperature=t)
        vapor_pressure = phreeqcWT_all_gasses.get_vapor_pressure(report=True)
        print("selected gasses")
        vapor_pressure = phreeqcWT_selected_gasses.get_vapor_pressure(report=True)
        print(vapor_pressure)
        # ant_vp = antoin_vapor_pressure(t)
        # print(
        #     "temp (C)",
        #     t,
        #     "Phreeqc total P(atm)",
        #     round(vapor_pressure["total_fugacity"]["value"], 4),
        #     "Phreeqc H2O only P(atm)",
        #     round(vapor_pressure["H2O(g)"]["value"], 4),
        #     "Antoin P(atm)",
        #     round(ant_vp, 4),
        #     "diff H2O Only (%)",
        #     (vapor_pressure["H2O(g)"]["value"] - ant_vp) / ant_vp * 100,
        # )
