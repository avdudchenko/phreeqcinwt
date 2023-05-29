from phreeqcinwt.phreeqc_wt_api import phreeqcWTapi

from watertap.property_models.multicomp_aq_sol_prop_pack import (
    MCASParameterBlock,
    ActivityCoefficientModel,
    DensityCalculation,
)
import idaes.core.util.scaling as iscale
from idaes.core.solvers import get_solver
from pyomo.environ import (
    ConcreteModel,
    value,
    Constraint,
    Objective,
    Param,
    TransformationFactory,
    assert_optimal_termination,
)


def build(comp_dict):
    m = ConcreteModel()
    m.properties = MCASParameterBlock(**default)
    m.block = m.properties.build_state_block([0])
    # m.block[0].conc_mass_phase_comp[...]
    # m.block[0].mass_frac_phase_comp[...]
    m.block[0].flow_mol_phase_comp[...]
    m.block[0].flow_mass_phase_comp[...]
    return m


def get_netural_concetration(m, comp_dict, balance_ion="Cl"):
    total_mass = 1000
    for ion, mass_loading in comp_dict.items():
        total_mass += mass_loading
    print(total_mass)
    m.block[0].flow_mass_phase_comp["Liq", "H2O"].fix(1)
    m.block[0].flow_mol_phase_comp["Liq", "H2O"].unfix()
    for ion, mass_loading in comp_dict.items():
        # print(ion)
        # m.block[0].mass_frac_phase_comp.display()
        m.block[0].flow_mass_phase_comp["Liq", ion].fix(mass_loading / 1000)
        m.block[0].flow_mol_phase_comp["Liq", ion].unfix()
        iscale.set_scaling_factor(
            m.block[0].mass_frac_phase_comp["Liq", ion],
            1 / (mass_loading / 1000),
        )

    iscale.calculate_scaling_factors(m)
    solver = get_solver()
    solver.solve(m)
    m.block[0].display()
    m.block[0].flow_mass_phase_comp["Liq", "H2O"].unfix()
    m.block[0].flow_mol_phase_comp["Liq", "H2O"].fix()
    for ion, mass_loading in comp_dict.items():
        m.block[0].flow_mol_phase_comp["Liq", ion].fix()
        m.block[0].flow_mass_phase_comp["Liq", ion].unfix()
    if ion == balance_ion:
        m.block[0].flow_mol_phase_comp["Liq", balance_ion].unfix()
    m.block[0].assert_electroneutrality(
        defined_state=True,
        adjust_by_ion=balance_ion,
        get_property="flow_mol_phase_comp",
    )
    return_dict = {}
    m.block[0].display()
    water_mass = m.block[0].flow_mass_phase_comp["Liq", "H2O"].value
    for ion, mass_loading in comp_dict.items():
        return_dict[ion] = (
            m.block[0].flow_mass_phase_comp["Liq", ion].value * 1000 / water_mass
        )
    print(return_dict)
    return return_dict


if __name__ == "__main__":
    phreeqcWT = phreeqcWTapi(database="phreeqc.dat")
    # phreeqcWT = phreeqcWTapi(database="minteq.v4.dat")
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
    default = {
        "solute_list": [
            "Ca",
            "SO4",
            "HCO3",
            "Na",
            "Cl",
            "K",
            "Mg",
        ],
        "diffusivity_data": {
            ("Liq", "Ca"): 9.2e-10,
            ("Liq", "SO4"): 1.06e-9,
            ("Liq", "HCO3"): 1.19e-9,
            ("Liq", "Na"): 1.33e-9,
            ("Liq", "Cl"): 2.03e-9,
            ("Liq", "K"): 1.957e-9,
            ("Liq", "Mg"): 0.706e-9,
        },
        "mw_data": {
            "H2O": 18e-3,
            "Ca": 40e-3,
            "HCO3": 61.0168e-3,
            "SO4": 96e-3,
            "Na": 23e-3,
            "Cl": 35e-3,
            "K": 22.989769e-3,
            "Mg": 24.305e-3,
        },
        "stokes_radius_data": {
            "Ca": 0.309e-9,
            "HCO3": 2.06e-10,
            "SO4": 0.230e-9,
            "Cl": 0.121e-9,
            "Na": 0.184e-9,
            "K": 0.125e-9,
            "Mg": 0.347e-9,
        },
        "charge": {
            "Ca": 2,
            "HCO3": -1,
            "SO4": -2,
            "Na": 1,
            "Cl": -1,
            "K": 1,
            "Mg": 2,
        },
        "activity_coefficient_model": ActivityCoefficientModel.ideal,
        "density_calculation": DensityCalculation.constant,
    }

    m = build(default)
    out = get_netural_concetration(m, input_composotion)
    # m.display()
    for ion, loading in out.items():
        input_composotion[ion] = loading
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

    print("-----------------------get intial solution state-----------------------")
    phreeqcWT.get_solution_state(report=True)
    # print("-----------------------soften water useing soda ash-----------------------")
    # phreeqcWT.perform_reaction(reactants={"Na2CO3": 63.22}, report=True)
    # # phreeqcWT.get_solution_state(report=True)
    # phreeqcWT.form_percipitants(report=True)
    # print("-----------------------solution after softeing-----------------------")
    # print("-----------------------add CO2 softeing-----------------------")
    # phreeqcWT.perform_reaction(reactants={"CO2": 145.26}, report=True)
    # print("-----------------------solution after CO2-----------------------")
    # phreeqcWT.get_solution_state(report=True)
    # phreeqcWT.perform_reaction(evaporate_water_mass_percent=72.2)
    # phreeqcWT.get_solution_state(report=True)
    # # phreeqcWT.get_vapor_pressure(report=True)
    # print("-----------------------heat up solution to 90 C-----------------------")

    # phreeqcWT.perform_reaction(temperature=50)
    # phreeqcWT.get_vapor_pressure(report=True)
    # phreeqcWT.get_solution_state(report=True)
    # phreeqcWT.form_percipitants(report=True)
    # phreeqcWT.get_solution_state(report=True)
    # # phreeqcWT.get_solution_state(report=True)
    # # phreeqcWT.perform_reaction(reactants={"CO2": 145.26}, report=True)
    # # phreeqcWT.get_solution_state(report=True)
