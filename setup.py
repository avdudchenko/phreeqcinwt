from setuptools import setup, find_packages

VERSION = "0.0.1"
DESCRIPTION = "Module for simulating water treatment systems with phreeqpy/phreeqc"
LONG_DESCRIPTION = "Module for simulating water treatment systems with phreeqpy/phreeqc"

# Setting up
setup(
    # the name must match the folder name 'verysimplemodule'
    name="phreeqcinwt",
    version=VERSION,
    author="Alexander V Dudchenko",
    author_email="<avd@slac.stanford.edu>",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=[
        "numpy <= 1.26.4",
        "pyyaml",
        "molmass",
    ],  # add any additional packages that
    # needs to be installed along with your package. Eg: 'caer'
    keywords=["python", "phreeqc", "phreeqpy"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ],
)
