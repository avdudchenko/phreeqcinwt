import sys
import os
import phreeqpy.iphreeqc.phreeqc_dll as phreeqc_mod

import csv
import numpy as np

import copy


import molmass
import yaml

from phreeqcinwt.core.data_base_utils import dataBaseManagment


class phreeqcWTapi(dataBaseManagment):
    def __init__(
        self,
        database=r"phreeqc.dat",
        db_dir=None,
        # database=r"minteq.v4.dat",
        rebuild_master_species=False,
        rebuild_soluton_species=False,
        rebuild_phases=False,
        log_phreeqc_commands=True,
        ignore_phase_list=None,
    ):
        """this is main class for phreeqcAPI that will handle working with a single or multiple solutions
        this class is a higher level api for phreeqpy and abstraction method for phreeqc with
        focus on application in water treatment.

        the class creates and manages phreeqc provided databaes (please place the database from database install in
        /databases folder of the module)

        the class requires generation of meta data for each database, from which aviaalble master species, sub-spesies, and
        phases are extracted and used to aquire data from phreeqc. These can be auto generated by use the rebuild key words described below.

        The module includes pre-build databases metadata files for a view libraries and will be auto created if they don't exist.
        The only file user should manually modify is the database_SOLUTION_MASTER_SPECIES.yaml file, where user cans pecify
        thier explicity formula and mw for compound being used in thier reactions, althoug in most cases this is not required.

        If user species log_phreeqc_commands to true, they will be stored in command_log dictionary, under key "Action #" where
        the # is sequence of command send to phreeqc back end. These are usefull for debugging purposes, if results fail to be returened
        the user is encouraged to print out the log to consol and paste into phreeqc GUI and run it, as it will display the excat
        error for why phreeqc failed to return results. The log can be printed useing print_log method.

        Database directory should include metadata folder.

        Keyword arguments:
        db_dir -- diretory for data base files if None, uses local module dir (default None)
        database -- database to use by phreeqcy, (default r'minteq.v4.dat)
        rebuild_master_species -- rebuild meta data for master species list (default False)
        rebuild_soluton_species -- rebuild meta data for solution species list (default False)
        rebuild_phases -- rebuild meta data for phases list (default False)
        log_phreeqc_commands -- log phreeqc commands(default False)
        ignore_phase_list -- provide list of phases to not check for scaling and percipitaiton, can be updated useing exclude_phases method
        """

        self.cwd = db_dir
        self.rebuild_metadata = [
            rebuild_master_species,
            rebuild_soluton_species,
            rebuild_phases,
        ]
        self.phreeqc = phreeqc_mod.IPhreeqc()
        self.database = database
        self.load_database()
        # storing last solution conditions for ph adjust etc.
        self.sol_state_dict = {}
        # number of current soluton and action being performed
        self.current_solution = 1
        self.current_action = 0
        # actions log
        self.command_log = {"log": log_phreeqc_commands}

        self.exclude_phases(ignore_phase_list)

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

    def print_log(self):
        for action, log in self.command_log.items():
            if isinstance(log, dict):
                print(log["command"])
            else:
                print(action, log)

    def exclude_phases(self, ignore_list):
        """Method to exclude phases from being checked when getting scailing tendencies or percipitaiton
        to use, provide ignore_list, then call get_solution_state to update other relevant settings
        before calling any other functions

        Keyword arguments:
        ignore_list -- List of phases to ignore
        """
        self.db_metadata["CHECK_PHASE_LIST"] = self.db_metadata["PHASES"].keys()
        if ignore_list != None:
            new_phase_list = []
            ignored_list = []
            for k in self.db_metadata["CHECK_PHASE_LIST"]:
                if k not in ignore_list:
                    new_phase_list.append(k)
                else:
                    ignored_list.append(k)
            if len(ignore_list) != len(ignore_list):
                print(
                    "Failed to find all ignore phases!, only found {}".format(
                        ignored_list
                    )
                )
            self.db_metadata["CHECK_PHASE_LIST"] = new_phase_list

    def build_water_composition(
        self,
        input_composotion,
        solution_number=1,
        pH=7,
        temperature=25,
        pe=4,
        redox="pe",
        pressure=1,
        units="g/kgw",
        density=1,
        charge_balance="Cl",
        water_mass=1,
        assume_alkalinity=True,
    ):
        """
        This method is used to build a solution.  Input compositon should use either phreeqc species, formula, or solution speices as defined in
        SOLUTION_MASTER_SPECIES.yaml file. The input dict will be passed through build_ion_dict method, which will first check for component name in
        phreeqc species names, followed by formula, and finnaly by species, it will then return a dict that uses phreeqc specie names and formulas
        to be passed into phreeqc to build the solution (e.g if user provides SO4, it will be passed in as S(6) as SO4 into phreeqc).

        For Alkalinity, if you specify assume_alkalinity=True, and provide HCO3 or CaCO3 value in input_composition this will set Alkalinity and C(4)
        to same values, and pH for the solution will be calcualted by phreeqC
        If assume_alkalinity is set to False, passing in HCO3 will use C(4) only and pH will be fixed to explicity value specified by pH argument.
        If user wants to provide differnt Alkalinity and HCO3/CO3 concetraiton, set assume_alakalinity=False
        and explicity provide HCO3/CO3 for HCO3 concetration which will be set as C(4) and Alkalinity for solution.

        input_compositon should be a python dictionory with following possible structures
        {component_name: loading of componet (must be in same units as specified by units keywords)} - this will load in the ion and formula from SOLUTION_MASTER_SPECIES

        if you want to specify a custom compound for molality calcualtion during solution generation provide the following dict structure
        {compound_name: {'value': loading of compound as above, 'formula': chemical formula, use phreeqc notation, (optional)'mw': moleculare weight of formula }
        When fromula is provided and mw is not provided, molmass package will be used to update the mw in the loaded SOLUTION_MASTER_SPECIES database
        for reporting in g/kgw in solution composition, if molmass fails, please provide mw manually.

        The two structures can be mixed and matched, eg.
        {Na:1, HCO3:{'value':1,'formula':CaCO3, 'mw': 50.04}}
        For debuging solution composition please check the sent command by via print_log after building the solution

        Keyword arguments:
        input_composotion -- dictionary for input compositon
        solution_number -- solution number being generated (default 1)
        pH -- solution pH (defualt 7)
        temperature -- solution temp in degrees C (default 25)
        pe -- solution pe - only needed for redox couples(default 4)
        redox -- redoux couple (default pe)
        pressure -- pressure of solution in atm (deafult 1)
        units -- units for input ions, can be any combionations of mass and volume units (defualt g/kgw)
        density -- density of solution, it will be calculated if database supports such calculations (default 1)
        charge_balance -- ion on which to perform the charge balance, needs to use phreeqc notation (default "Cl)
        water_mass -- mass of water in solution in kg (default 1)
        assume_alkalinity -- assume if HCO is provided its alkalinity, if TRUE include Alkalinity and C(4) with same concetraiton
        in solutin composition as HCO3 or CaCO3,
        note when CaCO3 phreeqc will use mw of 50.4 g/mol for it, and so will be mw in database (default True)

        """
        self.input_composotion_raw = input_composotion
        self.input_composotion = self.build_ion_dict(
            input_composotion, assume_alkalinity=assume_alkalinity
        )
        self.water_mass = water_mass
        self.current_solution = solution_number

        self.composition = "SOLUTION {}\n".format(solution_number)
        self.composition += "   temp {}\n".format(temperature)
        self.composition += "   pressure {}\n".format(pressure)
        if charge_balance == "pH":
            self.composition += "   pH {} charge\n".format(pH)
        else:
            self.composition += "   pH {}\n".format(pH)
        self.composition += "   pe {}\n".format(pe)
        self.composition += "   units {}\n".format(units)
        self.composition += "   density {} calc\n".format(density)
        # self.composition += "   alk {} calc\n".format(density)

        for key, concentration in self.input_composotion.items():
            if key == charge_balance:
                charge = "charge"
            else:
                charge = ""
            # print("concentration", concentration)
            if isinstance(concentration, dict):
                if "compound" in concentration:
                    self.composition += "   {element}   {concentration} as {compound} {charge}\n".format(
                        element=key,
                        concentration=concentration["value"],
                        charge=charge,
                        compound=concentration["compound"],
                    )
                else:
                    self.composition += (
                        "   {element}   {concentration}    {charge}\n".format(
                            element=key,
                            concentration=concentration["value"],
                            charge=charge,
                        )
                    )

            else:
                self.composition += (
                    "   {element}   {concentration}    {charge}\n".format(
                        element=key, concentration=concentration, charge=charge
                    )
                )

        self.composition += "   -water  {} # kg\n".format(water_mass)
        self.composition += "SAVE SOLUTION {}\n".format(self.current_solution)
        self.composition += "END\n"

        self.run_string(self.composition)
        self.db_metadata[
            "MAJOR_SOLUTION_COMPONENTS"
        ] = self.phreeqc.get_component_list()
        self.get_solution_state()

    def perform_reaction(
        self,
        solution_number=None,
        ph_adjust=None,
        reactants=None,
        temperature=None,
        pressure=None,
        evaporate_water_mass_percent=None,
        report=False,
    ):
        """
        Method for performing reaciton. ensure your reactant is present in defined_reactants.yaml in databases directory

        For reactants specifiy a dict with following structure
            to add specific amount of reactant use reactants key word {reactant:amount in mg/kgw}

        To adjust to specific pH use ph_adjust useing dict entery as {'reactant': reactant formula, 'ph':pH target}, if reactant is not specified will either use HCL or NaOH

        example for multiple reactants
        {{'HCl':100},{'NaOH':10}}
        only single pH adjust reactant can be used

        can enter ph_adjust and reacatant at same time but verify phreeqc can handle the calculation

        Keyword arguments:
        solution_number -- user provided solution nubmer to use (default None)
        reactant -- reactant use, should be a dict that includes reactant name and either mass or pH target,
        can contain multiple reactants {reactant:amount in mg} (default None)
        ph_adjust -- ph adjustant to use and target {'reactant': reactant formula, 'ph':pH target} (default None)
        pressure -- reaction pressure (default None)
        temperature -- reaction temperature (default None)
        evaporate_water_mass_percent -- percent of water to remove from solution (default None)
        report -- print out titration results (default False)
        """
        if solution_number == None:
            solution_number = self.current_solution

        command = ""
        command += "USE SOLUTION {}\n".format(self.current_solution)
        # self.current_reaction += 1
        if temperature is not None:
            command += "REACTION_TEMPERATURE\n"
            command += "   {}\n".format(temperature)
        if pressure is not None:
            command += "REACTION_PRESSURE \n"
            command += "   {}\n".format(pressure)
        # if reactants is not None or evaporate_water_mass_percent is not None:
        if reactants is not None:
            command = self._gen_reaction_command(command, reactants)
        if evaporate_water_mass_percent is not None:
            command = self._gen_evap_command(command, evaporate_water_mass_percent)
        if ph_adjust is not None:
            command = self._gen_titration_command(command, ph_adjust)

        command += "SELECTED_OUTPUT\n"
        command += " -equilibrium_phases Fix_H+ Fix_OH-\n"
        self.current_solution += 1
        command += "SAVE SOLUTION {}\n".format(self.current_solution)
        command += "END\n"

        self.run_string(command)
        reaction_dict = {}

        # if ph_adjust is not None:
        result = self.phreeqc.get_selected_output_array()

        if ph_adjust is not None:
            idx = np.where("d_Fix_H+" == np.array(result[0]))[0][0]
            reaction_dict = self.set_titrant_dict(
                reaction_dict, "acid", result[1][idx] * -1
            )
            idx = np.where("d_Fix_OH-" == np.array(result[0]))[0][0]
            reaction_dict = self.set_titrant_dict(
                reaction_dict, "base", result[1][idx] * -1
            )
        idx = np.where("pH" == np.array(result[0]))[0][0]
        reaction_dict["pH"] = {"value": result[1][idx]}

        if report:
            print("titration results---------")
            for key, result in reaction_dict.items():
                print("\t", key, result)
        return reaction_dict

    def _gen_evap_command(self, command, evaporate_water_mass_percent):
        command += "REACTION 1\n"
        mass_water_removal = self.water_mass * evaporate_water_mass_percent / 100

        mole_reactant = mass_water_removal * 1000 / 18.01528
        self.water_mass -= mass_water_removal
        command += "    H2O -{mole_reactant}\n".format(mole_reactant=mole_reactant)
        return command

    def _gen_reaction_command(self, command, reactants):
        command += "REACTION 2\n"
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
        command += "   Fix_H+ -{ph_target} {acid_titrant}\n".format(
            ph_target=ph_target, acid_titrant=acid_titrant
        )
        return command

    def _gen_base_adjust(self, command, ph_target, base_titrant):
        command += "PHASES\n"
        command += "Fix_OH-\n"
        command += "   OH-=OH-\n"
        command += "EQUILIBRIUM_PHASES \n"
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

    def get_solution_state(
        self,
        solution_number=None,
        report=False,
        units=True,
        return_above=1e-16,
        return_input_names=True,
    ):
        """Method for getting solution state.
        This will get the state of current active solution or
        provided solution number and return solution information including
        alkalinity, temperature, ph, ionic strength, charge balance, error in charge balance
        molalaitys of species and sub-species, and pre-scailing tendecies

        Keyword arguments:
        solution_number -- user provided solution nubmer to use (default None)
        report -- to print aquired data into consol (default False)
        units -- to convert molalities for major species from mol/kgw to g/kgw. If MW is not avaialble will reutrn mol/kg
        refer to units in returned dict (default True)
        return_above -- only returns molalaties that are above provided value (default 1e-16)
        return_input_names -- uses formulas provided by input dict when generating solution, if false, will return
        specie names as defined by phreeqc used database (deafult True)

        """
        if solution_number == None:
            solution_number = self.current_solution
        command = "USE SOLUTION {}\n".format(str(solution_number))
        command += "EQUILIBRIUM_PHASES\n"
        command += "SELECTED_OUTPUT\n"
        command += " -alkalinity true\n"
        command += " -temperature true\n"
        command += " -ionic_strength true\n"
        command += " -charge_balance true\n"
        command += " -water true\n"
        command += " -percent_error true\n"
        command += " -saturation_indices "
        for key in self.db_metadata["CHECK_PHASE_LIST"]:
            command += key + " "
        command += "\n"
        command += " -totals"
        for element, name in self.forward_dict.items():
            command += " {} ".format(name)
        command += "\n"
        command += " -molalities"
        for element, name in self.return_dict.items():
            for spc in self.db_metadata["SOLUTION_SPECIES"][element]["sub_species"]:
                command += " {} ".format(spc)
        command += "\n"
        command += "END\n"

        self.run_string(command)
        result = self.phreeqc.get_selected_output_array()

        solution_composition = {}
        solution_composition = self._get_scaling_tendencies(
            result,
        )
        solution_composition["composition"] = self._get_solution_comp(
            result,
            return_input_names=return_input_names,
            units=units,
            return_above=return_above,
        )
        if report:
            print("solution state--------------")
            for key, state in solution_composition["solution_state"].items():
                print("\t", key, state["value"])
            print("ion composion------------------")
            for ion, mass in solution_composition["composition"].items():
                print(
                    ion,
                    mass["value"],
                    mass["unit"],
                    "original input",
                    self.input_composotion[self.forward_dict[ion]]["value"],
                    "diff-assumed same units! (%)",
                    (
                        mass["value"]
                        - self.input_composotion[self.forward_dict[ion]]["value"]
                    )
                    / self.input_composotion[self.forward_dict[ion]]["value"]
                    * 100,
                )
                for sub, values in mass["sub_species"].items():
                    print("\t", sub, values["value"], values["unit"])
            print("scaling tendendencies------------------")
            for scalant, SI in solution_composition["scaling_tendencies"].items():
                if scalant == "max":
                    print("\t", scalant, SI["value"], SI["scalant"])
                else:
                    print("\t", scalant, SI["value"])
        return solution_composition

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
                            "unit": unit,
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
            aque_species_comp[vals["input_name"]]["unit"] = unit
        return aque_species_comp

    def form_percipitants(
        self,
        solution_number=None,
        phases=None,
        store_solution=True,
        return_non_zero=False,
        force_all_phases_in_db=False,
        report=False,
    ):
        """Method for getting solution state.
        This method will percipitate all formed phases from solution (changing composition)
        if you want to perform the percipitaiton but not affect solution, set store_solution=False
        to only percipitate specific phase provide phase name using same nomeclature as in PHASES metedata yaml
        in /databases/metadata

        Keyword arguments:
        solution_number -- user provided solution nubmer to use (default None)
        phaes -- specifiy phases to percipiate out, if none, will get all available phases (default None)
        store_solution -- save solution after percipiation with new sol number (default True)
        return_non_zero -- only return phases that percipaited (default False)
        force_all_phases_in_db -- if  true, will get all phases avaiable in database and
        not just those reported as available by phreeqc (default False)
        report -- print out results (default False)
        """
        if solution_number == None:
            solution_number = self.current_solution
        if phases is None:
            phases = list(self.db_metadata["PRESENT_PHASES_IN_SOLUTION"])
            if force_all_phases_in_db:
                phases = list(self.db_metadata["PHASES"].keys())
        command = "USE SOLUTION {}\n".format(self.current_solution)
        command += "EQUILIBRIUM_PHASES\n"
        for phase in phases:
            command += "    {}  0   0\n".format(phase)
        command += "SELECTED_OUTPUT\n"
        command += "-equilibrium_phases"
        for phase in phases:
            command += " {}".format(phase)
        command += "\n"
        if store_solution:
            self.current_solution += 1
            command += "SAVE SOLUTION {}\n".format(self.current_solution)
        command += "END\n"
        self.run_string(command)
        result = self.phreeqc.get_selected_output_array()
        percip_result = {}
        # print(result)
        for k in phases:
            idx = np.where(k == np.array(result[0]))[0][0]
            idx_d = np.where("d_" + k == np.array(result[0]))[0][0]
            mols = result[1][idx_d]
            if return_non_zero:
                if mols > 0:
                    percip_result[k + "(mol/kgw)"] = {
                        "value": result[1][idx_d] / self.water_mass,
                        "unit": "mol/kgw",
                    }
            elif mols > -999:
                percip_result[k + "(mol/kgw)"] = {
                    "value": result[1][idx_d] / self.water_mass,
                    "unit": "mol/kgw",
                }
        if report:
            print("precip results--------------------")
            for phase, amount in percip_result.items():
                print("\t", phase, amount)
        return percip_result

    def get_vapor_pressure(self, report):
        gas_phases = []
        gas_header = []

        for phase in list(self.db_metadata["PHASES"].keys()):
            if "(g)" in phase:
                gas_phases.append(phase)
                gas_header.append("fugacity_{}".format(phase))
        # print(gas_phases)
        command = "USE SOLUTION {}\n".format(self.current_solution)
        command += "GAS_PHASE 1\n"
        command += "   -fixed_volume\n"
        for g in gas_phases:
            command += "    {}\n".format(g)
        command += "   -fixed_volume\n"
        # command += "END\n"
        # command += "USE REACTION\n"  # .format(self.current_solution)
        # command += "USE gas_phase 1\n"
        #        command += "REACTION_TEMPERATURE\n"
        #       command += "   {}\n".format(temperture)
        # command += "END\n"
        command += "USER_PUNCH\n"
        command += "-start\n"
        command += "-headings {}\n".format(" ".join(gas_header))
        for i, g in enumerate(gas_phases):
            command += '{} PUNCH SR("{}")\n'.format(int(i * 10), g)
        command += "-end\n"
        command += "SELECTED_OUTPUT\n"
        command += "   -gases {}".format(" ".join(gas_phases))
        command += "   -user_punch True"
        command += "END\n"
        self.run_string(command)
        result = self.phreeqc.get_selected_output_array()
        out_dict = {}
        # print(result)
        total = 0
        for k in gas_phases:
            # print("fugacity_{}".format(k))
            idx = np.where("fugacity_{}".format(k) == np.array(result[0]))[0][0]
            out_dict[k] = result[1][idx]
            total += result[1][idx]
        out_dict["total_fugacity"] = total
        if report:
            print("vapor pressures-----------")
            for comp, vapor in out_dict.items():
                print("\t", comp, vapor)
        # print("vapor", out_dict)  # , result[1][idx])
        return out_dict

    def _get_scaling_tendencies(self, result, report=False):
        result_dict = {}
        # print(result)
        self.db_metadata["PRESENT_PHASES_IN_SOLUTION"] = []
        for phase in self.db_metadata["PHASES"].keys():
            # print(result[0])

            p_idx = np.where(np.array(result[0]) == "si_" + phase)[0]
            # print(p_idx)
            if p_idx.size > 0:
                si = result[1][p_idx[0]]
                if float(si) > -999:
                    result_dict[phase] = {
                        "value": 10 ** (float(si)),
                        "unit": "dimensionless",
                    }
                    self.db_metadata["PRESENT_PHASES_IN_SOLUTION"].append(phase)
        results_dict = {}
        results_dict["scaling_tendencies"] = result_dict
        results_dict["solution_state"] = {}
        for sol_state in [
            ["pH", "pH"],
            ["pe", "pe"],
            ["temp(C)", "temperature (degree C)"],
            ["Alk(eq/kgw)", "Alkalinity (g/kgw)"],
            ["charge(eq)", "charge balance (eq)"],
            ["pct_err", "Error in charge (%)"],
            ["mass_H2O", "Water mass (kg)"],
        ]:
            idx = np.where(sol_state[0] == np.array(result[0]))[0][0]
            val = result[1][idx]
            if sol_state[0] == "Alk(eq/kgw)":
                multiplier = self.db_metadata["SOLUTION_MASTER_SPECIES"]["Alkalinity"][
                    "mw"
                ]
                formula = self.db_metadata["SOLUTION_MASTER_SPECIES"]["Alkalinity"][
                    "formula"
                ]
                val = val * multiplier
                sol_state[1] = "Alkalinity (g as {}/kgw)".format(formula)
            results_dict["solution_state"][sol_state[1]] = {"value": val}
        self.water_mass = results_dict["solution_state"]["Water mass (kg)"]["value"]
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
