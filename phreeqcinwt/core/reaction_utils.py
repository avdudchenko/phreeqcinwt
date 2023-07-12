import numpy as np


class reaction_utils:
    def _gen_evap_command(self, command, evaporate_water_mass_percent):
        # command += "REACTION 1\n"
        mass_water_removal = self.water_mass * evaporate_water_mass_percent / 100

        mole_reactant = mass_water_removal * 1000 / 18.01528

        self.water_mass -= mass_water_removal
        if mole_reactant < 0:
            command += "    H2O {mole_reactant}\n".format(
                mole_reactant=abs(mole_reactant)
            )
        else:
            command += "    H2O -{mole_reactant}\n".format(mole_reactant=mole_reactant)
        return command

    def _gen_reaction_command(self, command, reactants):
        # command += "REACTION 2\n"
        for reactant, mass in reactants.items():
            mass_g = mass / 1000
            mw = self.db_metadata["DEFINED_REACTANTS"].get(reactant)
            if mw == None:
                raise (
                    "reactant {} not found in database, please add to /databases/defined_reactants.yaml".format(
                        reactant
                    )
                )
            mole_reactant = mass_g / mw * self.water_mass
            command += "    {reactant} {mole_reactant}\n".format(
                reactant=reactant, mole_reactant=mole_reactant
            )
        return command

    def _gen_titration_command(self, command, ph_adjust):
        if ph_adjust["pH"] < self.solution_ph:
            adjust = "acid"
        else:
            adjust = "base"
        reactant = ph_adjust.get("reactant")
        if ph_adjust.get("reactant") is None:
            reactant = self.db_metadata["DEFINED_REACTANTS"]["default_ph_adjust"][
                adjust
            ]
        else:
            self.db_metadata["DEFINED_REACTANTS"]["default_ph_adjust"][
                adjust
            ] = reactant
        if self.db_metadata["DEFINED_REACTANTS"].get(reactant) is None:
            raise (
                "Failed to find reactant {} in defined_reactants database, please add to /databases/defined_reactants.yaml".format(
                    reactant
                )
            )

        if adjust == "acid":
            command = self._gen_acid_adjust(command, ph_adjust["pH"], reactant)
        else:
            command = self._gen_base_adjust(command, ph_adjust["pH"], reactant)
        return command

    def _gen_acid_adjust(self, command, ph_target, acid_titrant):
        command += "PHASES\n"
        command += "Fix_H+\n"
        command += "   H+=H+\n"
        command += "EQUILIBRIUM_PHASES \n"
        if self.solution_ph != ph_target:
            command += "   Fix_H+ -{ph_target} {acid_titrant}\n".format(
                ph_target=ph_target, acid_titrant=acid_titrant
            )
        return command

    def _gen_base_adjust(self, command, ph_target, base_titrant):
        command += "PHASES\n"
        command += "Fix_OH-\n"
        command += "   OH-=OH-\n"
        command += "EQUILIBRIUM_PHASES \n"
        if self.solution_ph != ph_target:
            command += "   Fix_OH- -{ph_target} {base_titrant}\n".format(
                ph_target=(14 - ph_target), base_titrant=base_titrant
            )
        return command

    def set_titrant_dict(self, titration_dict, titrant_type, value):
        reactant = self.db_metadata["DEFINED_REACTANTS"]["default_ph_adjust"][
            titrant_type
        ]
        mw = self.db_metadata["DEFINED_REACTANTS"][reactant]
        titration_dict[reactant] = {
            "value": value * mw * 1000 / self.water_mass,
            "units": "mg/kgw",
        }
        return titration_dict
