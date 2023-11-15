import ifcopenshell as ifc
from src.ifc_template import Template
from src.utils import *
import numpy as np
import os

def get_random_orthogonal_vec(ref: np.ndarray) -> np.ndarray:
    """ find a random orthogonal vector to the reference vector"""
    norm = np.linalg.norm
    ref /= norm(ref)
    while True:
        r = np.random.uniform(size=ref.shape)
        theta = np.arccos(np.dot(ref, r)/(norm(ref)*norm(r)))
        if theta < 0.01: # check theta for numerical stability
            print(f'theta={theta} --> too low, retrying')
            continue
        u = r - (np.dot(r,ref)/(norm(ref)**2)*ref)
        u /= norm(u)
        break
    return u
        
def create_pipe_type(ifc_file: ifc.file) -> ifc.entity_instance:
    """_summary_

    Args:
        ifc_file (ifc.file): input IFC model, modified in-place

    Returns:
        ifc.entity_instance: ifc type
    """
    assert isinstance(ifc_file,ifc.file),'Please provide a valid IFC file to write to'
    owner_history = ifc_file.by_type('IfcOwnerHistory')[0]

    default_pset = ifc_file.create_entity('IfcPropertySet',
        GlobalId = create_guid(),
        OwnerHistory = owner_history,
        Name = 'Pset_DistributionFlowElementCommon',
        HasProperties = [
            ifc_file.create_entity('IfcPropertySingleValue', 
                Name = 'Reference', 
                NominalValue = ifc_file.create_entity('IfcIdentifier', 'Standard'))
        ]
        )
    pipe_type = ifc_file.create_entity('IfcPipeSegmentType',
        GlobalId = create_guid(),
        OwnerHistory = owner_history,
        Name = 'Pipe Types:Standard',
        HasPropertySets = [default_pset],
        PredefinedType = 'NOTDEFINED'
        )

    return pipe_type

def create_pipe(ifc_file, r = .15,
                start_pos = (1.3,1.4,1.5),
                extrusion_vector = (1.,1.,1.),
                name = '<Generated pipe>',
                description = '<Generated pipe description>',
                storey = None,
                lod = 1,
                type = None
                ):
    assert isinstance(ifc_file,ifc.file),'Please provide a valid IFC file to write to'
    assert storey, 'Please provide a storey'

    point_2d_circle = ifc_file.create_entity('IfcCartesianPoint', 
        Coordinates = (
            0.,
            0.
        ))
    direction_2d_circle = ifc_file.create_entity('IfcDirection',
        DirectionRatios=(
            1.,
            0.
        ))
    circle_position = ifc_file.create_entity('IfcAxis2Placement2D',
        Location = point_2d_circle,
        RefDirection = direction_2d_circle
        )
    circle_profile = ifc_file.create_entity('IfcCircleProfileDef',
        ProfileType = "AREA",
        Position = circle_position,
        Radius = r        
        )
    pipe_pos_location = ifc_file.create_entity('IfcCartesianPoint',
        Coordinates = start_pos)
    # get extrusion direction by normalizing the extrusion vector        
    direction = np.array(extrusion_vector)
    direction /= np.linalg.norm(direction)
    ref_direction = get_random_orthogonal_vec(direction)

    pipe_pos_axis = ifc_file.create_entity('IfcDirection',
        DirectionRatios = direction.tolist())
    pipe_pos_refdir = ifc_file.create_entity('IfcDirection',
        DirectionRatios = ref_direction.tolist())
    
    pipe_position = ifc_file.create_entity('IfcAxis2Placement3D',
        Location = pipe_pos_location,
        Axis = pipe_pos_axis,
        RefDirection = pipe_pos_refdir
    )    

    temp_placement = ifc_file.create_entity('IfcAxis2Placement3D',
        Location =      ifc_file.create_entity('IfcCartesianPoint', [0.,0.,0.]),
        Axis =          ifc_file.create_entity('IfcDirection', [0.,0.,1.]),
        RefDirection =  ifc_file.create_entity('IfcDirection', [1.,0.,0.]),
    ) 
    model_main_representation_context = ifc_file.by_type('IfcGeometricRepresentationContext')[0]
    
    if lod == 1: 
        # some software require a reference direction, which is orthogonal to the axis
   

        geometry = ifc_file.create_entity('IfcExtrudedAreaSolid',
            SweptArea = circle_profile,
            # Position = pipe_position, # try new placement
            Position = temp_placement,
            # always extrude perpendicular to profile
            ExtrudedDirection = ifc_file.createIfcDirection((0.,0.,1.)),
            # calculate depth from length of extrusion_vector
            Depth = np.linalg.norm(extrusion_vector)
            )
        pipe_3d_representation = ifc_file.create_entity('IfcShapeRepresentation',
        ContextOfItems = model_main_representation_context,
        RepresentationIdentifier = 'Body',
        RepresentationType = 'SweptSolid',
        Items = [geometry]
        )
        
    elif lod == 0:
        dir_ratios = ifc_file.create_entity('IfcDirection', 
            DirectionRatios = (0.,0.,1.))
        dir = ifc_file.create_entity('IfcVector',
            Orientation = dir_ratios,
            Magnitude = np.linalg.norm(extrusion_vector))
        geometry = ifc_file.create_entity('IfcLine',
            Pnt = ifc_file.create_entity('IfcCartesianPoint', [0.,0.,0.]),
            Dir = dir)
        
        pipe_3d_representation = ifc_file.create_entity('IfcShapeRepresentation',
        ContextOfItems = model_main_representation_context,
        RepresentationIdentifier = 'Body',
        RepresentationType = 'Curve2D',
        Items = [geometry]
        )

    pipe_product_definition_shape = ifc_file.create_entity('IfcProductDefinitionShape',
        # TODO: further representations can be added (e.g. point cloud, axis, etc.)
        Representations = [pipe_3d_representation]
        )
    
    storey_object_placement = storey.ObjectPlacement

    pipe_object_placement = ifc_file.create_entity('IfcLocalPlacement',
        PlacementRelTo = storey_object_placement,
        # RelativePlacement = ifc_file.createIfcAxis2Placement3D(Location=ifc_file.createIfcCartesianPoint([0.,0.,0.]))
        RelativePlacement = pipe_position
        )
   

    pipe = ifc_file.create_entity('IfcFlowSegment',
        GlobalId = create_guid(),
        # get main owner history in model
        OwnerHistory = ifc_file.by_type('IfcOwnerHistory')[0], # TODO pass this as argument
        Name = name,
        Description = description,
        ObjectPlacement = pipe_object_placement,
        Representation = pipe_product_definition_shape
        )
    ifc_file.create_entity('IfcRelContainedInSpatialStructure',
        GlobalId = create_guid(),
        OwnerHistory = ifc_file.by_type('IfcOwnerHistory')[0],
        RelatedElements = [pipe],
        RelatingStructure = storey
        )
    if type is not None:
        ifc_file.create_entity('IfcRelDefinesByType',
            GlobalId = create_guid(),
            OwnerHistory = owner_history,
            RelatedObjects = [pipe],
            RelatingType = type
            )
    return pipe


    
    
