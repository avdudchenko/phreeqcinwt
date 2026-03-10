from tkinter import NE

import numpy as np

import molmass


class solution_utils:
    def _process_activities(self, result):
        # print(result)
        activities = {}
        for element, name in self.return_dict.items():
            idx = np.where("la_" + element == np.array(result[0]))[0]
            # print(idx, "la_" + element)
            activities[element] = {
                "value": 10 ** result[1][idx[0]],
                "units": "dimensionless",
            }
            activities["log10_{}".format(element)] = {
                "value": result[1][idx[0]],
                "units": "dimensionless",
            }
        idx = np.where("la_H2O" == np.array(result[0]))[0]
        # print(idx)
        activities["H2O"] = {"value": 10 ** result[1][idx[0]], "units": "dimensionless"}
        activities["log10_{}".format("H2O")] = {
            "value": result[1][idx[0]],
            "units": "dimensionless",
        }
        # print(activities)
        return activities

    def _get_osmotic_pressure(self, result, solution_state, activities):
        idx = np.where("h2o_vm" == np.array(result[0]))[0]

        vm = result[1][idx[0]]  # cm3/mol
        activity = activities["H2O"]["value"]
        R = 8.31446261815324  # m3⋅Pa⋅K−1⋅mol−1
        T = solution_state["Temperature"]["value"] + 273.15
        if vm > 0:
            osmotic_pressure = -R * T / (vm * 1e-6) * np.log(activity)
        else:
            osmotic_pressure = None
        return {"units": "Pa", "value": osmotic_pressure}

    def _get_solution_comp(
        self,
        result,
    ):
        aque_species_comp = {"elements": {}, "species": {}}
        for i in range(len(result[1])):
            if isinstance(result[1][i], str) and "element" in result[1][i]:
                element = result[1][i + 1]
                if element in self.db_metadata["SOLUTION_MASTER_SPECIES"]:
                    normal_name = self.db_metadata["SOLUTION_MASTER_SPECIES"][element][
                        "formula"
                    ]
                    mw = self.db_metadata["SOLUTION_MASTER_SPECIES"][element]["mw"]
                else:
                    normal_name = element
                    mw = molmass.Formula(element).mass
                aque_species_comp["elements"][normal_name] = {
                    "mols": result[1][i + 2],
                    "mass (g)": result[1][i + 2] * mw,
                    "mw (g/mol)": mw,
                }
        for i in range(len(result[1])):
            if isinstance(result[1][i], str) and "specie" in result[1][i]:
                species = result[1][i + 1]
                mw = molmass.Formula(species).mass
                aque_species_comp["species"][species] = {
                    "mols": result[1][i + 2],
                    "mass (g)": result[1][i + 2] * mw,
                    "mw (g/mol)": mw,
                }
        return aque_species_comp

    def _get_diffusion_transfer_number(
        self,
        result,
    ):
        transport_data = {"diffusion": {}, "transfer_number": {}}
        for i in range(len(result[1])):
            if isinstance(result[1][i], str) and "diffusion" in result[1][i]:
                species = result[1][i + 1]
                transport_data["diffusion"][species] = {
                    "value": result[1][i + 2],
                    "units": "m2/s",
                }
        for i in range(len(result[1])):
            if isinstance(result[1][i], str) and "specie" in result[1][i]:
                species = result[1][i + 1]
                transport_data["transfer_number"][species] = {
                    "value": result[1][i + 2],
                    "units": "unitless",
                }
        return transport_data

    def _get_scaling_tendencies(self, result, report=False):
        result_dict = {}
        for i in range(len(result[1])):
            if isinstance(result[1][i], str) and "phase" in result[1][i]:
                phase = result[1][i + 1]
                si = result[1][i + 2]
                if float(si) > -999:
                    try:
                        val = 10 ** (float(si))
                    except:
                        val = 1e20
                    result_dict[phase] = {
                        "value": val,
                        "units": "dimensionless",
                    }
            if isinstance(result[1][i], str) and "volume" in result[1][i]:
                volume = result[1][i + 1]
        results_dict = {}
        results_dict["scaling_tendencies"] = result_dict
        results_dict["solution_state"] = {}

        sol_state_dict = {
            "pH": {"name": "pH", "units": "dimensionless"},
            "pe": {"name": "pe", "units": "dimensionless"},
            "temp(C)": {"name": "Temperature", "units": "C"},
            "Alk(eq/kgw)": {"name": "Alkalinity", "units": "g/kgw"},
            "charge(eq)": {"name": "Charge balance", "units": "eq"},
            "pct_err": {"name": "Error in charge", "units": "%"},
            "mass_H2O": {"name": "Water mass", "units": "kg"},
            "density": {"name": "Solution density", "units": "kg/L"},
            "mu": {"name": "Ionic strength", "units": "M"},
            "solution_conductivity": {
                "name": "Solution conductivity",
                "units": "uS/cm",
            },
        }
        # print(result[0])
        for key, data in sol_state_dict.items():
            # print(key, name, unit)
            name = data["name"]
            unit = data["units"]
            # print(key)

            idx = np.where(key == np.array(result[0]))[0][0]
            val = result[1][idx]
            if key == "Alk(eq/kgw)":
                multiplier = self.db_metadata["SOLUTION_MASTER_SPECIES"]["Alkalinity"][
                    "mw"
                ]
                formula = self.db_metadata["SOLUTION_MASTER_SPECIES"]["Alkalinity"][
                    "formula"
                ]
                val = val * multiplier
                unit = "g/kgw as {}".format(formula)
            # elif key == "density":
            # results_dict["solution_state"][name] = {"value": val, "units": unit}

            results_dict["solution_state"][name] = {"value": val, "units": unit}
            # print(results_dict)
        results_dict["solution_state"]["Solution volume"] = {
            "value": volume,
            "units": "L",
        }
        self.water_mass = results_dict["solution_state"]["Water mass"]["value"]
        self.water_volume = volume
        idx = np.where("pH" == np.array(result[0]))[0][0]
        self.solution_ph = result[1][idx]

        if results_dict["scaling_tendencies"].get("max") is not None:
            results_dict["scaling_tendencies"].pop("max")
        max_scaling_key = max(
            results_dict["scaling_tendencies"].keys(),
            key=lambda key: results_dict["scaling_tendencies"][key]["value"],
        )

        results_dict["scaling_tendencies"]["max"] = {
            "value": results_dict["scaling_tendencies"][max_scaling_key]["value"],
            "scalant": max_scaling_key,
        }
        return results_dict.copy()
