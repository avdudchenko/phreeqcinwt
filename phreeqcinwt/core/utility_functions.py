import molmass
import numpy as np


class utilities:
    def get_total_concetration(self, results_dict):
        total_mass = 0
        for key, mass in results_dict["composition"].items():
            if mass["units"] != "g/kgw":
                raise ("Units need to be in g/kgw")
            total_mass += mass["value"]
        result_dict = {}
        result_dict["Total solids (mass basis)"] = {
            "value": total_mass,
            "units": "g/kgw",
        }
        water_mass = results_dict["solution_state"]["Water mass"]["value"]
        rho = results_dict["solution_state"]["Solution density"]["value"]
        mass_solution = water_mass + total_mass / 1000 * water_mass
        result_dict["Solution mass"] = {"value": mass_solution, "units": "kg"}
        con_solids = total_mass * water_mass / (mass_solution / rho)
        result_dict["Total solids (volume basis)"] = {
            "value": con_solids,
            "units": "g/L",
        }
        return result_dict

    def find_input_in_db(self, name, input_loading):
        if name in self.db_metadata["SOLUTION_MASTER_SPECIES"]:
            return name
        else:
            name_found = True
            for ion, info in self.db_metadata["SOLUTION_MASTER_SPECIES"].items():
                # print(name, info)
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

    def check_formula_consistent(self, db_name, input_fomrula, input_mw=None):
        db_formula = self.db_metadata["SOLUTION_MASTER_SPECIES"][db_name]["formula"]
        if db_formula != input_fomrula:
            self.db_metadata["SOLUTION_MASTER_SPECIES"][db_name][
                "formula"
            ] = input_fomrula
        db_mw = self.db_metadata["SOLUTION_MASTER_SPECIES"][db_name]["mw"]

        try:
            if input_mw == None:
                self.db_metadata["SOLUTION_MASTER_SPECIES"][db_name][
                    "mw"
                ] = molmass.Formula(input_fomrula).mass
            else:
                self.db_metadata["SOLUTION_MASTER_SPECIES"][db_name]["mw"] = input_mw
        except:
            print(
                "failed to update db mw, please vefiy, useing {} g/mol for {}".format(
                    db_mw, input_formula
                )
            )

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

    def store_solution_name(self, name=None):
        if name is not None:
            if name in self.solution_name_reference:
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

    def save_solution(self, name):
        self.store_solution_name(name)

    def display_current_solutions(self):
        print("-----------stored solution aliases------------")
        for sol_name, number in self.store_solution_name.items():
            print(sol_name, number)
        print("----------------------------------------------")