def create_connected_pipes(ifc_file,
                           points,
                           direction = 'forward',
                           r = .15,
                           name = '<Generated pipe>',
                           description = '<Generated pipe description>',
                           storey = None,
                           lod = 1,
                           type = None,
                           owner_history = None):
    assert isinstance(ifc_file, ifc.file)
    assert direction in ['forward', 'none', None]
    if owner_history is None: owner_history = ifc_file.by_type('IfcOwnerHistory')[0]
    
    # points = np.unique(points, axis=1)
    
    # r
    assert isinstance(r, float) or isinstance(r, list)
    if isinstance(r, list): assert len(r) == (len(points)-1)
    else: r = np.repeat(r,len(points)-1)
    # name
    assert isinstance(name, str) or isinstance(name, list)
    if isinstance(name,list): assert len(r) == (len(points)-1)
    else: name = np.repeat(name, len(points)-1)
    # description
    assert isinstance(description, str) or isinstance(description, list)
    if isinstance(description,list): assert len(r) == (len(points)-1)
    else: description = np.repeat(description, len(points)-1)

    pipes = []
    first_port = None
    last_port = None

    for i in range(len(points)-1):
        a = points[i]
        b = points[i+1] 
        if sum(a-b) == 0: continue
        pipe = create_pipe(ifc_file, r[i], points[i].tolist(), (points[i+1]-points[i]).tolist(),name[i],description[i],storey=storey,lod=lod,type=type)
        
        def rel_placement_to_port(rel_placement, flow_direction):
            placement_a = ifc_file.create_entity('IfcLocalPlacement',
                PlacementRelTo = pipe.ObjectPlacement,
                RelativePlacement = rel_placement
                )
            port_a = ifc_file.create_entity('IfcDistributionPort',
                GlobalId = create_guid(),
                OwnerHistory = owner_history,
                Name = 'Port',
                Description = 'Flow',
                ObjectPlacement = placement_a,
                FlowDirection = flow_direction

                )
            ifc_file.create_entity('IfcRelConnectsPortToElement', # TODO: IfcRelConnectsPortToElement is deprecated
                GlobalId = create_guid(),
                OwnerHistory = owner_history,
                Name = f'port_of_{pipe.GlobalId}',
                Description = 'Flow',
                RelatingPort = port_a,
                RelatedElement = pipe
                )
            return port_a

        rel_placement_a = ifc_file.create_entity('IfcAxis2Placement3D',
            Location =          ifc_file.create_entity('IfcCartesianPoint',[0.,0.,0.]),
            Axis =              ifc_file.create_entity('IfcDirection',[0.,0.,1.]), # invert b
            RefDirection =      ifc_file.create_entity('IfcDirection',[1.,0.,0.])
            )
        port_a = rel_placement_to_port(rel_placement_a, flow_direction='SOURCE')

        pipe_length = float(np.linalg.norm(points[i]-points[i+1]))
        rel_placement_b = ifc_file.create_entity('IfcAxis2Placement3D',
            Location =          ifc_file.create_entity('IfcCartesianPoint',[0.,0.,pipe_length]),
            Axis =              ifc_file.create_entity('IfcDirection',[0.,0.,1.]), # invert b
            RefDirection =      ifc_file.create_entity('IfcDirection',[1.,0.,0.])
            )

        port_b = rel_placement_to_port(rel_placement_b, flow_direction='SINK')

        # if this is the first pipe -> save port 'a' as the input port of the system
        if first_port is None: first_port = port_a
        
        # if last port is not none: create relation between them
        if last_port is not None:
            ifc_file.create_entity('IfcRelConnectsPorts',
                GlobalId = create_guid(),
                OwnerHistory = owner_history,
                Name = 'port_connection',
                RelatingPort = last_port,
                RelatedPort = port_a
                )
        
        last_port = port_b
        pipes.append(pipe)
    return pipes, first_port, last_port


