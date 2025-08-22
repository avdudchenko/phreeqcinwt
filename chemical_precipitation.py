from phreeqcinwt.phreeqc_wt_api import phreeqcWTapi
import numpy as np
import pandas as pd
import json


if __name__ == "__main__":
    phreeqcWT = phreeqcWTapi(database="pitzer.dat")  # , ignore_phase_list=["Dolomite"])

    pH_outlet = np.linspace(9,10.5,15) # for Calcite production, 9 < pH < 10
    data = {}

    i = 0
    for n in pH_outlet:
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
        
        titrant_dict = phreeqcWT.perform_reaction(
            ph_adjust={"pH": n, "reactant": "Na2CO3"}, pressure=1, report=True
        )
        phase_dict = phreeqcWT.form_phases(return_non_zero=True,report=True)

        data[n] = {'dose':titrant_dict['Na2CO3'],'precip':phase_dict}
             
            
        i = i + 1


# Save the dictionary to a file
with open('data_chem_precip_Na2CO3.json', 'w') as f:
    json.dump(data, f, indent=4) # indent=4 makes the JSON file more readable

