import xml.etree.ElementTree as ET
import ifcopenshell as ifc
import os
from argparse import ArgumentParser
import src.create_pipe as cp
from src.ifc_template import Template
from src.utils import *
from pyproj import Proj
import argparse

def argument_parser():
    parser = argparse.ArgumentParser(description='Argument Parser')
    parser.add_argument('input', help='Input ifc file')
    parser.add_argument('-o', '--output', nargs='?', default=None, help='Name of output file (optional)')
    parser.add_argument('-u', '--utility', default="0.9.3", help="version of UtilityNetworkADE")
    parser.add_argument('-c', '--citygml', default="2.0", help="version of CityGML")
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose mode')
    parser.add_argument('-l', '--lod', default=0, help='Level of detail. 0=Lines (Default), 1=Cylinders', type=int)
    parser.add_argument('-r', '--radius', default=0.15, help='Radius of generated pipes. (Default = 15cm)', type=float)

    args = parser.parse_args()

    return args




# Setup paths
args = argument_parser()
if not args.output:
    args.output = os.path.split(args.input)[1].replace('.gml','.ifc')

ifc_dir, ifc_fn = os.path.split(args.output)
if ifc_dir:
    os.makedirs(ifc_dir, exist_ok=True)
if not ifc_fn:
    ifc_fn = os.path.split(args.input)[1].replace('.gml','.ifc')
        
        
ROOT = os.path.split(os.path.abspath(__file__))[0]
gml_fp = os.path.join(ROOT, args.input)
ifc_fp = os.path.join(ROOT, args.output)

# Startup info
if args.verbose:
    print(f"Reading {args.input}")
    print(f"Generating {args.output}")



root = ET.parse(gml_fp).getroot()

utility_version = args.utility
core_version = args.citygml

# setup citygml namespaces
ns = {
    'utility' : f"http://www.citygml.org/ade/utility/{utility_version}",
    'core': f'http://www.opengis.net/citygml/{core_version}',
    'gml': f'http://www.opengis.net/gml'
}

# parse the given CityGML file
cityObjectMember = root.find('core:cityObjectMember', ns)
networks = cityObjectMember.findall('utility:Network', ns)
topoGraphs = []
networkComponents = []
for network in networks:
    topoGraphs.append(network.find('utility:topoGraph',ns))
    networkComponents.append(network.findall("utility:component", ns))

networkGraphs = []
for topoGraph in topoGraphs:
    networkGraphs.append(topoGraph.findall('utility:NetworkGraph',ns))

networkGraphs # TopoGraphs x NetworkGraphs
featureGraphs = []
for tg in networkGraphs:
    for ng in tg:        
        for featureGraphMember in ng.findall('utility:featureGraphMember', ns):
            featureGraphs.append(featureGraphMember.find('utility:FeatureGraph', ns))
            
nodes = featureGraphs[0].findall('utility:nodeMember', ns)
nodes = [nm.find('utility:Node', ns) for nm in nodes]

# print nodes info
if args.verbose:
    print(f"Found {len(nodes)} nodes:")
    for node in nodes:
        for child in node:
            print(child)

# find the spetial reference system used in CityGML e.g. 'epsg:25832'
srs = root.find('gml:boundedBy', ns).find('gml:Envelope', ns).attrib['srsName']

# xtract point lists from feature grpaphs
feat_graphs_points = []
for featureGraph in featureGraphs:
    nodes = [nodeMember.find('utility:Node', ns) for nodeMember in featureGraph.findall('utility:nodeMember', ns)]
    link = featureGraph.find('utility:linkMember',ns)\
        .find('utility:InteriorFeatureLink',ns)\
        .find('utility:realization', ns)\
        .find('gml:LineString', ns)\
        .find('gml:posList',ns)\
        .text
    feat_graphs_points.append(parse_flat_pointlist(link))
    
# print info feature graphs
if args.verbose:
    print(f"Found {len(feat_graphs_points)} feature graphs with poitns: {[p.shape for p in feat_graphs_points]}")
    

# find reference point as the point with the smallest coordintes in the model
all_pts = np.zeros([0,3], dtype = np.float64)
for feat_graph_pts in feat_graphs_points:
    all_pts = np.concatenate([all_pts, feat_graph_pts], axis = 0)
ref_point = all_pts.min(axis=0)

# translate points to have `ref_point` as origin
for feat_graph_points in feat_graphs_points:
    feat_graph_points -= ref_point
    
# project coordinates to WGS84

srs_type = srs.split(':')[0]
if srs_type == 'epsg':
    epsg_code = srs.split(':')[1]
    in_proj = Proj(f'EPSG:{epsg_code}')
else:
    raise NotImplementedError(f"Unknown SRS type {srs_type}")


lon, lat = in_proj(ref_point[0], ref_point[1], inverse=True)

if args.verbose:
    print(f"IFC with origin\n\tLongitude: {decdeg2dms(lon)}\t Latitude: {decdeg2dms(lat)}")
    


# Create a site from the reference point
site_params = Template.create_site_params(RefLatitude=decdeg2dms(lat),RefLongitude=decdeg2dms(lon))

# Create a new IFC file from a template
my_template = Template(project_name=ifc_fn.replace('.ifc',''), site = site_params)
model = my_template.new_file()
storey = model.by_type('IfcBuildingStorey')[0]

# Create connected pipes from each feature graph and add them to an IfcSystem entity
for feat_graph_pts in feat_graphs_points:
    pipes, first_port, last_port = cp.create_connected_pipes(model, feat_graph_pts, r =args.radius, storey=storey,lod=int(args.lod))
    cp.create_system_from_pipes(model, pipes,port_a = first_port, port_b = last_port)
    

output_fn = os.path.join(ROOT,ifc_dir, f'{ifc_fn}')
model.write(output_fn)

print(f"Successfully created the file:\n{output_fn}")