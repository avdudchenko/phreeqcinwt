import yaml
import csv
import molmass
import phreeqcinwt.phreeqc_wt_api as phapi
import os


class dataBaseManagment:
    def load_database(self, remove_phase_list):
        if self.cwd is None:
            self.cwd = os.path.dirname(phapi.__file__) + "/"
        db_file = self.cwd + "databases/" + self.database
        print("Loading database file: {}".format(db_file))
        if remove_phase_list is not None:
            db_string = self.remove_phases_from_db(db_file, remove_phase_list)
            self.phreeqc.load_database_string(db_string)
        else:
            self.phreeqc.load_database(db_file)
        result = self.phreeqc.get_component_list()

        self.db_metadata = {
            "PHASES": {},
            "DEFINED_REACTANTS": {},
            "SOLUTION_MASTER_SPECIES": {},
        }
        states = self.load_db_metadata()
        if (
            self.db_metadata["PHASES"] == {}
            or self.db_metadata["SOLUTION_MASTER_SPECIES"] == {}
            or any(self.rebuild_metadata)
        ):
            if self.rebuild_metadata[0]:
                self.db_metadata["SOLUTION_MASTER_SPECIES"] = {}
            if self.rebuild_metadata[2]:
                self.db_metadata["PHASES"] = {}
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
                cur_phase = None
                for row in reader:
                    # print(row, len(row) == 0, found_phases)
                    if found_phases and "SURFACE_MASTER_SPECIES" in str(row):
                        found_phases = False
                    if found_master_species and "SOLUTION_SPECIES" in str(row):
                        # print(row)
                        found_master_species = False
                    if "PHASES" in str(row):
                        found_species = False
                    if "EXCHANGE_MASTER_SPECIES" in str(row):
                        found_phases = False
                    if (found_master_species and self.rebuild_metadata[0]) or (
                        found_master_species and states["SOLUTION_MASTER_SPECIES"]
                    ):
                        if "#" not in str(row) and "SOLUTION_SPECIES" not in str(row):

                            clean_row = []
                            for r in row:
                                sr = r.split(" ")
                                for s in sr:
                                    if s != "":
                                        clean_row.append(s)
                            # print(clean_row)
                            if clean_row != []:
                                try:
                                    float(clean_row[3])
                                    formula = clean_row[1].split("-")[0]
                                    formula = formula.split("+")[0]
                                except:
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
                                        if formula == "Ca0.5(CO3)0.5":
                                            mw = 50.04

                                self.db_metadata["SOLUTION_MASTER_SPECIES"][ion] = {
                                    "formula": formula,
                                    "species": species,
                                    "mw": mw,
                                }

                    if (found_phases and self.rebuild_metadata[2]) or (
                        found_phases and states["PHASES"]
                    ):
                        if row != [] and "PITZER" not in str(row):
                            if (
                                len(row[0]) > 1
                                and "#" not in str(row)
                                and row[0].split(" ")[0]
                                not in "-log_k,-delta_h,-delta_H,-analytic,-Vm,-T_c,-Omega,-P_c,-analytical_expression"
                            ):
                                split_row = row[0].split(" ")[0]
                                self.db_metadata["PHASES"][
                                    (split_row.replace(" ", ""))
                                ] = {}
                                cur_phase = split_row.replace(" ", "")
                            elif "PHASES" not in str(row):
                                reaction = row[0].split(" ")
                                if (
                                    reaction[0] == ""
                                    or reaction[0]
                                    not in "-log_k,-delta_h,-delta_H,-analytic,-Vm,-T_c,-Omega,-P_c,-analytical_expression"
                                ) and "=" in str(row):
                                    if len(row) > 1:
                                        l, r = row[1].split("=")
                                    else:
                                        l, r = row[0].split("=")
                                    formula = l.split("+")[0]
                                    formula = formula.replace(" ", "")
                                    try:
                                        mw = molmass.Formula(formula).mass
                                    except:
                                        mw = None
                                    self.db_metadata["PHASES"][cur_phase] = {
                                        "formula": formula,
                                        "mw": mw,
                                    }
                    if "SOLUTION_MASTER_SPECIES" in str(row):
                        # print(row)
                        found_master_species = True
                        # print("fms")
                    if "PHASES" in str(row):
                        found_phases = True
                        # print("fp")
                    if "PITZER" in str(row):
                        found_phases = False
            self.save_db_metadata()

    # self.phreeqc.load_database(db_file.stirp(".dat") + "_mod.dat")
    # print(self.db_metadata["SOLUTION_SPECIES"])
    # print(self.db_metadata["SOLUTION_MASTER_SPECIES"])
    def remove_phases_from_db(self, db_file, phase_list):
        def check_ignore(line, phase_list):
            found = False
            for phase in phase_list:
                if phase in line:
                    found = True
                    break
            return found

        db_string = ""
        print(phase_list)
        with open(db_file) as database:
            lines = database.readlines()
            found = False
            pass_lines = 0
            for l in lines:
                # print(found)
                if found == False:
                    found = check_ignore(l, phase_list)
                    if found == False:
                        db_string += l
                    else:
                        print("removed from db file: {}".format(l.strip("\n")))
                elif found and l[0:1].isspace():
                    print("removed from db file: {}".format(l.strip("\n")))
                else:
                    found = False
                    db_string += l
        # )
        return db_string

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
            print(dbm_dir)
            try:
                with open(dbm_dir, "r") as file_save:
                    self.db_metadata[key] = yaml.safe_load(file_save)

                    print("Loaded file", key)
            except:
                print("Failed to load {}".format(key))
            if self.db_metadata[key] == {}:
                states[key] = True
            else:
                states[key] = False
        return states
