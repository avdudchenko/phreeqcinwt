from phreeqcinwt.phreeqc_wt_api import phreeqcWTapi
import numpy as np
import pandas as pd
import json


if __name__ == "__main__":
    phreeqcWT = phreeqcWTapi(database="pitzer.dat")  # , ignore_phase_list=["Dolomite"])

    T_outlet = np.linspace(25,85,12)
    data = {}

    i = 0
    for n in T_outlet:
        # basic brackish water
        input_composotion = {
            "Na": 0.739,
            "K": 0.009,
            "Cl": 0.870,
            "Ca": 0.258,
            "Mg": 0.090,
            "HCO3": 0.385,
            "SO4": 1.011,
            # "C": 0.258,
            # "C": {"value": 0.385, "compound": "HCO3-"},
            # "Alkalinity": {"value": 0.381, "compound": "HCO3-"},
        }


        phreeqcWT.build_water_composition(
            input_composotion=input_composotion,
            charge_balance="Cl",
            pH=7,
            pe=0,
            units="g/kgw",
            pressure=1,
            temperature=20,
            assume_alkalinity=True,
        )
        
        phreeqcWT.get_solution_state(report=False)
        init_enth = phreeqcWT.get_enthalpy_phase()

        phreeqcWT.perform_reaction(temperature=n,)
        exit_enth = phreeqcWT.get_enthalpy_phase()
        
        phase_dict = phreeqcWT.form_phases(return_non_zero=True,report=True)

        # data[n] = {'delta_H': exit_enth-init_enth,'precip':phase_dict}
             
            
        i = i + 1


# Save the dictionary to a file
with open('data_therm_precip.json', 'w') as f:
    json.dump(data, f, indent=4) # indent=4 makes the JSON file more readable






# print(data)

# df_all = pd.DataFrame(data,columns=["pH_perm","NaOH mg/kg w","pH_outlet"] )
# df_all.to_csv("pH_swing_data_overall")
# print(df_all)