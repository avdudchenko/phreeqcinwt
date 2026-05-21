import logging

import molmass
import numpy as np


LOGGER = logging.getLogger(__name__)
SPECIAL_FORMULA_MW = {"Ca0.5(CO3)0.5": 50.05}


class utilities:
    def _get_formula_mw(self, formula):
        if formula in SPECIAL_FORMULA_MW:
            return SPECIAL_FORMULA_MW[formula]
        return molmass.Formula(formula).mass

    def get_total_concetration(self, results_dict):
        total_solid_mass = 0
        total_solution_mass = 0
        for key, mass in results_dict["composition"]["species"].items():
            if key not in ["H2O", "H+", "OH-"]:
                total_solid_mass += mass["mass (g)"]
            total_solution_mass += mass["mass (g)"]
        result_dict = {}
        result_dict["Total dissolved solids"] = {
            "value": total_solid_mass / self.water_volume,
            "units": "g/L",
        }
        result_dict["Solution mass"] = {"value": total_solution_mass, "units": "kg"}
        return result_dict

    def find_input_in_db(self, name, input_loading):
        if name in self.db_metadata["SOLUTION_MASTER_SPECIES"]:
            return name
        else:
            name_not_found = True
            for ion, info in self.db_metadata["SOLUTION_MASTER_SPECIES"].items():
                if name == info["formula"]:
                    return ion
                    break
                elif name == info["species"]:
                    name_not_found = False
                    return ion
                    break
            if name_not_found:
                raise Exception(
                    "Ion {} not found in metadata or database, please check".format(
                        name
                    )
                )

    def check_formula_consistent(self, db_name, input_formula, input_mw=None):
        species_metadata = self.db_metadata["SOLUTION_MASTER_SPECIES"][db_name]
        db_formula = species_metadata["formula"]
        db_mw = species_metadata["mw"]

        if db_formula != input_formula:
            species_metadata["formula"] = input_formula

        if input_mw is not None:
            species_metadata["mw"] = input_mw
            return

        if db_formula == input_formula and db_mw is not None:
            return

        try:
            species_metadata["mw"] = self._get_formula_mw(input_formula)
        except Exception:
            if db_mw is not None:
                LOGGER.debug(
                    "Unable to derive molecular weight for %s; keeping existing %s g/mol",
                    input_formula,
                    db_mw,
                )
                return
            raise

    def set_dict(self, phreeqc_ion_dict, name, input_loading, assume_alkalinity):
        if name == "HCO3" or name == "CaHCO3":
            if "C(4)" in self.db_metadata["SOLUTION_MASTER_SPECIES"]:
                phreeqc_name = "C(4)"
            elif "C(+4)" in self.db_metadata["SOLUTION_MASTER_SPECIES"]:
                phreeqc_name = "C(+4)"
            else:
                raise ("Did not find C4 or C(+4) in database")
            mw = None
            if name == "CaHCO3":
                mw = 50.04
                input_formula = "Ca0.5(CO3)0.5"
            else:
                input_formula = "HCO3"
            self.check_formula_consistent(phreeqc_name, input_formula, mw)

            phreeqc_ion_dict[phreeqc_name] = {
                "value": input_loading,
                "compound": input_formula,
            }
            if assume_alkalinity:
                phreeqc_ion_dict["Alkalinity"] = {
                    "value": input_loading,
                    "compound": input_formula,
                }
                self.check_formula_consistent("Alkalinity", input_formula, mw)
        elif name == "Alkalinity":
            phreeqc_name = self.find_input_in_db(name, input_loading)
            mw = None
            if isinstance(input_loading, dict):
                input_formula = input_loading.get(
                    "formula",
                    self.db_metadata["SOLUTION_MASTER_SPECIES"][phreeqc_name][
                        "formula"
                    ],
                )
                mw = input_loading.get("mw")
            else:
                input_formula = self.db_metadata["SOLUTION_MASTER_SPECIES"][
                    phreeqc_name
                ]["formula"]
            self.check_formula_consistent(phreeqc_name, input_formula, mw)
            phreeqc_ion_dict[phreeqc_name] = {
                "value": input_loading,
                "compound": input_formula,
            }
        else:
            phreeqc_name = self.find_input_in_db(name, input_loading)
            mw = None
            if isinstance(input_loading, dict):
                input_formula = input_loading["formula"]
                mw = input_loading.get("mw")
            else:
                input_formula = name
            self.check_formula_consistent(phreeqc_name, input_formula, mw)
            phreeqc_ion_dict[phreeqc_name] = {
                "value": input_loading,
                "compound": input_formula,
            }
        return phreeqc_ion_dict, phreeqc_name

    def build_ion_dict(self, input_dict, assume_alkalinity=False):
        phreeqc_ion_dict = {}
        self.return_dict = {}
        self.forward_dict = {}
        self.reverse_dict = {}
        for name, loading in input_dict.items():
            phreeqc_ion_dict, phreeqc_name = self.set_dict(
                phreeqc_ion_dict, name, loading, assume_alkalinity
            )

            self.return_dict[
                self.db_metadata["SOLUTION_MASTER_SPECIES"][phreeqc_name]["species"]
            ] = {
                "input_name": name,
                "mw": self.db_metadata["SOLUTION_MASTER_SPECIES"][phreeqc_name]["mw"],
            }
            self.forward_dict[name] = phreeqc_name
            self.reverse_dict[phreeqc_name] = name
        # prs
        return phreeqc_ion_dict

    def print_log(self):
        for action, log in self.command_log.items():
            if isinstance(log, dict):
                print(log["command"])
            else:
                print(action, log)

    def run_string(self, string):
        """Method to send command to phreeqpy
        the string is the command string that will be send, if phreeqcAPI is configured to log commands
        they will be stored in command log dict file.

        Keyword arguments:
        string -- Command to send in phreeqc via phreeqpy
        """

        if self.command_log["log"]:
            # self.current_action += 1
            self.command_log["Action #{}".format(self.current_action)] = {
                "command": string,
                "solution_number": self.current_solution,
            }
            self.current_action += 1
        self.phreeqc.run_string(string)

    def store_solution_name(self, name=None, warn=False):
        if name is not None:
            if name in self.solution_name_reference and warn:
                print("Warning {} already in solution list, overwriting".format(name))
            self.solution_name_reference[name] = {
                "sol_number": self.current_solution,
                "water_mass": self.water_mass,
            }

    def load_solution(self, name):
        sol_num = self.solution_name_reference.get(name)
        if sol_num is not None:
            self.current_solution = sol_num["sol_number"]
            self.water_mass = sol_num["water_mass"]
        else:
            print("Solution name {} not found".format(name))

    def save_solution(self, name, warn=False):
        self.store_solution_name(name, warn)

    def display_current_solutions(self):
        print("-----------stored solution aliases------------")
        for sol_name, number in self.store_solution_name.items():
            print(sol_name, number)
        print("----------------------------------------------")
