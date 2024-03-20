import numpy as np


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

        osmotic_pressure = -R * T / (vm * 1e-6) * np.log(activity)
        return {"units": "Pa", "value": osmotic_pressure}

    def _get_solution_comp(
        self,
        result,
        return_input_names=True,
        units="g/kgw",
        return_above=1e-16,
    ):
        aque_species_comp = {}
        for element, vals in self.return_dict.items():
            # print("m_" + items["species"] + "(mol/kgw)")
            aque_species_comp[vals["input_name"]] = {"sub_species": {}}
            # total_mols = 0
            for spc in self.db_metadata["SOLUTION_SPECIES"][element]["sub_species"]:
                idx = np.where("m_" + spc + "(mol/kgw)" == np.array(result[0]))[0]
                # print("m_" + items["species"] + "(mol/kgw)", idx)
                if idx.size > 0:
                    idx = idx[0]
                    value = result[1][idx]
                    unit = "mol/kgw"
                    # print(value)
                    # total_mols += value
                    if value > return_above:
                        aque_species_comp[vals["input_name"]]["sub_species"][spc] = {
                            "value": value,
                            "units": unit,
                        }
            idx = np.where(
                self.forward_dict[vals["input_name"]] + "(mol/kgw)"
                == np.array(result[0])
            )[0][0]
            # print(vals["input_name"], idx)
            total_mols = result[1][idx]
            # if self.return_dict.get(spc) is not None:
            if units:
                if isinstance(vals["mw"], float):
                    unit = "g/kgw"
                    total_mols = total_mols * vals["mw"]
                    # print(element, vals["mw"])
            # else:
            aque_species_comp[vals["input_name"]]["value"] = total_mols
            aque_species_comp[vals["input_name"]]["units"] = unit
        return aque_species_comp

    def _get_scaling_tendencies(self, result, report=False):
        result_dict = {}
        self.db_metadata["PRESENT_PHASES_IN_SOLUTION"] = []
        for phase in self.db_metadata["PHASES"].keys():
            # print(result[0])

            p_idx = np.where(np.array(result[0]) == "si_" + phase)[0]
            ksp_idx = np.where(np.array(result[0]) == "ksp_" + phase)[0]
            if p_idx.size > 0:
                si = result[1][p_idx[0]]
                if float(si) > -999:
                    try:
                        val = 10 ** (float(si))
                    except:
                        val = 1e20
                    result_dict[phase] = {
                        "value": val,
                        "log10_ksp": result[1][ksp_idx[0]],
                        "units": "dimensionless",
                    }
                    self.db_metadata["PRESENT_PHASES_IN_SOLUTION"].append(phase)

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
        print(result[0])
        for key, data in sol_state_dict.items():
            # print(key, name, unit)
            name = data["name"]
            unit = data["units"]
            # print(key)

            idx = np.where(key == np.array(result[0]))[0][0]
            val = result[1][idx]
            # print(key)
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

        self.water_mass = results_dict["solution_state"]["Water mass"]["value"]
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
            "log10_ksp": results_dict["scaling_tendencies"][max_scaling_key][
                "log10_ksp"
            ],
            "scalant": max_scaling_key,
        }
        return results_dict.copy()
