from phreeqcinwt.phreeqc_wt_api import phreeqcWTapi
import numpy as np
import json


def extract_data(output_row, result, vapor_pressure):
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
    if output_row.get("H2O pressure") is None:
        output_row["H2O pressure"] = []
    # print(vapor_pressure)
    output_row["H2O pressure"].append(vapor_pressure["H2O(g)"]["value"] * 101325)
    return output_row


def setup_phreeqc(feed_comp):
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
        pressure=10,
        assume_alkalinity=False,
    )
    print(result["solution_state"]["pH"])
    return phreeqcWT


def get_result(phreeqc):
    return phreeqc.get_solution_state(), phreeqc.get_vapor_pressure()


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
    output_feed_comp = feed_comp.copy()
    output_feed_comp["H2O"] = 1000 / 18.015

    result_dict = {}
    result_dict["feed_comp"] = output_feed_comp
    result_dict["phreeqc_results"] = {}
    result_dict["water_removal_percent"] = np.linspace(0, 90, 10).tolist()
    result_dict["HCl"] = np.linspace(0, 0.005, 10).tolist()
    result_dict["NaOH"] = np.linspace(0, 0.005, 10).tolist()
    result_dict["temperature"] = np.linspace(20, 95, 10).tolist()

    base_state = setup_phreeqc(feed_comp)
    result_dict["water_removal_percent_sweep"] = {}
    for wr in result_dict["water_removal_percent"]:
        base_state = setup_phreeqc(feed_comp)

        base_state.perform_reaction(evaporate_water_mass_percent=wr)
        r, v = get_result(base_state)
        print(wr, r["solution_state"]["Water mass"])
        extract_data(result_dict["water_removal_percent_sweep"], r, v)
        # base_state.solution_number = 0
    print(result_dict["water_removal_percent_sweep"])
    base_state = setup_phreeqc(feed_comp)
    result_dict["HCl_sweep"] = {}
    for wr in result_dict["HCl"]:
        base_state = setup_phreeqc(feed_comp)
        base_state.perform_reaction(reactants={"HCl": wr}, reactant_units="mol")
        r, v = get_result(base_state)
        extract_data(result_dict["HCl_sweep"], r, v)
    print(result_dict["HCl_sweep"])
    result_dict["NaOH_sweep"] = {}
    for wr in result_dict["NaOH"]:
        base_state = setup_phreeqc(feed_comp)
        base_state.perform_reaction(reactants={"NaOH": wr}, reactant_units="mol")
        r, v = get_result(base_state)
        extract_data(result_dict["NaOH_sweep"], r, v)
    print(result_dict["NaOH_sweep"])
    result_dict["temperature_sweep"] = {}
    for wr in result_dict["temperature"]:
        base_state = setup_phreeqc(feed_comp)
        base_state.perform_reaction(temperature=wr)
        r, v = get_result(base_state)
        extract_data(result_dict["temperature_sweep"], r, v)
    print(result_dict["temperature_sweep"])

    with open("phreeqc_data.json", "w") as bench_data:
        json.dump(result_dict, bench_data, indent=4)
