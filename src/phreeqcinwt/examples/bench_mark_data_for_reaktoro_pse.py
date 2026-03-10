from phreeqcinwt.phreeqc_wt_api import phreeqcWTapi
import numpy as np
import json


def extract_data(output_row, result, vapor_results=None, solids_results=None):
    # output_row = {}
    output_keys = [
        ("scaling_tendencies", "Anhydrite"),
        ("scaling_tendencies", "Calcite"),
        ("scaling_tendencies", "Gypsum"),
        ("solution_state", "pH"),
        ("solution_state", "Solution density"),
        ("solution_state", "Osmotic pressure"),
    ]
    for prop, key in output_keys:
        if output_row.get(key) is None:
            output_row[key] = []
        output_row[key].append(result[prop][key]["value"])
    if solids_results is not None:
        for solid in ["Calcite", "Anhydrite", "Gypsum"]:
            if output_row.get(f"formed phase {solid}") is None:
                output_row[f"formed phase {solid}"] = []
            output_row[f"formed phase {solid}"].append(solids_results[solid]["value"])
    if vapor_results is not None:
        if output_row.get("Vapor pressure") is None:
            output_row["Vapor pressure"] = []
        output_row["Vapor pressure"].append(vapor_results["H2O(g)"]["value"] * 101325)
    return output_row


def setup_phreeqc(
    feed_comp,
    add_vapor_phase=False,
    add_solid_phase=False,
    mix_solution=False,
    feed_comp_2=None,
    mix_ratio=None,
    ph_2=None,
):
    if add_vapor_phase:
        phreeqcWT = phreeqcWTapi(
            database="pitzer.dat",
            ignore_gas_phase_list=["CO2(g)"],
            track_gas_phase_list=["H2O(g)"],
        )
        result = phreeqcWT.build_water_composition(
            input_composotion=feed_comp,
            units="mol/kgw",
            pH=7.8,
            temperature=20,
            pressure=1,
            assume_alkalinity=False,
        )
    elif add_solid_phase:
        phreeqcWT = phreeqcWTapi(
            database="pitzer.dat",
            track_phase_list=["Calcite", "Anhydrite", "Gypsum"],
        )
        result = phreeqcWT.build_water_composition(
            input_composotion=feed_comp,
            units="mol/kgw",
            pH=7.8,
            temperature=20,
            pressure=1,
            assume_alkalinity=False,
        )
    elif mix_solution:
        phreeqcWT = phreeqcWTapi(
            database="pitzer.dat",
            track_phase_list=["Calcite", "Anhydrite", "Gypsum"],
        )
        result = phreeqcWT.build_water_composition(
            input_composotion=feed_comp,
            units="mol/kgw",
            pH=7.8,
            temperature=20,
            pressure=1,
            assume_alkalinity=False,
            solution_number=1,
        )
        result = phreeqcWT.build_water_composition(
            input_composotion=feed_comp_2,
            units="mol/kgw",
            pH=ph_2,
            temperature=20,
            pressure=1,
            assume_alkalinity=False,
            water_mass=1,
            solution_number=2,
        )
    else:
        phreeqcWT = phreeqcWTapi(
            database="pitzer.dat",
        )
        result = phreeqcWT.build_water_composition(
            input_composotion=feed_comp,
            units="mol/kgw",
            pH=7.8,
            temperature=20,
            pressure=1,
            assume_alkalinity=False,
        )
    return phreeqcWT


