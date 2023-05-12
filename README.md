# This repository is part of the GPR2BIM project.

To use first install dependencies with pip:

`pip install -r requirements.txt`

Example usage:
To create an LOD 1 model from one of the provided example UtilityADE files you can use:

`python utilitynetwork_to_ifc.py ./CityGML_Beispiele/outputTestGML.gml -o ./IFC_Beispiele/ --lod 1 --radius 0.12`

- LOD 0: pipes are represented by lines
- LOD 1: pipes are represented by cylinders with radius equal to `radius`

for full list of functions:

`python utilitynetwork_to_ifc.py --help`