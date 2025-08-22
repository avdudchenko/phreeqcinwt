from phreeqcinwt.phreeqc_wt_api import phreeqcWTapi
import numpy as np
import pandas as pd

if __name__ == "__main__":
    phreeqcWT = phreeqcWTapi(database="pitzer.dat")  # , ignore_phase_list=["Dolomite"])
    # phreeqcWT = phreeqcWTapi(database="phreeqc.dat")
    # phreeqcWT = phreeqcWTapi(database="minteq.v4.dat")
    # basic brackish water
    pH_recycle = np.linspace(7.8,11.6,20)
    pH_outlet = np.linspace(4,7,20)
    pH_swing_data_overall = np.zeros((400,4))
    q=0

    for k in pH_recycle:
        for n in pH_outlet:
            input_composotion = {
                    "Na": 10.556,
                    "K": 0.380,
                    "Cl": 18.980,
                    "Ca": 0.4,
                    "Mg": 1.262,
                    "HCO3": 0.140,
                    "SO4": 2.649,
                    "B": 0.005,
                    "Br": .065,
                    "Sr": .013,
                }

            phreeqcWT.build_water_composition(
                input_composotion=input_composotion,
                charge_balance="Cl",
                pH=7.56,
                pe=4,
                units="g/kgw",
                pressure=1,
                temperature=20,
                assume_alkalinity=False,
                solution_number=1,
                water_mass=1.021, 
            )
            rej1 = 0.990
            rej2 = 0.978
            input_composotion = {
                        "Na": 10.556*(1-rej1)*rej2,
                        "K": 0.380*(1-rej1)*rej2,
                        "Cl": 18.980*(1-rej1)*rej2,
                        "Ca": 0.4*(1-rej1)*rej2,
                        "Mg": 1.262*(1-rej1)*rej2,
                        "HCO3": 0.140*(1-rej1)*rej2,
                        "SO4": 2.649*(1-rej1)*rej2,
                        "B": 0.005,
                        "Br": .065*(1-rej1)*rej2,
                        "Sr": .013*(1-rej1)*rej2,
                        # "C": 0.258,
                        # "C": {"value": 0.385, "compound": "HCO3-"},
                        # "Alkalinity": {"value": 0.381, "compound": "HCO3-"},
                    }
            
            phreeqcWT.build_water_composition(
                    input_composotion=input_composotion,
                    charge_balance="Cl",
                    pH=k,
                    pe=4,
                    units="g/kgw",
                    pressure=1,
                    temperature=20,
                    assume_alkalinity=False,
                    solution_number=2,
                    water_mass=0.146,
                    )
            solutin_dict = {1: 1, 2: 1}
            phreeqcWT.mix_solutions(solutin_dict, new_solution_number=3)
            mixed_solution = phreeqcWT.get_solution_state(report=False)

            pH_swing_data_overall[q,0] = k
            pH_swing_data_overall[q,1] = mixed_solution["solution_state"]["pH"]["value"]

            titrant_dict = phreeqcWT.perform_reaction(
                ph_adjust={"pH": n, "reactant": "HCl"}, pressure=1, report=False
            )
            pH_swing_data_overall[q,2] = titrant_dict["HCl"]["value"]
            pH_swing_data_overall[q,3] = titrant_dict["pH"]["value"]

            q = q + 1
    
    print(pH_swing_data_overall)

    df_all = pd.DataFrame(pH_swing_data_overall,columns=["pH_recycle","pH_mix","HCl mg/kg w","pH_outlet"] )
    df_all.to_csv("acidification_data_overall_updated.csv")
    print(df_all)
    