if __name__ == "__main__":
    feed_comp = {
        "Na": 1120 / 22.989769e3,
        "Ca": 150 / 40.078e3,
        "Cl": 1750 / 35.453e3,
        "HCO3": 500 / 61.0168e3,
        # "H2O": 1000 / 18.01528,
        "SO4": 1.011 / 96.06e3,
        # "H+": 1000/18.0128*2,
    }
    feed_comp_2 = {
        "Na": 1.2 * 1120 / 22.989769e3,
        "Ca": 1.2 * 150 / 40.078e3,
        "Cl": 1750 / 35.453e3,
        "HCO3": 1.2 * 500 / 61.0168e3,
        "SO4": 1.011 / 96.06e3,
        # "H+": 1000/18.0128*2,
    }
    output_feed_comp = feed_comp.copy()
    output_feed_comp["H2O"] = 1000 / 18.015

    result_dict = {}
    result_dict["feed_comp"] = output_feed_comp
    result_dict["feed_comp_2"] = feed_comp_2
    result_dict["ph_2"] = 5
    result_dict["water_removal_percent"] = np.linspace(0, 90, 10).tolist()
    result_dict["HCl"] = np.linspace(0, 0.005, 10).tolist()
    result_dict["NaOH"] = np.linspace(0, 0.005, 10).tolist()
    result_dict["CaO"] = np.linspace(0, 0.005, 10).tolist()
    result_dict["temperature"] = np.linspace(20, 95, 10).tolist()
    result_dict["mix_ratio"] = np.linspace(0.1, 1.9, 20).tolist()
    base_state = setup_phreeqc(feed_comp)
    result_dict["mix_ratio_sweep"] = {}

    for ratio in result_dict["mix_ratio"]:
        new_comp = {}
        for ion in feed_comp_2:
            new_comp[ion] = feed_comp_2[ion]  ##* ratio
        base_state = setup_phreeqc(
            feed_comp,
            mix_solution=True,
            feed_comp_2=new_comp,
            ph_2=result_dict["ph_2"],
            mix_ratio=ratio,
        )
        solution_dict = {1: 1, 2: ratio}
        base_state.mix_solutions(solution_dict, new_solution_number=3)
        r = base_state.get_solution_state()
        extract_data(result_dict["mix_ratio_sweep"], r)
    base_state.solution_number = 0
    result_dict["water_removal_percent_sweep"] = {}
    for wr in result_dict["water_removal_percent"]:
        base_state = setup_phreeqc(feed_comp)

        base_state.perform_reaction(evaporate_water_mass_percent=wr)
        r = base_state.get_solution_state()
        print(wr, r["solution_state"]["Water mass"])
        extract_data(result_dict["water_removal_percent_sweep"], r)
        # base_state.solution_number = 0
    print(result_dict["water_removal_percent_sweep"])
    base_state = setup_phreeqc(feed_comp)
    result_dict["HCl_sweep"] = {}
    for wr in result_dict["HCl"]:
        base_state = setup_phreeqc(feed_comp)
        base_state.perform_reaction(reactants={"HCl": wr}, reactant_units="mol")
        r = base_state.get_solution_state()
        extract_data(result_dict["HCl_sweep"], r)
    print(result_dict["HCl_sweep"])
    result_dict["NaOH_sweep"] = {}
    for wr in result_dict["NaOH"]:
        base_state = setup_phreeqc(feed_comp)
        base_state.perform_reaction(reactants={"NaOH": wr}, reactant_units="mol")
        r = base_state.get_solution_state()
        extract_data(result_dict["NaOH_sweep"], r)
    print(result_dict["NaOH_sweep"])
    result_dict["temperature_sweep"] = {}
    for wr in result_dict["temperature"]:
        base_state = setup_phreeqc(feed_comp, add_vapor_phase=True)
        base_state.perform_reaction(temperature=wr)
        v = base_state.get_vapor_pressure()
        r = base_state.get_solution_state()
        extract_data(result_dict["temperature_sweep"], r, vapor_results=v)
    print(result_dict["temperature_sweep"])
    result_dict["CaO_sweep"] = {}
    for wr in result_dict["CaO"]:
        base_state = setup_phreeqc(feed_comp, add_solid_phase=True)
        base_state.perform_reaction(reactants={"CaO": wr}, reactant_units="mol")

        s = base_state.form_phases()
        r = base_state.get_solution_state()
        extract_data(result_dict["CaO_sweep"], r, solids_results=s)
    print(result_dict["CaO_sweep"])
    with open("phreeqc_data.json", "w") as bench_data:
        json.dump(result_dict, bench_data, indent=4)
