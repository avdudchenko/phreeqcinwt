# phreeqcinwt
This is a module for useing phreeqc to model chemistry with focus on water treatment applications 
The module uses phreeqpy to communicate with phreeqc and requies you to install phreeqpy first as well as phreeqc https://www.phreeqpy.com/

Installation 
    install phreeqc COM module (32 and 64 bit) - follow instructions from:

    https://water.usgs.gov/water-resources/software/PHREEQC/index.html

    install conda

    in cmd execute:

        conda env create -f phreeqcinwt.yml
        
    this will create hms_model_tools environment and setup all our dependencies. 

to update:

    conda env update -n phreeqcinwt --f phreeqcinwt.yml

to install into a different conda env:

    conda env update -n YOUR_ENV --file phreeqcinwt.yml

Cd to module directory and run python setup.py develop
place databases you want to use into phreeqcinwt/databases folder

for example usages look in to phreeqcinwt/examples