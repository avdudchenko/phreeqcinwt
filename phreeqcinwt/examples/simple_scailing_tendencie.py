from phreeqcinwt.phreeqc_wt_api import phreeqcWTapi

import numpy as np
from analysis_plot_kit.core import fig_generator

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
            # "Antigorite",
            # "Talc",
            # "Sepiolite",
            # "Anthophyllite",
        ],
        track_phase_list=["Calcite", "Gypsum", "Barite", "Celestite"],
    )

    input_composotion = {
        "Na": 163 / 1000,
        # "K": 5.7 / 1000,
        "Ca": 100 / 1000,
        # "Mg": 30.028 / 1000,
        "Cl": 107.15101 / 1000,
        # "SO4": 248.1 / 1000,
        "HCO3": 279.901 / 1000,
        # "Sr": 0.22962740 / 1000,
        # "Ba": 0.0060059149 / 1000,
        # "C": 0.258,
        # "C": {"value": 0.385, "compound": "HCO3-"},
        # "Alkalinity": {"value": 0.381, "compound": "HCO3-"},
    }

    result = phreeqcWT.build_water_composition(
        input_composotion=input_composotion,
        charge_balance="Cl",
        pH=7,
        pe=0,
        units="g/kgw",
        pressure=1,
        temperature=20,
        assume_alkalinity=False,
        report=False,
        water_mass=10,
    )
    result = phreeqcWT.get_solution_state(report=True)
    # result = phreeqcWT.perform_reaction(evaporate_water_mass_percent=90, report=True)
    # percipitation_result = phreeqcWT.form_phases(report=True)

    # result = phreeqcWT.perform_reaction(
    #     reactants={"CaO": 2000, "Na2CO3": 2000}, report=True
    # )
    # result = phreeqcWT.get_solution_state(report=True)
    # percipitation_result = phreeqcWT.form_phases(report=True)
    # result = phreeqcWT.perform_reaction(reactants={"HCl": 2000}, report=True)
    # percipitation_result = phreeqcWT.form_phases(report=True)
    # # result = phreeqcWT.get_solution_state(report=True)
