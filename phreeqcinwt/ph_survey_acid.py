from phreeqcinwt.phreeqc_wt_api import phreeqcWTapi
import numpy as np
import pandas as pd


if __name__ == "__main__":
    phreeqcWT = phreeqcWTapi(database="pitzer.dat")  # , ignore_phase_list=["Dolomite"])
    # phreeqcWT = phreeqcWTapi(database="phreeqc.dat")
    # phreeqcWT = phreeqcWTapi(database="minteq.v4.dat")
    feed_mix = 30808/35000

    pH_outlet = np.linspace(4,7,31)

    pH_swing_data_overall = np.zeros((31,2))

    input_composotion = {
            "Na": 10.556*feed_mix,
            "K": 0.380*feed_mix,
            "Cl": 18.980*feed_mix,
            "Ca": 0.4*feed_mix,
            "Mg": 1.262*feed_mix,
            "HCO3": 0.140*feed_mix,
            "SO4": 2.649*feed_mix,
            "B": 0.005,
            "Br": .065*feed_mix,
            "Sr": .013*feed_mix,
            # "C": 0.258,
            # "C": {"value": 0.385, "compound": "HCO3-"},
            # "Alkalinity": {"value": 0.381, "compound": "HCO3-"},
        }
    

    q = 0
    i = 0
    for n in pH_outlet:
        
        titrant_dict = phreeqcWT.perform_reaction(
            ph_adjust={"pH": n, "reactant": "HCl"}, pressure=1, report=False
        )
        pH_swing_data_overall[q,0] = titrant_dict["HCl"]["value"]
        pH_swing_data_overall[q,1] = titrant_dict["pH"]["value"]

        q = q + 1
        i = i + 1
    

# df_NaOH = pd.DataFrame(pH_swing_data_NaOH)
# df_NaOH.to_csv("phreeqc_pH_swing_data_NaOH_test_adj_int_pH.csv")
# df = pd.DataFrame(pH_swing_data_pH_outlet)
# df.to_csv("phreeqc_pH_swing_data_pH.csv")
# print(pH_swing_data_NaOH)

print(pH_swing_data_overall)

df_all = pd.DataFrame(pH_swing_data_overall,columns=["HCl mg/kg w","pH_outlet"] )
df_all.to_csv("acidification_data_overall")
print(df_all)