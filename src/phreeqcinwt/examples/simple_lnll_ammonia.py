from phreeqcinwt.phreeqc_wt_api import phreeqcWTapi


if __name__ == "__main__":
    phreeqcWT = phreeqcWTapi(database="llnl.dat")
    phreeqcWT.build_water_composition(
        input_composotion={"Fe": 1200, "N": 2000, "SO4-2": 1000},
        charge_balance="SO4-2",
        pH=7,
        pe=0,
        units="mg/L",
        pressure=1,
        temperature=25,
        assume_alkalinity=True,
        water_mass=1,
    )

    print(
        "\n ================================ Initial solution state: ====================================\n"
    )
    phreeqcWT.print_log()
    phreeqcWT.get_solution_state(report=True)
