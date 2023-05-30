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
