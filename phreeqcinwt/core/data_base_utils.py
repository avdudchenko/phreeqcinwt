import yaml
import csv
import molmass
import phreeqcinwt.phreeqc_wt_api as phapi
import os


class dataBaseManagment:
    def load_database(self):
        if self.cwd is None:
            self.cwd = os.path.dirname(phapi.__file__) + "/"
        db_file = self.cwd + "databases/" + self.database
        self.phreeqc.load_database(db_file)
        result = self.phreeqc.get_component_list()

        self.db_metadata = {
            "PHASES": {},
            "DEFINED_REACTANTS": {},
            "SOLUTION_MASTER_SPECIES": {},
            "SOLUTION_SPECIES": {},
        }
        states = self.load_db_metadata()
        if (
            self.db_metadata["PHASES"] == {}
            or self.db_metadata["SOLUTION_MASTER_SPECIES"] == {}
            or any(self.rebuild_metadata)
        ):
            if self.rebuild_metadata[0]:
                self.db_metadata["SOLUTION_MASTER_SPECIES"] = {}
            if self.rebuild_metadata[1]:
                self.db_metadata["SOLUTION_SPECIES"] = {}
            if self.rebuild_metadata[2]:
                self.db_metadata["PHASES"] = {}
            # print(self.db_metadata["SOLUTION_MASTER_SPECIES"])
            with open(db_file) as database:
                try:
                    reader = csv.reader(database, delimiter="\t")
                except:
                    raise (
                        "Cound not find the database {}, please verify it exists".format(
                            db_file
                        )
                    )
                found_phases = False
                found_master_species = False
                found_species = False
                for row in reader:
                    # print(row, len(row) == 0, found_phases)
                    if (
                        found_phases
                        and len(row) == 0
                        or "SURFACE_MASTER_SPECIES" in str(row)
                    ):
                        found_phases = False
                    if (
                        found_master_species
                        and len(row) == 0
                        or "SOLUTION_SPECIES" in str(row)
                    ):
                        found_master_species = False
                    if "PHASES" in str(row):
                        found_species = False
                    if "EXCHANGE_MASTER_SPECIES" in str(row):
                        found_phases = False
                    if (found_master_species and self.rebuild_metadata[0]) or (
                        found_master_species and states["SOLUTION_MASTER_SPECIES"]
                    ):
                        if "#" not in str(row) and "SOLUTION_SPECIES" not in str(row):
                            # print(row)
                            clean_row = []
                            for r in row:
                                sr = r.split(" ")
                                for s in sr:
                                    if s != "":
                                        clean_row.append(s)
                            print(clean_row)
                            if clean_row != []:
                                formula = clean_row[3]
                                species = clean_row[1]
                                ion = clean_row[0]
                                try:
                                    mw = float(row[-1])
                                except:
                                    try:
                                        mw = molmass.Formula(formula).mass
                                    except:
                                        mw = None

                                self.db_metadata["SOLUTION_MASTER_SPECIES"][ion] = {
                                    "formula": formula,
                                    "species": species,
                                    "mw": mw,
                                }

                            # p#rint(self.db_metadata["SOLUTION_SPECIES"])
                            # ass
                    # print(row)
                    if (found_species and self.rebuild_metadata[1]) or (
                        found_species and states["SOLUTION_SPECIES"]
                    ):
                        if (
                            "#" not in str(row)
                            and "SOLUTION_SPECIES" not in str(row)
                            and row != []
                        ):
                            # print(row)
                            if row[0] != "":
                                split_equation = row[0].split(" ")
                                for comp in split_equation:
                                    if comp != "+" or comp != "-" or comp != "=":
                                        for specie, items in self.db_metadata[
                                            "SOLUTION_SPECIES"
                                        ].items():
                                            if (
                                                items["formula"] in comp
                                                and comp
                                                not in self.db_metadata[
                                                    "SOLUTION_SPECIES"
                                                ][specie]["sub_species"]
                                            ):
                                                self.db_metadata["SOLUTION_SPECIES"][
                                                    specie
                                                ]["sub_species"].append(comp)
                                        # print("ss")
                    if (found_phases and self.rebuild_metadata[2]) or (
                        found_phases and states["PHASES"]
                    ):
                        print(row)
                        if row != []:
                            if len(row[0]) > 1 and "#" not in str(row):
                                self.db_metadata["PHASES"][
                                    (row[0].replace(" ", ""))
                                ] = {}
                                cur_phase = row[0].replace(" ", "")
                            elif "#" not in str(row) and "PHASES" not in str(row):
                                reaction = row[1].split(" ")
                                if (
                                    reaction[0]
                                    not in "-log_k,-delta_h,-delta_H,-analytic,-Vm,-T_c,-Omega,-P_c,-analytical_expression"
                                ):
                                    print(row)
                                    l, r = row[1].split(" = ")
                                    formula = l.split(" ")[0]
                                    # print(cur_phase, formula)  # , r)
                                    try:
                                        mw = molmass.Formula(formula).mass
                                    except:
                                        mw = None
                                    self.db_metadata["PHASES"][cur_phase] = {
                                        "formula": formula,
                                        "mw": mw,
                                    }
                    if "SOLUTION_MASTER_SPECIES" in str(row):
                        found_master_species = True
                        print("fms")
                    if "PHASES" in str(row):
                        found_phases = True
                        print("fp")
                    if "SOLUTION_SPECIES" in str(row):
                        for name, item in self.db_metadata[
                            "SOLUTION_MASTER_SPECIES"
                        ].items():
                            species = item["species"]
                            if species != "e-":
                                unched_specie = species
                                for charge in range(-10, 0):
                                    if charge < -1:
                                        charge = str(charge)
                                    elif charge == -1:
                                        charge = "-"
                                    elif charge == +1:
                                        charge = "+"
                                    else:
                                        charge = "+" + str(charge)
                                    unched_specie = unched_specie.replace(
                                        str(charge), ""
                                    )
                                    # print(unched_specie, charge)
                                for charge in list(range(0, 10))[::-1]:
                                    if charge < -1:
                                        charge = str(charge)
                                    elif charge == -1:
                                        charge = "-"
                                    elif charge == +1:
                                        charge = "+"
                                    else:
                                        charge = "+" + str(charge)
                                    unched_specie = unched_specie.replace(
                                        str(charge), ""
                                    )

                                self.db_metadata["SOLUTION_SPECIES"][species] = {
                                    "formula": unched_specie,
                                    "sub_species": [],
                                }
                        found_species = True
                        # print("ss")
            self.save_db_metadata()

        # print(self.db_metadata["SOLUTION_SPECIES"])
        # print(self.db_metadata["SOLUTION_MASTER_SPECIES"])

    def save_db_metadata(self):
        dbm_dir = self.cwd + "databases/metadata/" + self.database.strip(".dat")
        for key, data in self.db_metadata.items():
            if key != "DEFINED_REACTANTS":
                with open(dbm_dir + "_" + key + ".yaml", "w") as file_save:
                    setup = yaml.dump(data, file_save, sort_keys=False)

    def load_db_metadata(self):
        states = {}
        for key, item in self.db_metadata.items():
            if key == "DEFINED_REACTANTS":
                dbm_dir = self.cwd + "databases/defined_reactants.yaml"
            else:
                dbm_dir = (
                    self.cwd
                    + "databases/metadata/"
                    + self.database.strip(".dat")
                    + "_"
                    + key
                    + ".yaml"
                )

            try:
                with open(dbm_dir, "r") as file_save:
                    self.db_metadata[key] = yaml.safe_load(file_save)

                    print("Loaded filw", key)
            except:
                print("Failed to load {}".format(key))
            if self.db_metadata[key] == {}:
                states[key] = True
            else:
                states[key] = False
        return states