def create_system_from_pipes(
        ifc_file:ifc.file, 
        pipes, 
        system_guid= None, 
        system_description = None, 
        owner_history = None, 
        name = '<System>', 
        port_a=None,
        port_b=None):
    """Generate an IfcSystem entity from a list of connected pipes. 
    Optionally the input and output ports of the system can be provided to the `port_a` and `port_b` parameters"""
    assert isinstance(ifc_file, ifc.file)
    if owner_history is None: owner_history = ifc_file.by_type('IfcOwnerHistory')[0]
    if system_guid is not None:
        assert isinstance(system_guid, str, 'GUID must be passed as string') # type: ignore
        if len(system_guid == 22):
            pass
        if len(system_guid == 32):
            system_guid = ifc.guid.compress(system_guid)
        else:
            raise ValueError('GUID must be either 22-base64 or 32-base16 int. Make sure to remove any unnessesary charecters')
    else:
        system_guid = create_guid()

    if port_a is not None: pipes.append(port_a)    
    if port_b is not None: pipes.append(port_b)

    system = ifc_file.create_entity('IfcSystem',
        GlobalId = system_guid,
        OwnerHistory = owner_history,
        Name = name        
        )
    ifc_file.create_entity('IfcRelAssignsToGroup',
        GlobalId = create_guid(),
        OwnerHistory = owner_history,
        RelatedObjects = pipes,
        RelatingGroup = system
        )    

    return system
    


if __name__ == '__main__':
    """test the IFC generation"""

    ROOT = os.path.split(os.path.abspath(__file__))[0]
    input = os.path.join(ROOT, 'data')
    my_template = Template()
    model = my_template.new_file()

    #Collecting general data from the IFC-File
    owner_history = model.by_type("IfcOwnerHistory")[0]
    project = model.by_type("IfcProject")[0]
    context = model.by_type("IfcGeometricRepresentationContext")[0]

    # pick a storey
    storey = model.by_type('IfcBuildingStorey')[0]
    # number of points = num segments + 1
    N = 37
    
    x = np.linspace(0, np.pi*2, N)    
    pts = np.array([np.cos(x),np.sin(x),np.cos(x)*np.sin(x)]).T
    
    print(pts.shape) # N x 3


    pipe_default_type = create_pipe_type(model)
    names = [f'pipe_{n}' for n in range(N-1)]
    create_connected_pipes(model, 
                           pts, 
                           r = 0.05, 
                           storey=storey, 
                           type = pipe_default_type, 
                           lod = 1,
                           name=names)

    model.write('test_export_22_site.ifc')