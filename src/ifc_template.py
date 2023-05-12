import ifcopenshell as ifc
from src.utils import *
from datetime import datetime
import tempfile
import collections
import os


class Template:

    @staticmethod
    def create_site_params(
            Name= '<Site name>',
            Description='<Site Description>',
            ObjectType='<Site type>',
            LongName='<Site long name>',
            RefLatitude=(42,21,31,181945),
            RefLongitude=(-71,-3,-24,-263305),
            RefElevation= 0.,
    ):
        return locals()
    
    def __init__(self,
        # default values
        project_name = '<Untitled IFC Project>',
        creator = ('ID', 'Max', 'Mustermann', ),
        organization = {
            'ID':'<Corporation ID>',
            'Name': '<Corporation>', 
            'Description': '<Corporation description>',
            'Roles': '<Corporation role>',
            'Addresses':'<Corporation address>'},
        file_schema = 'IFC2X3',
        site = None
        ):
        # initialize
        self.project_name = project_name
        self.timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        self.creator = creator
        self.organization = organization
        supported_schemas = ['IFC2X3','IFC4']
        assert file_schema in supported_schemas, f"Schema '{file_schema}' not supported. Please use {supported_schemas}"
        self.file_schema = file_schema
        if site is not None:
            self.site = site
        else:
            self.site = self.create_site_params()

        self.template_string = f"""
ISO-10303-21;
HEADER;
FILE_DESCRIPTION (('ViewDefinition [CoordinationView, 
  QuantityTakeOffAddOnView]'), '2;1');
FILE_NAME ('{self.project_name}.ifc', '{self.timestamp}', 
  ('Vermesser'), ('Vermessungsbüro'), 
  'v0.6.0', 
  'ifcopenshell', 'The authorising person');
FILE_SCHEMA (('{self.file_schema}'));
ENDSEC;
DATA;

/* define the project and the creator meta data */
#1 = IFCPROJECT('0YvctVUKr0kugbFTf53O9L', #2, '{self.project_name}', 
     $ , $, $, $, (#20), #7);
#2 = IFCOWNERHISTORY(#3, #6, $, .ADDED., $, $, $, 1217620436);
#3 = IFCPERSONANDORGANIZATION(#4, #5, $);
#4 = IFCPERSON('ID001', 'Beetz', 'Jakob', $, $, $, $, $);
#5 = IFCORGANIZATION($, 'RWTH', 'Faktultaet Architektur, Reiff Museum', $, $);
#6 = IFCAPPLICATION(#5, 'version 0.10', 'My text editor', 'TA 1001');

/*determine the units used in the project (e.g. length unit in metre) */
#7 = IFCUNITASSIGNMENT((#8, #9, #10, #11, #15, #16, #17, #18, #19));
#8 = IFCSIUNIT(*, .LENGTHUNIT., $, .METRE.);
#9 = IFCSIUNIT(*, .AREAUNIT., $, .SQUARE_METRE.);
#10 = IFCSIUNIT(*, .VOLUMEUNIT., $, .CUBIC_METRE.);
#11 = IFCCONVERSIONBASEDUNIT(#12, .PLANEANGLEUNIT., 'DEGREE', #13);
#12 = IFCDIMENSIONALEXPONENTS(0, 0, 0, 0, 0, 0, 0);
#13 = IFCMEASUREWITHUNIT(IFCPLANEANGLEMEASURE(1.745E-2), #14);
#14 = IFCSIUNIT(*, .PLANEANGLEUNIT., $, .RADIAN.);
#15 = IFCSIUNIT(*, .SOLIDANGLEUNIT., $, .STERADIAN.);
#16 = IFCSIUNIT(*, .MASSUNIT., $, .GRAM.);
#17 = IFCSIUNIT(*, .TIMEUNIT., $, .SECOND.);
#18 = IFCSIUNIT(*, .THERMODYNAMICTEMPERATUREUNIT., $, .DEGREE_CELSIUS.);
#19 = IFCSIUNIT(*, .LUMINOUSINTENSITYUNIT., $, .LUMEN.);
#20 = IFCGEOMETRICREPRESENTATIONCONTEXT($, 'Model', 3, 1.000E-5, #21, $);
#21 = IFCAXIS2PLACEMENT3D(#22, $, $);
#22 = IFCCARTESIANPOINT((0., 0., 0.));

/* the site of the model */


#23 = IFCSITE('{create_guid()}', #2, '{self.site['Name']}', 
'{self.site['Description']}', $, #24, $, $, .ELEMENT., {self.site['RefLatitude']},{self.site['RefLongitude']},{self.site['RefElevation']}, $, $);

/* The origin of the model */
#24 = IFCLOCALPLACEMENT($, #25);
#25 = IFCAXIS2PLACEMENT3D(#26, #27, #28);
#26 = IFCCARTESIANPOINT((0., 0., 0.));
#27 = IFCDIRECTION((0., 0., 1.));
#28 = IFCDIRECTION((1., 0., 0.));


/*  Description of the main building */
#29 = IFCBUILDING('{create_guid()}', #2, '{self.site['Description']}', 
    '{self.site['Description']}', $, #30, $, $, .ELEMENT., $, $, $);
#30 = IFCLOCALPLACEMENT(#24, #31);
#31 = IFCAXIS2PLACEMENT3D(#32, #33, #34);
#32 = IFCCARTESIANPOINT((0., 0., 0.));
#33 = IFCDIRECTION((0., 0., 1.));
#34 = IFCDIRECTION((1., 0., 0.));


/* a storey within the building */
#35 = IFCBUILDINGSTOREY('{create_guid()}', #2, 'Default Building Storey', 
    'Description of Default Building Storey', $, #36, $, $, .ELEMENT., 0.);
#36 = IFCLOCALPLACEMENT(#30, #37);
#37 = IFCAXIS2PLACEMENT3D(#38, #39, #40);
#38 = IFCCARTESIANPOINT((0., 0., 0.));
#39 = IFCDIRECTION((0., 0., 1.));
#40 = IFCDIRECTION((1., 0., 0.));


/* relate the site - building - story by objectified relildingContainer' */
#42 = IFCRELAGGREGATES('{create_guid()}', #2, 'SiteContainer', 
      'SiteContainer For Buildings', #23, (#29));
#43 = IFCRELAGGREGATES('{create_guid()}', #2, 'ProjectContainer', 
      'ProjectContainer for Sites', #1, (#23));
#44 = IFCRELAGGREGATES('{create_guid()}', #2, 'BuildingContainer', 
      'BuildingContainer for Storeys', #29, (#35));      
/*#45 = IFCRELCONTAINEDINSPATIALSTRUCTURE('{create_guid()}', #2, 
      'Default Building', 'Contents of Building Storey', (#45, #97, #127, #124), #35);*/
ENDSEC;
END-ISO-10303-21;

            """
    def new_file(self):
        temp_handle, temp_filename = tempfile.mkstemp(suffix='.ifc')
        with open(temp_filename,'wt') as f:
            f.write(self.template_string)
        ifc_file = ifc.open(temp_filename)        
        return ifc_file


        


if __name__ == '__main__':
    my_template = Template()
    model = my_template.new_file()
    model.write('test_export6.ifc')