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

    water_mass = m.block[0].flow_mass_phase_comp["Liq", "H2O"].value
    for ion, mass_loading in comp_dict.items():
        return_dict[ion] = (
            m.block[0].flow_mass_phase_comp["Liq", ion].value * 1000 / water_mass
        )

    return return_dict


def ion_balance(input_dict, balance_ion="Cl"):
    ion_props = {
        "mw_data": {
            "H2O": 18e-3,
            "Ca": 40.078e-3,
            "HCO3": 61.0168e-3,
            "SO4": 96.06e-3,
            "Na": 22.989769e-3,
            "Cl": 35.453e-3,
            "K": 39.0983e-3,
            "Mg": 24.305e-3,
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
    }
    total_charge = 0
    in_charge = {}
    balanced_dict = {}
    for ion, mass in input_dict.items():
        # if ion != balance_ion:
        charge = ion_props["charge"][ion]
        mols = mass / 1000 / ion_props["mw_data"][ion]
        total_charge += charge * mols
        # rint(ion, mols, charge * mols)
        in_charge[ion] = charge * mols
    mol_cl = total_charge / (ion_props["charge"][balance_ion])
    # Ellipsisif total_charge > 0 and ion_props["charge"][balance_ion] < 0:
    balanced_mass = -mol_cl * 1000 * ion_props["mw_data"][balance_ion]
    print(balanced_mass)
    input_dict[balance_ion] = input_dict[balance_ion] + balanced_mass
    # total_charge_out = 0
    # ts = {}
    # for ion, mass in input_dict.items():
    #     charge = ion_props["charge"][ion]
    #     mols = mass / 1000 / ion_props["mw_data"][ion]
    #     total_charge_out += charge * mols
    #     ts[ion] = charge * mols
    # if abs(total_charge_out) > 0.1:
    #     print(total_charge, total_charge_out, ts, in_charge)
    # else:
    #     print("charge okay", total_charge, balanced_mass)
    return input_dict


if __name__ == "__main__":
    phreeqc_pitzer = phreeqcWTapi(database="pitzer.dat")

    # basic brackish water
    input_composotion = {
        "Na": 0.4,
        "K": 0.009,
        "Cl": 0.2,
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
            "Ca": 40.078e-3,
            "HCO3": 61.0168e-3,
            "SO4": 96.06e-3,
            "Na": 22.989769e-3,
            "Cl": 35.453e-3,
            "K": 39.0983e-3,
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
    ib = ion_balance(input_composotion.copy())
    print(out, ib)
    for ion, loading in out.items():
        # input_composotion[ion] = loading
        print(ion, "org", input_composotion[ion], "wt", loading, "m", ib[ion])
    for ion, loading in out.items():
        input_composotion[ion] = loading
    # print(ion, "wt", loading, "m", ib[ion])
    phreeqc_pitzer.build_water_composition(
        input_composotion=input_composotion,
        charge_balance="Cl",
        pH=7,
        pe=0,
        units="g/kgw",
        pressure=1,
        temperature=20,
        assume_alkalinity=False,
    )

    print("-----------------------get intial solution state-----------------------")
    phreeqc_pitzer.get_solution_state(report=True)
