import ifcopenshell as ifc
import numpy as np
import uuid

create_guid = lambda: ifc.guid.compress(uuid.uuid1().hex)




def create_ifcaxis2placement(ifc_file, point, dir1, dir2):
    '''Creates an IfcAxis2Placement3D from Location, Axis and RefDirection specified as Python tuples'''
    point = ifc_file.createIfcCartesianPoint(point)
    dir1 = ifc_file.createIfcDirection(dir1)
    dir2 = ifc_file.createIfcDirection(dir2)
    axis2placement = ifc_file.createIfcAxis2Placement3D(point, dir1, dir2)
    return axis2placement



def create_ifclocalplacement(ifc_file, point, dir1, dir2, relative_to=None):
    '''Creates an IfcLocalPlacement from Location, Axis and RefDirection, specified as Python tuples, and relative placement'''
    axis2placement = create_ifcaxis2placement(ifc_file, point, dir1, dir2)
    ifclocalplacement2 = ifc_file.createIfcLocalPlacement(relative_to, axis2placement)
    return ifclocalplacement2



def create_ifcpolyline(ifc_file, point_list):
    '''Creates an IfcPolyLine from a list of points, specified as Python tuples'''
    ifcpts = []
    for point in point_list:
        point = ifc_file.createIfcCartesianPoint(point)
        ifcpts.append(point)
    polyline = ifc_file.createIfcPolyLine(ifcpts)
    return polyline



def create_ifcextrudedareasolid(ifc_file, point_list, ifcaxis2placement, extrude_dir, extrusion):
    '''Creates an IfcExtrudedAreaSolid from a list of points, specified as Python tuples'''
    polyline = create_ifcpolyline(ifc_file, point_list)
    ifcclosedprofile = ifc_file.createIfcArbitraryClosedProfileDef("AREA", None, polyline)
    ifcdir = ifc_file.createIfcDirection(extrude_dir)
    ifcextrudedareasolid = ifc_file.createIfcExtrudedAreaSolid(ifcclosedprofile, ifcaxis2placement, ifcdir, extrusion)
    return ifcextrudedareasolid


def parse_flat_pointlist(flat_list:str)->np.ndarray:
    """Generates a list of points in the shape [N,3] from a flat list of numbers, separated by ' '.

    Args:
        flat_list (str): flat list of numbers, separated by a space (' ')

    Returns:
        np.ndarray: List of numbers as a numpy array with shape [N,3]
    """
    return np.array(flat_list.split(' ')).reshape(-1, 3).astype(np.float64)

def decdeg2dms(dd):
    """Translated a decimal angle to the format (degrees, minutes, seconds)"""
    mult = -1 if dd < 0 else 1
    mnt,sec = divmod(abs(dd)*3600, 60)
    deg,mnt = divmod(mnt, 60)
    return mult*deg, mult*mnt, mult*sec