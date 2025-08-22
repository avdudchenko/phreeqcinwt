from phreeqcinwt.phreeqc_wt_api import phreeqcWTapi
import numpy as np
import pandas as pd


if __name__ == "__main__":
    phreeqcWT = phreeqcWTapi(database="pitzer.dat")  # , ignore_phase_list=["Dolomite"])
    # phreeqcWT = phreeqcWTapi(database="phreeqc.dat")
    # phreeqcWT = phreeqcWTapi(database="minteq.v4.dat")
    RO1_perm = 367/35000

    # B_conc = np.linspace(0,0.01,22)
    pH_outlet = np.linspace(8,12,41)
    pH_perm = np.linspace(4,7,31)

    # pH_swing_data_pH_perm = np.zeros((len(B_conc),len(pH_outlet)))
    # pH_swing_data_pH_outlet = np.zeros((len(B_conc),len(pH_outlet)))
    # pH_swing_data_NaOH = np.zeros((len(B_conc),len(pH_outlet)))
    pH_swing_data_overall = np.zeros((41*31,3))

    q = 0

    k = 0
    for l in pH_perm:
        i = 0
        for n in pH_outlet:
            input_composotion = {
                "Na": 10.556*RO1_perm,
                "K": 0.380*RO1_perm,
                "Cl": 18.980*RO1_perm,
                "Ca": 0.4*RO1_perm,
                "Mg": 1.262*RO1_perm,
                "HCO3": 0.140*RO1_perm,
                "SO4": 2.649*RO1_perm,
                "B": 0.005,
                "Br": .065*RO1_perm,
                "Sr": .013*RO1_perm,
                # "C": 0.258,
                # "C": {"value": 0.385, "compound": "HCO3-"},
                # "Alkalinity": {"value": 0.381, "compound": "HCO3-"},
            }

            phreeqcWT.build_water_composition(
                input_composotion=input_composotion,
                charge_balance="Cl",
                pH=l,
                pe=4,
                units="g/kgw",
                pressure=1,
                temperature=25,
                assume_alkalinity=False,
            )
            
            titrant_dict = phreeqcWT.perform_reaction(
                ph_adjust={"pH": n, "reactant": "NaOH"}, pressure=1, report=False
            )
            pH_swing_data_overall[q,0] = l
            pH_swing_data_overall[q,1] = titrant_dict["NaOH"]["value"]
            pH_swing_data_overall[q,2] = titrant_dict["pH"]["value"]

            # pH_swing_data_NaOH[j,i] = titrant_dict["NaOH"]["value"]
            # pH_swing_data_pH_outlet[j,i] = titrant_dict["pH"]["value"]
            q = q + 1
            i = i + 1
    
    k = k + 1

# df_NaOH = pd.DataFrame(pH_swing_data_NaOH)
# df_NaOH.to_csv("phreeqc_pH_swing_data_NaOH_test_adj_int_pH.csv")
# df = pd.DataFrame(pH_swing_data_pH_outlet)
# df.to_csv("phreeqc_pH_swing_data_pH.csv")
# print(pH_swing_data_NaOH)

print(pH_swing_data_overall)

df_all = pd.DataFrame(pH_swing_data_overall,columns=["pH_perm","NaOH mg/kg w","pH_outlet"] )
df_all.to_csv("pH_swing_data_overall")
print(df_all)