import os
import json
import sys

paramdefs =  [
 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Aliquot ID',
  'desc_short': 'Aliquot ID',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'id_aliquot',
  'parents': ['aliquot', 'identifiers'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Stack Y Origin',
  'desc_short': 'Stack Y Origin',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_data_yorg',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': ['Up', 'Down'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'Screen Position',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'screen_position',
  'parents': ['microscope'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Cell size Z',
  'desc_short': 'Cell size Z',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_size_zlen',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Stack ND2',
  'desc_short': 'Stack ND2',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_data_nd2',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': ['1', '2', '4', '8', '16'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Binning',
  'desc_short': 'Hardware Binning Y',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'binning_hardware_y',
  'parents': ['binning'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Stack ND1',
  'desc_short': 'Stack ND1',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_data_nd1',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Spot alignment 2 deflectors',
  'desc_short': 'Spot alignment 2 deflectors',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'spot_alignment_2_deflectors',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'A',
  'desc_long': '',
  'desc_short': 'Temperature TEC Current',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ddd_temperature_tec_current',
  'parents': ['ddd_camera'],
  'property': 'current',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Year grant started being referenced in P41 APR',
  'desc_short': 'Start for p41',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'grant_p41_ref_start',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'datetime'},


 {'children': ['category_image',
                'assess_grid',
                'comment_analysis',
                'processed_structure',
                'description_buffer_dilution',
                'comment_grid',
                'comment_project_desc',
                'comment_specimen_stability',
                'description_grid_prefreezing',
                'folder_description',
                'description_notebook',
                'comments_text',
                'description_purification',
                'description_aliquot',
                'ice_type',
                'description_buffer_purification',
                'subject_notebook',
                'comment_aliquot',
                'description_grid_postfreezing',
                'description_medical_relevance',
                'comment_goals',
                'description_storage_location',
                'assess_ice_comments',
                'comment_presentation',
                'description_storage_conditions',
                'description_purpose',
                'description_reconstruction',
                'description_specimen_stability',
                'description_background',
                'description_progress',
                'comment_pretreatment_grid',
                'name_folder',
                'assess_ice_thick',
                'comment_project_progress',
                'assess_image_quality',
                'comment_reconstruction',
                'description_goals',
                'comment_postfreezing_grid',
                'description_genetic',
                'comment_purpose',
                'description_storage'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Textual descriptions',
  'desc_short': 'Textual descriptions',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'textual_descriptions',
  'parents': ['descriptive_information'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'End date for a P41 Report',
  'desc_short': 'Report End',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'p41_report_end_date',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'datetime'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Journal name',
  'desc_short': 'Journal name',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'name_journal',
  'parents': ['publication'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Project Investigators',
  'desc_short': 'Investigators',
  'immutable': None,
  'indexed': True,
  'iter': True,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'project_investigators',
  'parents': ['people'],
  'property': None,
  'uri': None,
  'vartype': 'user'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Gain',
  'desc_short': 'Gain',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'nikon_gain',
  'parents': ['scanner'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'fax',
  'desc_short': 'fax',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'fax',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Condenser stigmator deflectors',
  'desc_short': 'Condenser stigmator deflectors',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'condenser_stigmator_deflectors',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '???',
  'desc_short': '???',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'def_plax',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': ['Usa_Federal', 'Industry', 'Foundation'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Type of entity providing support',
  'desc_short': 'Grant Source Type',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'grant_source_type',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'choice'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'degree',
  'desc_long': 'Stage tilt X-axis',
  'desc_short': 'Stage tilt X-axis',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'specimen_tilt',
  'parents': ['microscope', 'angle'],
  'property': 'angle',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'CryoEM ParamDefs',
  'desc_short': 'CryoEM ParamDefs',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'domain_cryoem',
  'parents': ['root'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'Last Dark Frame Dataset',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ddd_last_dark_frame_dataset',
  'parents': ['ddd_camera'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'um',
  'desc_long': 'Intended defocus while imaging, underfocus positive',
  'desc_short': 'Set Defocus',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ctf_defocus_set',
  'parents': ['ctf', 'length'],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': ['0',
               '1',
               '2',
               '3',
               '4',
               '5',
               '6',
               '7',
               '8',
               '9',
               '10'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Image Quality. 0 is unusable, 10 is perfect.',
  'desc_short': 'Image quality',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'assess_image_quality',
  'parents': ['textual_descriptions'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': ['1024', '2048', '4096', '10240'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'pixel',
  'desc_long': 'Size of frame along the X-axis',
  'desc_short': 'Frame width',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'size_image_ccd_x',
  'parents': ['size'],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Humidifier enabled flag',
  'desc_short': 'Humidifier enabled',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'vitrobot_humid_on',
  'parents': ['blotting'],
  'property': None,
  'uri': None,
  'vartype': 'boolean'},


 {'children': ['vitrobot_humidity', 'humidity_ambient'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Humidity',
  'desc_short': 'Humidity',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'humidity',
  'parents': ['physical_property'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 's',
  'desc_long': 'Blanking time',
  'desc_short': 'Blanking time',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'digicamcond_blankingtime',
  'parents': [],
  'property': 'time',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': ['Data Collection', 'Screening', 'Unknown', 'Other'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Type of microscopy session',
  'desc_short': 'Session type',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'type_session',
  'parents': ['microscopy'],
  'property': None,
  'uri': None,
  'vartype': 'choice'},


 {'children': [],
  'choices': ['1', '2', '4', '8', '16'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'Hardware Binning X',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'binning_hardware_x',
  'parents': ['binning'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Fixed Increment',
  'desc_short': 'Fixed Increment',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_fixedincrement',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Spot',
  'desc_short': 'Spot',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'eos_spot',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Visualization Bitrate',
  'desc_short': 'Visualization Bitrate',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'visualization_bitrate',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': ['Frozen Hydrated',
               'Sugar Embedding',
               'Negative   Stain',
               'Cryonegative'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Freezing technique',
  'desc_short': 'Freezing technique',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'select_technique_freezing',
  'parents': ['freezing'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Gun shift deflectors',
  'desc_short': 'Gun shift deflectors',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'gun_shift_deflectors',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Zeiss brightness',
  'desc_short': 'Zeiss brightness',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'zeiss_brightness',
  'parents': ['scanner'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': ['tem_dose_rate'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Rate parameters',
  'desc_short': 'Rate parameters',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'rate',
  'parents': ['elapsed_time'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['lens_voltage_projector', 'lens_voltage_objective'],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Placeholder: lens voltage',
  'desc_short': 'Lens Voltage Parameters',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'voltage_lens',
  'parents': ['lens', 'current_lens', 'voltage'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': ['Electron  Diffraction',
               'X-Ray  Solution  Scattering',
               'PDB'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Sample source',
  'desc_short': 'Sample source',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'source_sample',
  'parents': ['biological_target', 'scanner'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Description of the event or discussion',
  'desc_short': 'Text',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'description_notebook',
  'parents': ['textual_descriptions'],
  'property': None,
  'uri': None,
  'vartype': 'text'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'um',
  'desc_long': 'Delta X',
  'desc_short': 'Delta X',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'delta_z',
  'parents': [],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Visualization Codec',
  'desc_short': 'Visualization Codec',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'visualization_codec',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Stack Lens Data',
  'desc_short': 'Stack Lens Data',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_data_lens',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'pixel',
  'desc_long': 'Right coordinate',
  'desc_short': 'Right coord',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'digicamprm_arearight',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Complete description of solubilization buffer used in purification',
  'desc_short': 'Storage buffer',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'description_buffer_purification',
  'parents': ['textual_descriptions'],
  'property': None,
  'uri': None,
  'vartype': 'text'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Profile Photo',
  'desc_short': 'Profile Photo',
  'immutable': None,
  'indexed': True,
  'iter': True,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'person_image',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'binary'},


 {'children': ['current_screen', 'current_lens'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Current',
  'desc_short': 'Current',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'current',
  'parents': ['physical_property'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Editor Comments',
  'desc_short': 'Editor Comments',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'comments_editor',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'text'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Interm lens 4 DAC',
  'desc_short': 'Interm lens 4 DAC',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'lens_il4dac',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'e/A2/sec',
  'desc_long': 'The dosage received by the camera per unit time',
  'desc_short': 'Dose rate',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'tem_dose_rate',
  'parents': ['microscope', 'rate'],
  'property': 'dose',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Start date for a P41 Report',
  'desc_short': 'Report Start',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'p41_report_start_date',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'datetime'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Stack ID Type',
  'desc_short': 'Stack ID Type',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_data_idtype',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Purpose of experiment',
  'desc_short': 'Purpose',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'description_purpose',
  'parents': ['textual_descriptions', 'biology_of_project'],
  'property': None,
  'uri': None,
  'vartype': 'text'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Title of a book',
  'desc_short': 'Book Title',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'name_book',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Reconstruction parameters',
  'desc_short': 'Reconstruction parameters',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'parameters_reconstruction',
  'parents': ['final_reconstruction'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['box_label',
                'box_count',
                'box_color',
                'box_coords',
                'box_size'],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Box file attachments. Typically ordered by date.',
  'desc_short': 'Box Files',
  'immutable': None,
  'indexed': True,
  'iter': True,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'box',
  'parents': ['processing'],
  'property': None,
  'uri': None,
  'vartype': 'binary'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Box Label',
  'desc_short': 'Box Label',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'box_label',
  'parents': ['box'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': ['Empty - no ice',
               'Too thin',
               'A little thin',
               'Perfect',
               'A little thick',
               'Too thick',
               'Bad ice'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'The thickness of the ice',
  'desc_short': 'Ice thick',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'assess_ice_thick',
  'parents': ['textual_descriptions', 'ice'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Dark level',
  'desc_short': 'Dark level',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'eos_darklevel',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': ['ctf_ampcont',
                'ctf_defocus_measured',
                'ctf_defocus_set',
                'ctf_drift_bfactor',
                'ctf_astig_angle',
                'ctf_astig_defocus_diff',
                'ctf_snr_max',
                'ctf_bfactor',
                'ctf_drift_angle'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'CTF details',
  'desc_short': 'CTF details',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ctf',
  'parents': ['microscope', 'imaging'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Number of grids lost ',
  'desc_short': 'Grids lost ',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'grids_tem_lost',
  'parents': ['grid'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'pf',
  'desc_long': 'Concentration per mL',
  'desc_short': 'Conc per mL',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'concentration_pml',
  'parents': ['concentration'],
  'property': 'concentration',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Stack STAMP',
  'desc_short': 'Stack STAMP',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_data_stamp',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'The person who did the training',
  'desc_short': 'Trainer',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'trainer',
  'parents': ['people'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 's',
  'desc_long': 'Length of time the pads are in contact with the grid during the blot.',
  'desc_short': 'Blot time',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'vitrobot_time_blot',
  'parents': ['elapsed_time', 'blotting'],
  'property': 'time',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Interm lens 1 DAC',
  'desc_short': 'Interm lens 1 DAC',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'lens_il1dac',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': ['ddd_sensor_offset',
                'ddd_data_output_mode',
                'ddd_raw_frame_type',
                'ddd_last_gain_frame_dataset',
                'ddd_gain_correction',
                'ddd_dark_correction',
                'ddd_raw_frame_suffix',
                'ddd_raw_frame_save_summed',
                'ddd_fpga_version',
                'faraday_plate_peak',
                'ddd_temperature_control',
                'ddd_exposure_mode',
                'ddd_gain_frame_status',
                'ddd_raw_frame_save',
                'ddd_sensor_coarse_gain',
                'ddd_sensor_output_mode',
                'ddd_temperature_tec_current',
                'time_preexposure',
                'ddd_temperature_control_mode',
                'ddd_last_dark_frame_dataset',
                'ddd_dark_frame_status'],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Direct Electron Detector parameters',
  'desc_short': 'Direct Electron Detector parameters',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ddd_camera',
  'parents': ['camera'],
  'property': None,
  'uri': None,
  'vartype': 'none'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'X beam-tilt setting',
  'desc_short': 'X beam tilt',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'def_beamtiltx',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'kV',
  'desc_long': 'Projector lens voltage',
  'desc_short': 'Projector lens volt',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'lens_voltage_projector',
  'parents': ['lens', 'voltage_lens'],
  'property': 'voltage',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'User-defined bookmarks',
  'desc_short': 'Bookmarks',
  'immutable': False,
  'indexed': True,
  'iter': True,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'bookmarks',
  'parents': ['core'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Cond lens 1 DAC',
  'desc_short': 'Cond lens 1 DAC',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'lens_cl1dac',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Placeholder: JADAS',
  'desc_short': 'Placeholder: JADAS',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'mds_defx',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Placeholder: JADAS',
  'desc_short': 'Placeholder: JADAS',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'mds_defy',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '???',
  'desc_short': '???',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'lens_cmdac',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': ['Rejected',
               'Indefinite Hold',
               'Wait for Sample',
               'Complete',
               'Screening',
               'Analysis',
               'Imaging',
               'Manuscript Prep.'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'The current state of this project',
  'desc_short': 'Project Status',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'project_status',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'choice'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'X image-shift setting',
  'desc_short': 'X image shift',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'def_imageshiftx',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Y image-shift setting',
  'desc_short': 'Y image shift',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'def_imageshifty',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': ['tem_magnification_measured', 'tem_magnification_set'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Magnification',
  'desc_short': 'Magnification',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'magnification',
  'parents': ['microscope', 'imaging'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['roi_offset_y',
                'roi_offset_x',
                'ccd_camera',
                'film_camera',
                'roi_offset_w',
                'roi_offset_h',
                'ddd_camera'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Camera details',
  'desc_short': 'Camera details',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'camera',
  'parents': ['equipment'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['sequence_rna', 'sequence_dna', 'sequence_protein'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Sequence',
  'desc_short': 'Sequence',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'sequence',
  'parents': ['biological_target', 'physical_property'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Intensity',
  'desc_short': 'Intensity',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_intensity',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'degree',
  'desc_long': 'Direction of drift',
  'desc_short': 'Drift angle',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ctf_drift_angle',
  'parents': ['ctf', 'angle'],
  'property': 'angle',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Publication type',
  'desc_short': 'Publication type',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'type_publication',
  'parents': ['publication'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['description_storage_location',
                'name_specimen',
                'sequence',
                'aliquot',
                'absorbance_at_wavelength',
                'description_storage_conditions',
                'wavelength_at_absorbance',
                'description_specimen_stability',
                'source_sample',
                'mass_specimen',
                'symmetry_particle',
                'description_storage'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Biological target',
  'desc_short': 'Biological target',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'biological_target',
  'parents': ['descriptive_information'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['lens_voltage_objective'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'kV',
  'desc_long': 'Accelerating voltage',
  'desc_short': 'Acc volt',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'tem_voltage',
  'parents': ['microscope', 'voltage'],
  'property': 'voltage',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Number of blots done on the grid',
  'desc_short': 'Number of blots',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'vitrobot_blots',
  'parents': ['blotting'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'phone',
  'desc_short': 'phone',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'phone',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'uL',
  'desc_long': 'Volume of the aliquot',
  'desc_short': 'Aliquot volume',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'volume_aliquot',
  'parents': ['aliquot', 'volume'],
  'property': 'volume',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Obj lens x stigmator',
  'desc_short': 'Obj lens x stigmator',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'def_olstigx',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Y gun-shift setting',
  'desc_short': 'Y gun shift',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'def_gunshifty',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Grid Size Y',
  'desc_short': 'Grid Size Y',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_size_my',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Grid size X',
  'desc_short': 'Grid size X',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_size_mx',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Grid Size Z',
  'desc_short': 'Grid Size Z',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_size_mz',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'degC',
  'desc_long': '',
  'desc_short': 'Detector Temperature',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ddd_temperature_detector',
  'parents': ['temperature'],
  'property': 'temperature',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': ['On', 'Off'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'Dark Correction',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ddd_dark_correction',
  'parents': ['ddd_camera'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 's',
  'desc_long': 'Pre-exposure delay',
  'desc_short': 'Pre-exposure delay',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'pre_exposure_delay',
  'parents': [],
  'property': 'time',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Amount of grant in USD',
  'desc_short': 'Grant Amount',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'grant_funds',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': ['voltage_lens'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'A',
  'desc_long': 'Lens current',
  'desc_short': 'Lens current',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'current_lens',
  'parents': ['current', 'lens'],
  'property': 'current',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Funding Agency Credits',
  'desc_short': 'Funding Agency Credits',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'visualization_credits_funding',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'Vacuum Level',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'vacuum_level',
  'parents': ['microscope'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': ['on-axis', 'off-axis'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Focus centering',
  'desc_short': 'Focus centering',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'focus_centering',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'choice'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Projector lens',
  'desc_short': 'Projector lens',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'projector_lens',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': ['Gain Normalized', 'Dark Subtracted', 'Unprocessed'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Frame type',
  'desc_short': 'Frame type',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'type_frame',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'choice'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Projector deflectors',
  'desc_short': 'Projector deflectors',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'projector_deflectors',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': ['5', '20', '30', '40', '50', '60'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'um',
  'desc_long': 'Objective aperture',
  'desc_short': 'Objective aperture',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'aperture_objective',
  'parents': ['length', 'microscope'],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'um',
  'desc_long': 'Defocus determined by fitting the power spectrum',
  'desc_short': 'Meas defocus',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ctf_defocus_measured',
  'parents': ['ctf', 'length'],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 's',
  'desc_long': '',
  'desc_short': 'Preexposure Time',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'time_preexposure',
  'parents': ['ddd_camera'],
  'property': 'time',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'uL',
  'desc_long': 'Volume of the aliquot in uL',
  'desc_short': 'Vol aliquot, uL',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'grid_volume_applied',
  'parents': ['volume'],
  'property': 'volume',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Box Coords',
  'desc_short': 'Box Coords',
  'immutable': None,
  'indexed': True,
  'iter': True,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'box_coords',
  'parents': ['box'],
  'property': None,
  'uri': None,
  'vartype': 'coordinate'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'X gun-shift setting',
  'desc_short': 'X gun shift',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'def_gunshiftx',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Intermediate stigmator deflectors',
  'desc_short': 'Intermediate stigmator deflectors',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'intermediate_stigmator_deflectors',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'um',
  'desc_long': 'Pixel size',
  'desc_short': 'Size of pixel',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ccd_pixelsize',
  'parents': ['length'],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Proj lens 3 DAC',
  'desc_short': 'Proj lens 3 DAC',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'lens_pl3dac',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '???',
  'desc_short': '???',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'def_play',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': ['Holey Carbon Film', 'Continuous Carbon'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Substrate used',
  'desc_short': 'Substrate',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'select_substrate_grid',
  'parents': ['grid'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Aliquot description',
  'desc_short': 'Aliquot description',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'description_aliquot',
  'parents': ['aliquot', 'textual_descriptions'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Visualization Name',
  'desc_short': 'Name',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'visualization_name',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'A^2',
  'desc_long': 'B-factor in the drift direction',
  'desc_short': 'B-factor in drift direction',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ctf_drift_bfactor',
  'parents': ['ctf'],
  'property': 'bfactor',
  'uri': None,
  'vartype': 'float'},


 {'children': ['website',
                'address_city',
                'name_group',
                'address_zipcode',
                'support',
                'address_international',
                'affiliations',
                'phone_voice',
                'phone_fax',
                'phone_voice_international',
                'address_email',
                'phone_fax_international',
                'address_street',
                'institution'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Placeholder: info. on research groups',
  'desc_short': 'Groups (remove)',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'group_descriptors',
  'parents': ['descriptive_information'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'degree',
  'desc_long': 'Y rotation or tilt',
  'desc_short': 'Y rot/tilt',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'goniopos_rotortilty',
  'parents': [],
  'property': 'angle',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'comment_goals',
  'desc_short': 'comment goals',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'comment_goals',
  'parents': ['textual_descriptions'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Screen to film ratio',
  'desc_short': 'Screen/film ratio',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'film_screen_ratio',
  'parents': ['ratio', 'film'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Stack CMAP',
  'desc_short': 'Stack CMAP',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_data_cmap',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': ['Quantifoil   R 1.2/1.3',
               'Quantifoil R 2/1',
               'Quantifoil R 2/2',
               'Quantifoil R 3.5/1',
               'Copper',
               'Molybdenum'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Grid type',
  'desc_short': 'Grid type',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'grid_tem_type',
  'parents': ['grid'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Y gun-tilt setting',
  'desc_short': 'Y gun tilt',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'def_guntilty',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'X gun-tilt setting',
  'desc_short': 'X gun tilt',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'def_guntiltx',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': ['hazard_bl_max'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Hazards',
  'desc_short': 'Hazards',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'hazard',
  'parents': ['descriptive_information'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Cell size Y',
  'desc_short': 'Cell size Y',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_size_ylen',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Down-sampling ratio of the film scanner',
  'desc_short': 'Average factor',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'scan_average',
  'parents': ['scanner'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Full citation for a publication in P41 APR format',
  'desc_short': 'Citation',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'publication_citation',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'text'},


 {'children': ['description_purification'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Purification parameters',
  'desc_short': 'Purification parameters',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'purification',
  'parents': ['experimental-techniques'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Workshop Agenda',
  'desc_short': 'Workshop Agenda',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'agenda',
  'parents': ['project_information'],
  'property': None,
  'uri': None,
  'vartype': 'text'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'um',
  'desc_long': 'CCD size X (width) in pixels',
  'desc_short': 'CCD size X',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ccd_size_pix_x',
  'parents': ['length', 'ccd_camera'],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'comment_purpose',
  'desc_short': 'comment purpose',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'comment_purpose',
  'parents': ['textual_descriptions'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'ID of this CCD recording process',
  'desc_short': 'CCD process ID',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ccd_process_identifier',
  'parents': ['identifiers', 'ccd_camera'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Saxton Increment',
  'desc_short': 'Saxton Increment',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_saxtonincrement',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 's',
  'desc_long': 'Exposure time',
  'desc_short': 'Exposure time',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'exposure_time',
  'parents': [],
  'property': 'time',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Gun tilt deflectors',
  'desc_short': 'Gun tilt deflectors',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'gun_tilt_deflectors',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': ['200', '300', '400'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Meshsize of the grid',
  'desc_short': 'Grid meshsize',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'grid_tem_mesh_size',
  'parents': ['length', 'grid', 'area'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'Gain Frame Status',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ddd_gain_frame_status',
  'parents': ['ddd_camera'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Freezing label',
  'desc_short': 'Freezing label',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'title_freezing',
  'parents': ['identifiers'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'A^2',
  'desc_long': 'ctf B-factor',
  'desc_short': 'B-factor',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ctf_bfactor',
  'parents': ['ctf'],
  'property': 'bfactor',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Year a book was published',
  'desc_short': 'Publication Year',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'year_published',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Title of the demonstration',
  'desc_short': 'Demo title',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'title_demonstration',
  'parents': ['microscope_demo'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Micrograph ID',
  'desc_short': 'Micrograph ID',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'id_micrograph',
  'parents': ['identifiers'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': ['EMAN', 'IMAGIC', 'SAVR', 'SPIDER'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Low dose method',
  'desc_short': 'Low dose method',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'comment_reconstruction',
  'parents': ['textual_descriptions', 'final_reconstruction'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Resolution',
  'desc_short': 'Resolution',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'visualization_resolution',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Mask files for a 3D map or volume',
  'desc_short': '3D Volume Masks',
  'immutable': False,
  'indexed': True,
  'iter': True,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'file_volume_masks',
  'parents': ['file_volume'],
  'property': None,
  'uri': None,
  'vartype': 'binary'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Placeholder: JADAS',
  'desc_short': 'Placeholder: JADAS',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'mds_blankingtype',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Date Completed',
  'desc_short': 'Date Completed',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'date_complete',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'datetime'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'ID of the grid batch',
  'desc_short': 'ID of grid batch',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'id_grid_batch',
  'parents': ['identifiers'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Condenser tilt deflectors',
  'desc_short': 'Condenser tilt deflectors',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'condenser_tilt_deflectors',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Recent Progress',
  'desc_short': 'Recent Progress',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'description_progress',
  'parents': ['textual_descriptions'],
  'property': None,
  'uri': None,
  'vartype': 'text'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Frozen by',
  'desc_short': 'Frozen by',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'frozen_by',
  'parents': ['people'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'nm',
  'desc_long': 'Y position',
  'desc_short': 'Y pos',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'goniopos_y',
  'parents': [],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'nm',
  'desc_long': 'X position',
  'desc_short': 'X pos',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'goniopos_x',
  'parents': [],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'nm',
  'desc_long': 'Z position',
  'desc_short': 'Z pos',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'goniopos_z',
  'parents': [],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'High-tension level',
  'desc_short': 'High-tension level',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'eos_htlevel',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Creator Comments',
  'desc_short': 'Creator Comments',
  'immutable': None,
  'indexed': True,
  'iter': True,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'comments_creator',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'comments'},


 {'children': [],
  'choices': ['1024', '2048', '4096', '10240'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'pixel',
  'desc_long': 'Size of frame along the Y-axis',
  'desc_short': 'Frame height',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'size_image_ccd_y',
  'parents': ['size'],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Proj lens 2 DAC',
  'desc_short': 'Proj lens 2 DAC',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'lens_pl2dac',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'um',
  'desc_long': 'Scan step',
  'desc_short': 'Scan step',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'scan_step',
  'parents': ['scanner'],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Coarse objective lens',
  'desc_short': 'Coarse objective lens',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'coarse_objective_lens',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Placeholder: JADAS',
  'desc_short': 'Placeholder: JADAS',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'photo_manualexptime',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '???',
  'desc_short': '???',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'eos_temasidmode',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Wavelength',
  'desc_short': 'Wavelength',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'wavelength',
  'parents': ['physical_property', 'length'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': ['10', '20', '50', '70', '120', '150', '200'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'um',
  'desc_long': 'Condenser aperture',
  'desc_short': 'Condenser aperture',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'aperture_condenser',
  'parents': ['length', 'microscope'],
  'property': 'length',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'General parameter for storage of textual comments',
  'desc_short': 'Comments',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'comments_text',
  'parents': ['textual_descriptions', 'microscope_demo'],
  'property': None,
  'uri': None,
  'vartype': 'text'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Cond lens y stigmator',
  'desc_short': 'Cond lens y stigmator',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'def_clstigy',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Cond lens x stigmator',
  'desc_short': 'Cond lens x stigmator',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'def_clstigx',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'mV',
  'desc_long': 'Omega-filter setting',
  'desc_short': 'Omega filter',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ht_energyshift',
  'parents': [],
  'property': 'voltage',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Camera index',
  'desc_short': 'Camera index',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'camera_index',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Local person in charge',
  'desc_short': 'Person in charge',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'localperson',
  'parents': ['microscope_demo', 'people'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Publish',
  'desc_short': 'Publish',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'publish',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'boolean'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Date the sample was received',
  'desc_short': 'Date received',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'date_received',
  'parents': ['date_time'],
  'property': None,
  'uri': None,
  'vartype': 'datetime'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Maximum biohazard level for experiments in this project',
  'desc_short': 'Max biohazard level',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'hazard_bl_max',
  'parents': ['project_information', 'hazard'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Publication is in press',
  'desc_short': 'In Press',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'publication_in_press',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'boolean'},


 {'children': [],
  'choices': ['On', 'Off'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'Save Raw Frames',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ddd_raw_frame_save',
  'parents': ['ddd_camera'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Box Size',
  'desc_short': 'Box Size',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'box_size',
  'parents': ['box'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Biomedical Relevance',
  'desc_short': 'Biomedical Relevance',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'description_medical_relevance',
  'parents': ['textual_descriptions', 'biology_of_project'],
  'property': None,
  'uri': None,
  'vartype': 'text'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Image shift 1 deflectors',
  'desc_short': 'Image shift 1 deflectors',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'image_shift_1_deflectors',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Job Title',
  'desc_short': 'Title',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'job_title',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Recent progress on a P41 subproject',
  'desc_short': 'Recent Progress',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'p41_progress',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'text'},


 {'children': [],
  'choices': ['Gatan   2kx2k  MSC',
               'Gatan  4kx4k   US',
               'Gatan   1K   x  1K',
               'Gatan US10kXP CCD'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'The camera used',
  'desc_short': 'Camera',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ccd_id',
  'parents': ['ccd_camera'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Map name',
  'desc_short': 'Map name',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'mapname',
  'parents': ['final_reconstruction', 'identifiers'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Title of a research grant',
  'desc_short': 'Grant Title',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'grant_title',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['ctf', 'magnification', 'binning'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Imaging',
  'desc_short': 'Imaging',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'imaging',
  'parents': ['physical_property'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Stack Filename',
  'desc_short': 'Stack Filename',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_filename',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Visualization Length',
  'desc_short': 'Visualization Length',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'visualization_length',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Number of Labels',
  'desc_short': 'Number of Labels',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_data_nlabl',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Grant Start Date',
  'desc_short': 'Grant Start Date',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'grant_start_date',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'datetime'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Stack X Origin',
  'desc_short': 'Stack X Origin',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_data_xorg',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': ['biological_target',
                'binary_data',
                'identifiers',
                'publication',
                'date_time',
                'url',
                'textual_descriptions',
                'final_reconstruction',
                'people',
                'comments',
                'project_information',
                'hazard',
                'group_descriptors',
                'microscope_demo'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Descriptive Information',
  'desc_short': 'Descriptive Information',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'descriptive_information',
  'parents': ['root'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Image type, ispg',
  'desc_short': 'Image type',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_data_ispg',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Cell angle Gamma',
  'desc_short': 'Cell angle Gamma',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_angle_gamma',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': ['ctf_defocus_set',
                'aperture_objective',
                'ctf_defocus_measured',
                'grid_tem_hole_size',
                'length_camera',
                'diameter_max',
                'angstroms_per_pixel',
                'grid_tem_mesh_size',
                'ctf_astig_defocus_diff',
                'aberration_spherical',
                'ccd_size_pix_y',
                'ccd_size_pix_x',
                'aperture_selarea',
                'wavelength',
                'aperture_condenser',
                'beam_diameter_tem',
                'diameter_min',
                'ccd_pixelsize',
                'aberration_chromatic'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Length',
  'desc_short': 'Length',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'length',
  'parents': ['size'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': ['Retracted'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'Camera Position',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'camera_position',
  'parents': ['microscope'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'Raw Frames Filename Suffix',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ddd_raw_frame_suffix',
  'parents': ['ddd_camera'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Corresponding Author',
  'desc_short': 'Corresponding Author',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'author_corresponding',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': ['Excellent', 'Good', 'Fair', 'Bad'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Comments on the grids',
  'desc_short': 'Grid comments',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'assess_grid',
  'parents': ['textual_descriptions', 'grid'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'RNA sequence',
  'desc_short': 'RNA sequence',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'sequence_rna',
  'parents': ['sequence'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['symmetry_particle'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Symmetry',
  'desc_short': 'Symmetry',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'symmetry',
  'parents': ['physical_property'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'comment_grid',
  'desc_short': 'comment grid',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'comment_grid',
  'parents': ['textual_descriptions'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Journal volume',
  'desc_short': 'Vol journal',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'journal_volume',
  'parents': ['publication'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Piece coordinates for montage',
  'desc_short': 'Piece coordinates for montage',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_data_montage',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': ['area',
                'size_image_ccd_y',
                'size_image_ccd_x',
                'volume',
                'length',
                'mass'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Size',
  'desc_short': 'Size',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'size',
  'parents': ['physical_property'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Title or Subject of this note',
  'desc_short': 'Subject',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'subject_notebook',
  'parents': ['textual_descriptions'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['description_genetic',
                'description_goals',
                'description_medical_relevance',
                'description_purpose',
                'description_background'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Placeholder: biology of project',
  'desc_short': 'Project biological details',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'biology_of_project',
  'parents': ['project_information'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['journal_volume',
                'reference',
                'url_list',
                'abstract',
                'title_structure',
                'corresponding_author_contact',
                'page_range',
                'url_journal',
                'journal_date',
                'pmid',
                'title_publication',
                'name_journal',
                'type_publication'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Publication details',
  'desc_short': 'Publication details',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'publication',
  'parents': ['descriptive_information'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Project title',
  'desc_short': 'Project title',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'name_project',
  'parents': ['project_information', 'microscope_demo'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Objective mini lens',
  'desc_short': 'Objective mini lens',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'objective_mini_lens',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Project PI for the P41 APR',
  'desc_short': 'Project PI',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'p41_project_pi',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'user'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Title of the grid',
  'desc_short': 'Label',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'title_purification',
  'parents': ['identifiers'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'First Author of a publication',
  'desc_short': 'First Author',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'author_first',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'DNA sequence',
  'desc_short': 'DNA sequence',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'sequence_dna',
  'parents': ['sequence'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Stack Z Origin',
  'desc_short': 'Stack Z Origin',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_data_zorg',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Current Tilt Angles',
  'desc_short': 'Current Tilt Angles',
  'immutable': None,
  'indexed': True,
  'iter': True,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_data_tiltangles_current',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Serial number of a P41 grant',
  'desc_short': 'P41 Number',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'p41_serial',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Pages ',
  'desc_short': 'Pages ',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'page_range',
  'parents': ['publication'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'um',
  'desc_long': 'Difference between major and minor defocus in astigmatism',
  'desc_short': 'Astig magnitude',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ctf_astig_defocus_diff',
  'parents': ['ctf', 'length'],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Temperature of microscopy stage',
  'desc_short': 'Temp stage',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'temperature_tem_stage',
  'parents': ['temperature_specimen'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Intended Audience',
  'desc_short': 'Intended Audience',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'talk_audience',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Visualization Synopsis',
  'desc_short': 'Synopsis',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'visualization_synopsis',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'text'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Image encoding',
  'desc_short': 'Image encoding',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'digicamcond_dataformat',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Cond lens 3 DAC',
  'desc_short': 'Cond lens 3 DAC',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'lens_cl3dac',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Grant End Date',
  'desc_short': 'Grant End Date',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'grant_end_date',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'datetime'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'e/A^2',
  'desc_long': 'The dosage received by the camera',
  'desc_short': 'Total dose',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'tem_dose',
  'parents': ['dose'],
  'property': 'exposure',
  'uri': None,
  'vartype': 'float'},


 {'children': ['vitrobot'],
  'choices': ['Vitrobot',
               'Manual   Plunger',
               'Berriman  Plunger',
               'Pneumatic Plunger'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'The vitrification device used',
  'desc_short': 'Vit device',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'vitrification_device',
  'parents': ['equipment', 'vitrification'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': u'\xc5',
  'desc_long': 'Fourier shell correlation',
  'desc_short': 'FSC',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'shell_corr_fourier',
  'parents': ['final_reconstruction'],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'degree',
  'desc_long': 'Astigmatism major axis angle',
  'desc_short': 'Astig major axis angle',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ctf_astig_angle',
  'parents': ['ctf', 'angle'],
  'property': 'angle',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Beam blanked',
  'desc_short': 'Beam blanked',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'digicamcond_blankbeam',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'boolean'},


 {'children': [],
  'choices': ['first', 'second', 'third', 'not recorded'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Selected area aperture',
  'desc_short': 'Sel area apert',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'aperture_selarea',
  'parents': ['length', 'area'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 's',
  'desc_long': 'The time elapsed between applying the sample and blotting',
  'desc_short': 'Wait time',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'vitrobot_time_wait',
  'parents': ['elapsed_time', 'blotting'],
  'property': 'time',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Stack RMS',
  'desc_short': 'Stack RMS',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_data_rms',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': ['concentration_pf',
                'concentration_pml',
                'absorbance_at_wavelength',
                'concentration_solution'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Concentration',
  'desc_short': 'Concentration',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'concentration',
  'parents': ['physical_property'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 's',
  'desc_long': 'The vitrobot can be used in two modes: manual and automatic operation.  During manual operation, the human operator initiates the next respective step by use of the foot pedal.  In automatic operation, the vitrobot proceeds automatically taking a fixed amount of time for each step; the length of this step is recorded in this parameter',
  'desc_short': 'Vit duration',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'vitrobot_time_step',
  'parents': ['elapsed_time', 'blotting'],
  'property': 'time',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Condenser mini lens',
  'desc_short': 'Condenser mini lens',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'condenser_mini_lens',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'The year of a P41 APR',
  'desc_short': 'P41 Year',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'p41_year',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': ['specimen_tilt',
                'angle_illumination',
                'ctf_drift_angle',
                'ctf_astig_angle'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Angle',
  'desc_short': 'Angle',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'angle',
  'parents': ['physical_property'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Maximum signal to noise ratio in radial curve',
  'desc_short': 'SNR Max',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ctf_snr_max',
  'parents': ['ctf'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': ['specimen_holder',
                'scanner',
                'microscope_demo',
                'lens',
                'microscope',
                'camera',
                'grid',
                'vitrification_device',
                'equipment_service',
                'film',
                'cryoholder'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Equipment details',
  'desc_short': 'Equipment details',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'equipment',
  'parents': ['root'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Stack VD2',
  'desc_short': 'Stack VD2',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_data_vd2',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Stack VD1',
  'desc_short': 'Stack VD1',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_data_vd1',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'The title of the publication',
  'desc_short': 'Title',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'title_publication',
  'parents': ['publication'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Placeholder: JADAS',
  'desc_short': 'Placeholder: JADAS',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'mds_blankingtime',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Stage Pos X',
  'desc_short': 'Stage Pos X',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_stagepos_x',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Stage Pos Y',
  'desc_short': 'Stage Pos Y',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_stagepos_y',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'um',
  'desc_long': 'CCD size Y (length) in pixels',
  'desc_short': 'CCD size Y',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ccd_size_pix_y',
  'parents': ['length', 'ccd_camera'],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '?Wobbler?',
  'desc_short': '?Wobbler?',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'eos_alpha',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Link to cryo-holder',
  'desc_short': 'Film holder',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'scanner_cartridge',
  'parents': ['scanner'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Placeholder: JADAS',
  'desc_short': 'Placeholder: JADAS',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'photo_exposuremode',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Visitor List',
  'desc_short': 'Visitor List',
  'immutable': None,
  'indexed': True,
  'iter': True,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'visitors',
  'parents': ['microscope_demo', 'people'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Date of the journal',
  'desc_short': 'Date journal',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'journal_date',
  'parents': ['publication'],
  'property': None,
  'uri': None,
  'vartype': 'datetime'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Map Column S (1=x, 2=y, 3=z)',
  'desc_short': 'Map Column S',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_map_maps',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'co-PIs on a grant',
  'desc_short': 'Grant co-PIs',
  'immutable': None,
  'indexed': True,
  'iter': True,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'grant_copi',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'PubMedCentral ID',
  'desc_short': 'PubMedCentral ID',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'pmcid',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['website', 'url_list', 'url_journal'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'URI References',
  'desc_short': 'URI References',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'url',
  'parents': ['descriptive_information'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Principle Investigator on a grant',
  'desc_short': 'Grant PI',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'grant_pi',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'user'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'Faraday Plate Peak Reading During Last Exposure',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'faraday_plate_peak',
  'parents': ['ddd_camera'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': u'\xc5',
  'desc_long': 'Height of the sample',
  'desc_short': 'Height sample',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'diameter_max',
  'parents': ['length'],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': ['4',
               '6',
               '8',
               '10',
               '50',
               '60',
               '25',
               '100',
               '120',
               '150',
               '200',
               '400',
               '40',
               '20',
               '15',
               '80',
               '12',
               '30'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Intended magnification.',
  'desc_short': 'Set Magnification',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'tem_magnification_set',
  'parents': ['magnification'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Post-blank status',
  'desc_short': 'Post-blank status',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'post_blank_status',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'boolean'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'comment_analysis',
  'desc_short': 'comment analysis',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'comment_analysis',
  'parents': ['textual_descriptions'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'publisher',
  'desc_short': 'Publisher',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'publisher',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Url link (if the paper is printed)',
  'desc_short': 'URL link',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'url_journal',
  'parents': ['url', 'publication'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Person who demonstrates',
  'desc_short': 'Presenter',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'demonstrator',
  'parents': ['microscope_demo', 'people'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Purification procedure',
  'desc_short': 'Purification procedure',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'description_purification',
  'parents': ['textual_descriptions', 'purification'],
  'property': None,
  'uri': None,
  'vartype': 'text'},


 {'children': ['vitrobot_time_wait',
                'vitrobot_humidity',
                'vitrobot_humid_on',
                'vitrobot_time_blot',
                'vitrobot_blots',
                'vitrobot_blot_offset',
                'grid',
                'vitrobot_level_liquid',
                'vitrobot_temp',
                'vitrobot_time_step',
                'vitrobot_time_drain',
                'direction_blotting'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Blotting parameters',
  'desc_short': 'Blotting parameters',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'blotting',
  'parents': ['freezing'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'mrad',
  'desc_long': 'Illumination angle',
  'desc_short': 'Alpha angle',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'angle_illumination',
  'parents': ['angle'],
  'property': 'angle',
  'uri': None,
  'vartype': 'float'},


 {'children': ['film_screen_ratio', 'ccd_screen_ratio', 'dose'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Ratio',
  'desc_short': 'Ratio',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ratio',
  'parents': ['physical_property'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': '%RH',
  'desc_long': 'Vitrobot humidity',
  'desc_short': 'Humidity',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'vitrobot_humidity',
  'parents': ['humidity', 'blotting'],
  'property': 'relative_humidity',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Sample symmetry',
  'desc_short': 'Sample symmetry',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'symmetry_particle',
  'parents': ['biological_target', 'symmetry'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 's',
  'desc_long': 'Length of exposure',
  'desc_short': 'Exposure time',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'time_exposure_tem',
  'parents': ['elapsed_time'],
  'property': 'time',
  'uri': None,
  'vartype': 'float'},


 {'children': ['dilution', 'freezing', 'microscopy', 'purification'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Placeholder: techniques',
  'desc_short': 'Placeholder: techniques',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'experimental-techniques',
  'parents': ['root'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Whatever done after freezing',
  'desc_short': 'Post-freezing comments',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'description_grid_postfreezing',
  'parents': ['textual_descriptions', 'grid'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': u'\xc5',
  'desc_long': 'Actual defocus',
  'desc_short': 'Actual defocus',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'defocus_realphysval',
  'parents': [],
  'property': 'length',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Fine objective lens',
  'desc_short': 'Fine objective lens',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'fine_objective_lens',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'Temperature Control Mode',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ddd_temperature_control_mode',
  'parents': ['ddd_camera'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Film camera',
  'desc_short': 'Film camera',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'film_camera',
  'parents': ['camera'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['blotting', 'vitrification', 'select_technique_freezing'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Freezing parameters',
  'desc_short': 'Freezing parameters',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'freezing',
  'parents': ['experimental-techniques'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Sample storage conditions',
  'desc_short': 'Sample storage conditions',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'description_storage_conditions',
  'parents': ['biological_target', 'textual_descriptions'],
  'property': None,
  'uri': None,
  'vartype': 'text'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Specimen stability',
  'desc_short': 'Specimen stability',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'description_specimen_stability',
  'parents': ['biological_target', 'textual_descriptions'],
  'property': None,
  'uri': None,
  'vartype': 'text'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'Sensor Output Mode',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ddd_sensor_output_mode',
  'parents': ['ddd_camera'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Imaging mode',
  'desc_short': 'Imaging mode',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'eos_imagingmode',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': ['Front',
               'Back',
               'Both',
               'Side',
               'Front, azimuthal variation',
               'Some front some back'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Direction(s) from which the blotting takes place',
  'desc_short': 'Blotting direction(s)',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'direction_blotting',
  'parents': ['blotting'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Project abstract for P41 APR',
  'desc_short': 'Project Abstract',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'p41_abstract',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'text'},


 {'children': ['ccd_screen_ratio',
                'ccd_serialno',
                'ccd_id',
                'ccd_size_pix_y',
                'ccd_size_pix_x',
                'ccd_model',
                'ccd_process_identifier'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'CCD camera parameters',
  'desc_short': 'CCD camera parameters',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ccd_camera',
  'parents': ['camera'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'nm',
  'desc_long': 'Intended defocus',
  'desc_short': 'Intended defocus',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'intendeddefocus_valinnm',
  'parents': [],
  'property': 'length',
  'uri': None,
  'vartype': 'int'},


 {'children': ['elapsed_time',
                'angle',
                'temperature',
                'symmetry',
                'sequence',
                'dose',
                'current',
                'imaging',
                'voltage',
                'wavelength',
                'absorbance',
                'ratio',
                'concentration',
                'humidity',
                'stack',
                'size'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Physical properties',
  'desc_short': 'Physical properties',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'physical_property',
  'parents': ['root'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'degree',
  'desc_long': 'X tilt',
  'desc_short': 'X tilt',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'goniopos_tiltx',
  'parents': [],
  'property': 'angle',
  'uri': None,
  'vartype': 'float'},


 {'children': ['type_session'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Microscopy parameters',
  'desc_short': 'Microscopy parameters',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'microscopy',
  'parents': ['experimental-techniques'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': ['Journal Article', 'Abstract', 'Book', 'P', ''],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Type of publication for P41 APR',
  'desc_short': 'Publication Type',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'p41_publication_type',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'choice'},


 {'children': ['aperture_objective',
                'screen_position',
                'dose_rate_scaling_factor',
                'status_energy_filter',
                'aperture_condenser',
                'tem_name',
                'tem_polepiece',
                'length_camera',
                'ctf',
                'magnification',
                'aberration_spherical',
                'aberration_chromatic',
                'beam_diameter_tem',
                'tem_dose_rate',
                'tem_voltage',
                'tem_lowdose_method',
                'specimen_tilt',
                'lens',
                'position_stage_y',
                'position_stage_x',
                'vacuum_level',
                'tem_spot_size',
                'camera_position'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Microscope parameters',
  'desc_short': 'Microscope parameters',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'microscope',
  'parents': ['equipment', 'microscope_demo'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'The person who performs the service',
  'desc_short': 'Serviced by',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'service_engineer',
  'parents': ['equipment_service', 'people'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'uL',
  'desc_long': 'Before plunging, the grid may be immersed in a solution containing the sample itself or  a solution that would pre-treat the grid; vitrobot_level_liquid measures the volume of this solution',
  'desc_short': 'Vit liquid level',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'vitrobot_level_liquid',
  'parents': ['volume', 'blotting'],
  'property': 'volume',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Sample components and sequences/IDs',
  'desc_short': 'Sample components and sequences/IDs',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'description_genetic',
  'parents': ['textual_descriptions', 'biology_of_project'],
  'property': None,
  'uri': None,
  'vartype': 'text'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'V',
  'desc_long': 'High-tension setting',
  'desc_short': 'High tension',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ht_ht',
  'parents': [],
  'property': 'voltage',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Box Color; hex RGB string',
  'desc_short': 'Box Color',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'box_color',
  'parents': ['box'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Placeholder: JADAS',
  'desc_short': 'Placeholder: JADAS',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'mds_blankingdef',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Structure processing details',
  'desc_short': 'Structure processing details',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'processed_structure',
  'parents': ['textual_descriptions', 'structure'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['ref_type'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Reference (remove)',
  'desc_short': 'Reference (remove)',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'reference',
  'parents': ['publication'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Y beam-shift setting',
  'desc_short': 'Y beam shift',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'def_beamshifty',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'X beam-shift setting',
  'desc_short': 'X beam shift',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'def_beamshiftx',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'pixel',
  'desc_long': 'Top coordinate',
  'desc_short': 'Top coord',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'digicamprm_areatop',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'degree',
  'desc_long': 'Delta X',
  'desc_short': 'Delta X',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'delta_tx',
  'parents': [],
  'property': 'angle',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Condenser lens 1',
  'desc_short': 'Condenser lens 1',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'condenser_lens_1',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Condenser lens 3',
  'desc_short': 'Condenser lens 3',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'condenser_lens_3',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Condenser lens 2',
  'desc_short': 'Condenser lens 2',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'condenser_lens_2',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Slit Width',
  'desc_short': 'Slit Width',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_slitwidth',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': ['<2 um',
               '2  - 5 um',
               '>5 um',
               '1.2 um',
               '2',
               '3.5',
               '3.5',
               '2 grids R2/2, 1  grid R1.2/1.3',
               'variable',
               'homemade'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Grid hole size ',
  'desc_short': 'Grid holesize ',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'grid_tem_hole_size',
  'parents': ['length', 'grid', 'area'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Technical Contact',
  'desc_short': 'Technical Contact',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'contact_technical',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'cm',
  'desc_long': 'The diameter of the electron beam',
  'desc_short': 'Beam width',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'beam_diameter_tem',
  'parents': ['length', 'microscope'],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Screen status',
  'desc_short': 'Screen status',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'post_acquisition_screen_status_lowered',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'boolean'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Pole piece',
  'desc_short': 'Pole piece',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'tem_polepiece',
  'parents': ['microscope'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'The title of the structure',
  'desc_short': 'Structure title',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'title_structure',
  'parents': ['identifiers', 'publication'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'ms',
  'desc_long': 'Zeiss exposure',
  'desc_short': 'Zeiss expos',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'zeiss_exposure',
  'parents': ['elapsed_time', 'scanner'],
  'property': 'time',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': '%RH',
  'desc_long': 'Room humidity',
  'desc_short': 'Room humid',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'humidity_ambient',
  'parents': ['humidity'],
  'property': 'relative_humidity',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Original Tilt Angles',
  'desc_short': 'Original Tilt Angles',
  'immutable': None,
  'indexed': True,
  'iter': True,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_data_tiltangles_orig',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'comment_pretreatment_grid',
  'desc_short': 'comment pretreatment grid',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'comment_pretreatment_grid',
  'parents': ['textual_descriptions'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'FPGA Version',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ddd_fpga_version',
  'parents': ['ddd_camera'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Number of bytes per section in the extended header, nint',
  'desc_short': 'Ext. header bytes per section',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_data_bytespersection',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Placeholder: JADAS',
  'desc_short': 'Placeholder: JADAS',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'photo_filmtext',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Extended header flags (binary), nreal',
  'desc_short': 'Ext. header flags',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_data_extheaderflags',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Corresponding author contact information',
  'desc_short': 'Corresponding Auth Email',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'corresponding_author_contact',
  'parents': ['publication', 'people'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Maximum tilt angle of stack',
  'desc_short': 'Maximum tilt angle of stack',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_maxangle',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Federal agency or other source for a research grant',
  'desc_short': 'Grant Source',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'grant_source',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Protein sequence (one letter amino acid abbreviations)',
  'desc_short': 'Protein sequence',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'sequence_protein',
  'parents': ['sequence'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'CCD model number',
  'desc_short': 'CCD model no',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ccd_model',
  'parents': ['identifiers', 'ccd_camera'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Sample storage location',
  'desc_short': 'Sample storage location',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'description_storage',
  'parents': ['biological_target', 'textual_descriptions'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Volume size X',
  'desc_short': 'Volume size X',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_size_nx',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 's',
  'desc_long': 'Pre-irradiation time',
  'desc_short': 'Pre-irradiation',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'digicamcond_preirradiation',
  'parents': [],
  'property': 'time',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'degC',
  'desc_long': '',
  'desc_short': 'Water Line Temperature',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ddd_temperature_water_line',
  'parents': ['temperature'],
  'property': 'temperature',
  'uri': None,
  'vartype': 'float'},


 {'children': ['temperature_tem_stage'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'K',
  'desc_long': 'Specimen temperature',
  'desc_short': 'Specimen temp',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'temperature_specimen',
  'parents': ['temperature'],
  'property': 'temperature',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Placeholder: JADAS',
  'desc_short': 'Placeholder: JADAS',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'photo_filmnumber',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Volume size Z',
  'desc_short': 'Volume size Z',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_size_nz',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'List of authors',
  'desc_short': 'Authors (Lastname, F. M.)',
  'immutable': None,
  'indexed': True,
  'iter': True,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'author_list',
  'parents': ['people'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': ['Technical_Core',
               'Dissemination',
               'Collaboration',
               'Service'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Project type for P41 APR',
  'desc_short': 'Project Type',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'p41_project_type',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'choice'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'mm',
  'desc_long': 'maxres',
  'desc_short': 'maxres',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'maxres',
  'parents': [],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Title of a project for P41 APR',
  'desc_short': 'Project Title',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'p41_project_title',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Proj lens 1 DAC',
  'desc_short': 'Proj lens 1 DAC',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'lens_pl1dac',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Bright-dark mode',
  'desc_short': 'Bright-dark',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'eos_brightdarkmode',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': '%',
  'desc_long': 'Amplitude contrast',
  'desc_short': 'Amp contrast',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ctf_ampcont',
  'parents': ['ctf'],
  'property': 'percentage',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Ice type',
  'desc_short': 'Ice type',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ice_type',
  'parents': ['textual_descriptions', 'ice'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'degC',
  'desc_long': '',
  'desc_short': 'Vitrobot temperature',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'vitrobot_temp',
  'parents': ['temperature', 'blotting'],
  'property': 'temperature',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'PubMed ID',
  'desc_short': 'PubMed ID',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'pmid',
  'parents': ['publication'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['file_binary', 'file_volume', 'file_binary_image'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Attachments',
  'desc_short': 'Attachments',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'binary_data',
  'parents': ['descriptive_information'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Name of a conference for a publication',
  'desc_short': 'Conference Name',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'name_conference',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['id_aliquot',
                'description_aliquot',
                'aliquot_used',
                'aliquot_storage',
                'volume_aliquot',
                'aliquot_count',
                'comment_aliquot'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Aliquot parameters',
  'desc_short': 'Aliquot parameters',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'aliquot',
  'parents': ['biological_target'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Aliquot storage conditions',
  'desc_short': 'Aliquot storage conditions',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'aliquot_storage',
  'parents': ['aliquot'],
  'property': None,
  'uri': None,
  'vartype': 'text'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Maximum pixel value',
  'desc_short': 'Maximum pixel value',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_pixel_max',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Unique sequential identifier for P41 projects',
  'desc_short': 'Subproject ID',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'p41_subprojectid',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['assess_ice_comments', 'ice_type', 'assess_ice_thick'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Ice parameters',
  'desc_short': 'Ice parameters',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ice',
  'parents': ['vitrification'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Spot alignment 1 deflectors',
  'desc_short': 'Spot alignment 1 deflectors',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'spot_alignment_1_deflectors',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Space group number, nsymbt',
  'desc_short': 'Space group number',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_data_nsymbt',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'Temperature Control',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ddd_temperature_control',
  'parents': ['ddd_camera'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Service date',
  'desc_short': 'Service date',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'service_date',
  'parents': ['date_time', 'equipment_service'],
  'property': None,
  'uri': None,
  'vartype': 'datetime'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Holder',
  'desc_short': 'Holder',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'specimen_holder',
  'parents': ['equipment'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'ID of the recorded frame ',
  'desc_short': 'Frame ID ',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'id_ccd_frame',
  'parents': ['identifiers'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'mg/ml',
  'desc_long': 'Solution concentration',
  'desc_short': 'Concentration',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'concentration_solution',
  'parents': ['concentration'],
  'property': 'concentration',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Spectrum Mode',
  'desc_short': 'Spectrum Mode',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'eos_spectrummode',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'comment_project_desc',
  'desc_short': 'comment project desc',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'comment_project_desc',
  'parents': ['textual_descriptions'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'comment_specimen_stability',
  'desc_short': 'comment specimen stability',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'comment_specimen_stability',
  'parents': ['textual_descriptions'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': ['Dark'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'Exposure Mode',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ddd_exposure_mode',
  'parents': ['ddd_camera'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'Pi   Amp/cm2',
  'desc_long': 'Screen current',
  'desc_short': 'Screen current',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'current_screen',
  'parents': ['current'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'pixel',
  'desc_long': 'Left coordinate',
  'desc_short': 'Left coord',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'digicamprm_arealeft',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 's',
  'desc_long': 'The time elapsed between blotting and plunging',
  'desc_short': 'Drain time',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'vitrobot_time_drain',
  'parents': ['elapsed_time', 'blotting'],
  'property': 'time',
  'uri': None,
  'vartype': 'float'},


 {'children': ['vitrification_device', 'ice'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Vitrification parameters',
  'desc_short': 'Vitrification parameters',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'vitrification',
  'parents': ['freezing'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Title of the grid',
  'desc_short': 'Grid label',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'title_grid',
  'parents': ['identifiers'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Placeholder: JADAS',
  'desc_short': 'Placeholder: JADAS',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'mds_mdsmode',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'List of usernames associated with project',
  'desc_short': 'Project Investigators',
  'immutable': None,
  'indexed': True,
  'iter': True,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'p41_project_investigators',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'user'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Accession ID',
  'desc_short': 'Accession ID',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'visualization_accession',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['vitrobot_time_wait',
                'film_time_develop',
                'time_exposure_tem',
                'vitrobot_time_blot',
                'vitrobot_time_drain',
                'zeiss_exposure',
                'vitrobot_blot_offset',
                'rate',
                'vitrobot_time_step',
                'time_glowdischarge'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'Elapsed Time',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'elapsed_time',
  'parents': ['physical_property'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'mm',
  'desc_long': 'Camera units',
  'desc_short': 'Camera units',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'camera_units',
  'parents': [],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Intermediate lens 2',
  'desc_short': 'Intermediate lens 2',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'intermediate_lens_2',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': u'\xc5',
  'desc_long': 'Resolution cutoff for low-pass filter',
  'desc_short': 'Cut-off point',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'resolution_cutoff',
  'parents': ['final_reconstruction'],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Service type',
  'desc_short': 'Service type',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'service_type',
  'parents': ['equipment_service'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'mm',
  'desc_long': 'Spherical aberration',
  'desc_short': 'C sub s',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'aberration_spherical',
  'parents': ['length', 'microscope'],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'mm',
  'desc_long': 'Chromatic aberration',
  'desc_short': 'C sub c',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'aberration_chromatic',
  'parents': ['length', 'microscope'],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Intermediate lens 3',
  'desc_short': 'Intermediate lens 3',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'intermediate_lens_3',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': ['1', '2', '4', '8', '16'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'Binning Y',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'binning_y',
  'parents': ['binning'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': ['1', '2', '4', '8', '16'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'Binning X',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'binning_x',
  'parents': ['binning'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'PI Credits',
  'desc_short': 'PI Credits',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'visualization_credits_pi',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'degC',
  'desc_long': '',
  'desc_short': 'Cold Finger Temperature',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ddd_temperature_cold_finger',
  'parents': ['temperature'],
  'property': 'temperature',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Number of good grids',
  'desc_short': 'Good grids',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'grids_tem_good',
  'parents': ['grid'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Buffer used for dilution',
  'desc_short': 'Dilution buffer',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'description_buffer_dilution',
  'parents': ['textual_descriptions', 'dilution'],
  'property': None,
  'uri': None,
  'vartype': 'text'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Service description',
  'desc_short': 'Service desc',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'service_description',
  'parents': ['equipment_service'],
  'property': None,
  'uri': None,
  'vartype': 'text'},


 {'children': ['stack_size_nx',
                'stack_size_ny',
                'stack_size_nz',
                'stack_minangle',
                'stack_data_labels',
                'stack_data_yorg',
                'stack_start_ny',
                'stack_start_nz',
                'stack_size_zlen',
                'stack_data_nd2',
                'stack_size_my',
                'stack_data_nd1',
                'stack_data_rms',
                'stack_size_mx',
                'stack_data_montage',
                'stack_slitwidth',
                'stack_data_extheaderflags',
                'stack_intensity',
                'stack_data_nlabl',
                'stack_totaldose',
                'stack_angle_alpha',
                'stack_data_lens',
                'stack_saxtonincrement',
                'stack_maxangle',
                'stack_data_xorg',
                'stack_data_vd2',
                'stack_data_vd1',
                'stack_data_cmap',
                'stack_pixel_mean',
                'stack_data_idtype',
                'stack_data_zorg',
                'stack_data_tiltangles_current',
                'stack_data_tiltangles_orig',
                'stack_size_ylen',
                'stack_stagepos',
                'stack_map_mapr',
                'stack_map_maps',
                'stack_data_extheadersize',
                'stack_pixel_max',
                'stack_start_nx',
                'stack_size_xlen',
                'stack_data_nsymbt',
                'stack_angle_beta',
                'stack_data_ispg',
                'stack_angle_gamma',
                'stack_data_creatid',
                'stack_data_mode',
                'stack_map_mapc',
                'stack_pixel_min',
                'stack_size_mz',
                'stack_data_bytespersection',
                'stack_fixedincrement',
                'stack_data_stamp'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Image stack and tomography Parameters',
  'desc_short': 'Image stack parameters',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack',
  'parents': ['physical_property'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Screen closed',
  'desc_short': 'Screen closed',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'digicamcond_closescreen',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'boolean'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'pixel',
  'desc_long': 'Bottom coordinate',
  'desc_short': 'Bottom coord',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'digicamprm_areabottom',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Camera name',
  'desc_short': 'Camera name',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'digicamprm_cameraname',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['temperature_specimen',
                'ddd_temperature_cold_finger',
                'temperature_ambient',
                'ddd_temperature_water_line',
                'vitrobot_temp',
                'ddd_temperature_detector'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Temperature',
  'desc_short': 'Temperature',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'temperature',
  'parents': ['physical_property'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Aliquot ID used',
  'desc_short': 'Aliquot ID used',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'aliquot_used',
  'parents': ['aliquot'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'nm',
  'desc_long': 'Absorbance of the sample at a specific wavelength (wavelength_at_absorbance)',
  'desc_short': 'Absorbance',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'absorbance_at_wavelength',
  'parents': ['absorbance', 'biological_target', 'concentration'],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': ['title_purification',
                'mapname',
                'id_aliquot',
                'tem_name',
                'ccd_serialno',
                'scanner_film',
                'title_structure',
                'film_type',
                'name_specimen',
                'recname',
                'id_micrograph',
                'id_ccd_frame',
                'microscope_serialno',
                'ccd_model',
                'id_grid_batch',
                'title_freezing',
                'ccd_process_identifier',
                'number_exposure',
                'title_grid'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Unique or restrictive identifiers',
  'desc_short': 'Unique or restrictive identifiers',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'identifiers',
  'parents': ['descriptive_information'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'nm',
  'desc_long': 'Defocus',
  'desc_short': 'Defocus',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'defocus',
  'parents': [],
  'property': 'length',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Map Column C (1=x, 2=y, 3=z)',
  'desc_short': 'Map Column C',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_map_mapc',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Title of a P41 grant',
  'desc_short': 'P41 Title',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'p41_title',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'City where a conference took place',
  'desc_short': 'Conference City',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'city_conference',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Size of the electron beam spot',
  'desc_short': 'Spot size',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'tem_spot_size',
  'parents': ['microscope', 'area'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Condenser shift deflectors',
  'desc_short': 'Condenser shift deflectors',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'condenser_shift_deflectors',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': ['60 degree #1',
               '60 degree #2',
               '70 degree #1',
               '70 degree #2',
               '80 degree'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Cryoholder(s)',
  'desc_short': 'Cryoholder',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'cryoholder',
  'parents': ['equipment'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': u'\xc5',
  'desc_long': 'Inner radius',
  'desc_short': 'Inner radius',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'diameter_min',
  'parents': ['length'],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Select when complete and ready for the APR',
  'desc_short': 'Ready for APR (Wah)',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'p41_project_ready',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'boolean'},


 {'children': [],
  'choices': ['On', 'Off'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'Save Summed Image',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ddd_raw_frame_save_summed',
  'parents': ['ddd_camera'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['tem_dose'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Dose',
  'desc_short': 'Dose',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'dose',
  'parents': ['physical_property', 'ratio'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Dose rate scaling factor',
  'desc_short': 'Dose rate scaling factor',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'dose_rate_scaling_factor',
  'parents': ['microscope'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': ['voltage_lens', 'tem_voltage'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Voltage',
  'desc_short': 'Voltage',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'voltage',
  'parents': ['physical_property'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'The person(source) who/which provides the sample',
  'desc_short': 'Sample provider',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'provided_by',
  'parents': ['people'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'mg/ml',
  'desc_long': 'Aliquot concentration in mg/ml',
  'desc_short': 'Aliquot conc mg/ml',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'concentration_pf',
  'parents': ['concentration'],
  'property': 'concentration',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Specimen name',
  'desc_short': 'Specimen name',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'name_specimen',
  'parents': ['biological_target', 'identifiers'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': u'\xc5/pixel',
  'desc_long': 'Apixel',
  'desc_short': 'A/pixel',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'angstroms_per_pixel',
  'parents': ['length'],
  'property': 'resolution',
  'uri': None,
  'vartype': 'float'},


 {'children': ['service_type',
                'service_description',
                'service_engineer',
                'service_date'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Equipment service parameters',
  'desc_short': 'Equipment service parameters',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'equipment_service',
  'parents': ['equipment'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'pixel',
  'desc_long': 'Image size X',
  'desc_short': 'Image size X',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'x_value',
  'parents': ['final_reconstruction'],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'Dark Frame Status',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ddd_dark_frame_status',
  'parents': ['ddd_camera'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'ROI Offset Y',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'roi_offset_y',
  'parents': ['camera'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'ROI Offset X',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'roi_offset_x',
  'parents': ['camera'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Mean pixel value',
  'desc_short': 'Mean pixel value',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_pixel_mean',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': ['5 step',
               'UF',
               'Yoshi  box',
               'MDS',
               'FasTEM  MDS',
               'Philips',
               'manual',
               '15',
               '20'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Low dose method',
  'desc_short': 'Low dose method',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'tem_lowdose_method',
  'parents': ['microscope'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Workshop Instructors',
  'desc_short': 'Instructors',
  'immutable': None,
  'indexed': True,
  'iter': True,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'instructors',
  'parents': ['people'],
  'property': None,
  'uri': None,
  'vartype': 'user'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'ROI Offset Width',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'roi_offset_w',
  'parents': ['camera'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'ROI Offset Height',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'roi_offset_h',
  'parents': ['camera'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Id number of a grant',
  'desc_short': 'Grant Number',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'grant_number',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': ['Zeiss',
               'Nikon',
               'Minolta',
               'Nikon Blue',
               'Nikon Red',
               'Nikon  Mike',
               'Nikon9000  Htet',
               'CCD',
               'JOEL 1230 CCD  (2Kx2K)',
               'CCD  2Kx2K'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Scanner ID',
  'desc_short': 'Scanner ID',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'scanner_film',
  'parents': ['identifiers', 'scanner', 'film'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['select_substrate_grid_prep',
                'assess_grid',
                'select_substrate_grid',
                'grid_tem_type',
                'grid_tem_hole_size',
                'grids_tem_lost',
                'grids_tem_used',
                'grid_tem_mesh_size',
                'description_grid_prefreezing',
                'grids_tem_good',
                'description_grid_postfreezing'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Grid parameters',
  'desc_short': 'Grid parameters',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'grid',
  'parents': ['equipment', 'blotting'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'degree',
  'desc_long': 'Delta X',
  'desc_short': 'Delta X',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'delta_ty',
  'parents': [],
  'property': 'angle',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 's',
  'desc_long': 'Glowdischarge time prior to freezing',
  'desc_short': 'Glowdischarge time',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'time_glowdischarge',
  'parents': ['elapsed_time'],
  'property': 'time',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Minimum pixel value',
  'desc_short': 'Minimum pixel value',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_pixel_min',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Defocus setting',
  'desc_short': 'Defocus setting',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'defocus_absdac',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Frame Dose',
  'desc_short': 'Frame Dose',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_dose',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '???',
  'desc_short': '???',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'eos_magcamindex',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Comments on the ice condition',
  'desc_short': 'Ice cond',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'assess_ice_comments',
  'parents': ['textual_descriptions', 'ice'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'count',
  'desc_long': 'Total magnification factor after calibration by unspecified means',
  'desc_short': 'Calibrated mag',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'tem_magnification_measured',
  'parents': ['magnification'],
  'property': 'count',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Y beam-tilt setting',
  'desc_short': 'Y beam tilt',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'def_beamtilty',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': ['description_buffer_dilution'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Dilution',
  'desc_short': 'Dilution',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'dilution',
  'parents': ['experimental-techniques'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Vitrobot parameters',
  'desc_short': 'Vitrobot parameters',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'vitrobot',
  'parents': ['vitrification_device'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'Sensor Coarse Gain',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ddd_sensor_coarse_gain',
  'parents': ['ddd_camera'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Due Date',
  'desc_short': 'Due Date',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'date_due',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'datetime'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Stack Labels',
  'desc_short': 'Stack Labels',
  'immutable': None,
  'indexed': True,
  'iter': True,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_data_labels',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['organizers',
                'modifyuser',
                'name_pi',
                'provided_by',
                'name_receiver',
                'frozen_by',
                'localperson',
                'instructors',
                'trainer',
                'author_list',
                'corresponding_author_contact',
                'visitors',
                'scanned_by',
                'service_engineer',
                'name_contact',
                'performed_by',
                'demonstrator',
                'owner',
                'project_investigators',
                'creator'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'People',
  'desc_short': 'People',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'people',
  'parents': ['descriptive_information'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Description of storage location',
  'desc_short': 'Description of storage location',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'description_storage_location',
  'parents': ['biological_target', 'textual_descriptions'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Interm lens 3DAC',
  'desc_short': 'Interm lens 3 DAC',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'lens_il3dac',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Person who scanned',
  'desc_short': 'Scanned by',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'scanned_by',
  'parents': ['people'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Cond lens 2 DAC',
  'desc_short': 'Cond lens 2 DAC',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'lens_cl2dac',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Total Dose for Tilt Series',
  'desc_short': 'Total Dose for Tilt Series',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_totaldose',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Data Mode, 0 = unsigned byte, 1 = short int, 2 = float, 3 = short*2, 4 = float*2',
  'desc_short': 'Data Mode',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_data_mode',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Interm lens x stigmator',
  'desc_short': 'Interm lens x stigmator',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'def_ilstigx',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'cm',
  'desc_long': 'Camera length',
  'desc_short': 'Camera length',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'length_camera',
  'parents': ['length', 'microscope'],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 's',
  'desc_long': 'Exposure time',
  'desc_short': 'Exposure',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'digicamprm_exposure',
  'parents': [],
  'property': 'time',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'kV',
  'desc_long': 'lens_voltage_objective',
  'desc_short': 'Voltage',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'lens_voltage_objective',
  'parents': ['lens', 'voltage_lens', 'tem_voltage'],
  'property': 'voltage',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'um',
  'desc_long': 'Delta X',
  'desc_short': 'Delta X',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'delta_x',
  'parents': [],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'um',
  'desc_long': 'Delta X',
  'desc_short': 'Delta X',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'delta_y',
  'parents': [],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Person who received the material',
  'desc_short': 'Received by',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'name_receiver',
  'parents': ['people'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Links',
  'desc_short': 'Links',
  'immutable': None,
  'indexed': True,
  'iter': True,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'url_list',
  'parents': ['url', 'publication'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['box'],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Image processing related parameters',
  'desc_short': 'Image processing',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'processing',
  'parents': ['root'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Principal investigator',
  'desc_short': 'PI',
  'immutable': None,
  'indexed': True,
  'iter': True,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'name_pi',
  'parents': ['people'],
  'property': None,
  'uri': None,
  'vartype': 'user'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'pixel',
  'desc_long': 'Image size Y',
  'desc_short': 'Image size Y',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'y_value',
  'parents': ['final_reconstruction'],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Percent of grant applied to a P41 subproject',
  'desc_short': 'Percent Effort',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'p41_percent',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Description',
  'desc_short': 'Reconst desc',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'description_reconstruction',
  'parents': ['textual_descriptions'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'List of editors',
  'desc_short': 'Editors',
  'immutable': None,
  'indexed': True,
  'iter': True,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'author_editor_list',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['absorbance_at_wavelength'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Absorbance',
  'desc_short': 'Absorbance',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'absorbance',
  'parents': ['physical_property'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'kDa',
  'desc_long': 'Mass of the target protein/sample',
  'desc_short': 'Mass of the target',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'mass_specimen',
  'parents': ['biological_target', 'mass'],
  'property': 'mass',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': """Y coordinate of microscope's stage position during imaging""",
  'desc_short': 'Stage pos, Y',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'position_stage_y',
  'parents': ['microscope'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': """X coordinate of microscope's stage position during imaging""",
  'desc_short': 'Stage pos, X',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'position_stage_x',
  'parents': ['microscope'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Substrate preparation',
  'desc_short': 'Substrate comments',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'select_substrate_grid_prep',
  'parents': ['grid'],
  'property': None,
  'uri': None,
  'vartype': 'text'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Cell size X',
  'desc_short': 'Cell size X',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_size_xlen',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Cell angle Beta',
  'desc_short': 'Cell angle Beta',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_angle_beta',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'degC',
  'desc_long': 'Room temperature',
  'desc_short': 'Room temp',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'temperature_ambient',
  'parents': ['temperature'],
  'property': 'temperature',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'nm',
  'desc_long': 'Wavelength of the sample at its absorbance peak',
  'desc_short': 'Wavelength',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'wavelength_at_absorbance',
  'parents': ['biological_target'],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'This person is responsible for the next progress in this project. It should be updated to reflect who is currently responsible for periodic progress updates. This field should not relate to authorship expectations.',
  'desc_short': 'Current Workflow',
  'immutable': None,
  'indexed': True,
  'iter': True,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'project_block',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'user'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Stage Position',
  'desc_short': 'Stage Position',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_stagepos',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Workshop Organizers',
  'desc_short': 'Workshop Organizers',
  'immutable': None,
  'indexed': True,
  'iter': True,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'organizers',
  'parents': ['people'],
  'property': None,
  'uri': None,
  'vartype': 'user'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Number of boxes',
  'desc_short': 'Box Count',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'box_count',
  'parents': ['box'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Sub image starting point X',
  'desc_short': 'Subimage origin X',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_start_nx',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Sub image starting point Y',
  'desc_short': 'Subimage origin Y',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_start_ny',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Sub image starting point Z',
  'desc_short': 'Subimage origin Z',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_start_nz',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Map Column R (1=x, 2=y, 3=z)',
  'desc_short': 'Map Column R',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_map_mapr',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': ['Glow Discharge',
               'Plasma Cleaner',
               'Carbon Evaporation',
               'Organic Solvent Wash',
               'Water Wash',
               'Pre-irradiated'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Whatever done prior to the freezing',
  'desc_short': 'Pre-freezing comments',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'description_grid_prefreezing',
  'parents': ['textual_descriptions', 'grid'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': None,
  'desc_short': 'Presentation comments',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'comment_presentation',
  'parents': ['textual_descriptions'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'comment_aliquot',
  'desc_short': 'comment aliquot',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'comment_aliquot',
  'parents': ['aliquot', 'textual_descriptions'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Screen to CCD ratio',
  'desc_short': 'Screen/CCD ratio',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ccd_screen_ratio',
  'parents': ['ratio', 'ccd_camera'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Microscope name',
  'desc_short': 'Microscope name',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'tem_name',
  'parents': ['microscope', 'identifiers'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['grid_tem_mesh_size',
                'aperture_selarea',
                'grid_tem_hole_size',
                'tem_spot_size'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Area',
  'desc_short': 'Area',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'area',
  'parents': ['size'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': ['CCD', 'DDD', 'SO-163'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Detector',
  'desc_short': 'Detector',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'film_type',
  'parents': ['identifiers', 'film'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Interm lens 2 DAC',
  'desc_short': 'Interm lens 2 DAC',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'lens_il2dac',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Number of aliquots shipped with these conditions',
  'desc_short': 'Aliquots received',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'aliquot_count',
  'parents': ['aliquot'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'Sensor Offset',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ddd_sensor_offset',
  'parents': ['ddd_camera'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': ['N/A', 'Service', 'Collaborative', 'Core'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Project type',
  'desc_short': 'Project type',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'project_type',
  'parents': ['project_information'],
  'property': None,
  'uri': None,
  'vartype': 'choice'},


 {'children': ['volume_aliquot',
                'grid_volume_applied',
                'vitrobot_level_liquid'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Volume',
  'desc_short': 'Volume',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'volume',
  'parents': ['size'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Binning',
  'desc_short': 'Binning',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'digicamprm_binning',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Background material for specimen',
  'desc_short': 'Background Info',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'description_background',
  'parents': ['textual_descriptions', 'biology_of_project'],
  'property': None,
  'uri': None,
  'vartype': 'text'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Extended header size',
  'desc_short': 'Extended header size',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_data_extheadersize',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Reference type',
  'desc_short': 'Reference type',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ref_type',
  'parents': ['reference'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': ['1', '2', '3', '4'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Number of exposure',
  'desc_short': 'Exposure #',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'number_exposure',
  'parents': ['identifiers'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': '%',
  'desc_long': 'Zeiss contrast',
  'desc_short': 'Zeiss contrast',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'zeiss_contrast',
  'parents': ['scanner'],
  'property': 'percentage',
  'uri': None,
  'vartype': 'float'},


 {'children': ['file_volume_masks'],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '3D Density map or volume',
  'desc_short': '3D Volume',
  'immutable': False,
  'indexed': True,
  'iter': True,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'file_volume',
  'parents': ['binary_data'],
  'property': None,
  'uri': None,
  'vartype': 'binary'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Placeholder: JADAS',
  'desc_short': 'Placeholder: JADAS',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'mds_shutterdelay',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Illumination Mode',
  'desc_short': 'Illumination Mode',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'eos_illuminationmode',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Title of a chapter or section',
  'desc_short': 'Chapter Title',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'name_chapter',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': ['Data, Good Quality',
               'Data, Medium Quality',
               'Data, Poor Quality',
               'Diffraction',
               'Em Calibration',
               'Low Magnification'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'User-assigned image category',
  'desc_short': 'Image category',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'category_image',
  'parents': ['textual_descriptions'],
  'property': None,
  'uri': None,
  'vartype': 'choice'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Volume size Y',
  'desc_short': 'Volume size Y',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_size_ny',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Minimum tilt angle of stack',
  'desc_short': 'Minimum tilt angle of stack',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_minangle',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': ['zeiss_exposure',
                'scan_step',
                'scan_average',
                'zeiss_contrast',
                'zeiss_brightness',
                'scanner_film',
                'scanner_cartridge',
                'source_sample',
                'nikon_gain'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Scanned micrograph parameters',
  'desc_short': 'Scanned micrograph parameters',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'scanner',
  'parents': ['equipment'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'Data Output Mode',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ddd_data_output_mode',
  'parents': ['ddd_camera'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Identifier used as the record title',
  'desc_short': 'Record title',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'recname',
  'parents': ['identifiers'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Journal article abstract',
  'desc_short': 'Abstract text',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'abstract',
  'parents': ['publication'],
  'property': None,
  'uri': None,
  'vartype': 'text'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'mm',
  'desc_long': 'The angle at which the two pads meet at the point of impact with the grid.  Positive values indicate that less pressure than the default of zero is applied during blotting (e.g., +2).  Lower offset means that a pressure higher than the default is being applied (e.g., -2).',
  'desc_short': 'Vit offset',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'vitrobot_blot_offset',
  'parents': ['elapsed_time', 'blotting'],
  'property': 'length',
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': ['Off', '0', '1', '10', '15', '18', '20', '30'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'The type of energy filter ',
  'desc_short': 'Energy filter ',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'status_energy_filter',
  'parents': ['microscope'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'pixel',
  'desc_long': 'Image size Z',
  'desc_short': 'Image size Z',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'z_value',
  'parents': ['final_reconstruction'],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Intermediate lens 1',
  'desc_short': 'Intermediate lens 1',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'intermediate_lens_1',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': ['film_screen_ratio',
                'film_time_develop',
                'scanner_film',
                'film_type'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Film parameters',
  'desc_short': 'Film parameters',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'film',
  'parents': ['equipment'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'Last Gain Frame Dataset',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ddd_last_gain_frame_dataset',
  'parents': ['ddd_camera'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': ['On', 'Off'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'Gain Correction',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ddd_gain_correction',
  'parents': ['ddd_camera'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Cell angle Alpha',
  'desc_short': 'Cell angle Alpha',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_angle_alpha',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Number of grids used',
  'desc_short': 'Num grids used',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'grids_tem_used',
  'parents': ['grid'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': ['agenda',
                'support',
                'hazard_bl_max',
                'project_type',
                'biology_of_project',
                'name_project'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Project Details',
  'desc_short': 'Project Details',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'project_information',
  'parents': ['descriptive_information'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Year grant stopped being referenced in P41 APR',
  'desc_short': 'End for p41',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'grant_p41_ref_end',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'datetime'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'This parameter is used for testing the database',
  'desc_short': 'Test Parameter',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'test',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'comment_postfreezing_grid',
  'desc_short': 'comment postfreezing grid',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'comment_postfreezing_grid',
  'parents': ['textual_descriptions'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'CCD serial number',
  'desc_short': 'CCD serial no',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ccd_serialno',
  'parents': ['identifiers', 'ccd_camera'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['lens_voltage_projector',
                'lens_voltage_objective',
                'current_lens',
                'voltage_lens'],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Placeholder: lens',
  'desc_short': 'Lens Parameters',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'lens',
  'parents': ['equipment', 'microscope'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['binning_hardware_y',
                'binning_hardware_x',
                'binning_y',
                'binning_x'],
  'choices': ['1', '2', '4', '8', '16'],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Binning',
  'desc_short': 'Binning',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'binning',
  'parents': ['imaging'],
  'property': None,
  'uri': None,
  'vartype': 'float'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Stigmator level',
  'desc_short': 'Stigmator level',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'eos_stiglevel',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'The serial number of the microscope',
  'desc_short': 'Serial no',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'microscope_serialno',
  'parents': ['identifiers'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Whether the P41 was acknowledged in a publication',
  'desc_short': 'Include in P41 Report',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'p41_acknowledged',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'boolean'},


 {'children': ['processed_structure'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Placeholder: structure',
  'desc_short': 'Placeholder: structure',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'structure',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': ['date_end',
                'date_start',
                'creationtime',
                'date_received',
                'modifytime',
                'date_submit',
                'service_date',
                'date_occurred'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Date and Time',
  'desc_short': 'Date and time parameters',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'date_time',
  'parents': ['descriptive_information'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': [],
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': '',
  'desc_short': 'Raw Frame Type',
  'immutable': False,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ddd_raw_frame_type',
  'parents': ['ddd_camera'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'comment_project_progress',
  'desc_short': 'comment project progress',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'comment_project_progress',
  'parents': ['textual_descriptions'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Notes',
  'desc_short': 'Notes',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'acquire_text',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'text'},


 {'children': ['y_value',
                'comment_reconstruction',
                'x_value',
                'z_value',
                'mapname',
                'resolution_cutoff',
                'parameters_reconstruction',
                'shell_corr_fourier'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Reconstruction details',
  'desc_short': 'Reconstruction details',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'final_reconstruction',
  'parents': ['descriptive_information'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Obj lens y stigmator',
  'desc_short': 'Obj lens y stigmator',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'def_olstigy',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Image shift 2 deflectors',
  'desc_short': 'Image shift 2 deflectors',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'image_shift_2_deflectors',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Stack creator ID. This may not map to a database user.',
  'desc_short': 'Stack creator ID',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack_data_creatid',
  'parents': ['stack'],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Interm lens y stigmator',
  'desc_short': 'Interm lens y stigmator',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'def_ilstigy',
  'parents': [],
  'property': None,
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Goals of the project',
  'desc_short': 'Project goals',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'description_goals',
  'parents': ['textual_descriptions',
               'biology_of_project',
               'microscope_demo'],
  'property': None,
  'uri': None,
  'vartype': 'text'},


 {'children': ['mass_specimen'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Mass',
  'desc_short': 'Mass',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'mass',
  'parents': ['size'],
  'property': None,
  'uri': None,
  'vartype': 'string'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': 'min',
  'desc_long': 'Develop time (in min)',
  'desc_short': 'Film develop time',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'film_time_develop',
  'parents': ['elapsed_time', 'film'],
  'property': 'time',
  'uri': None,
  'vartype': 'int'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'The date the paper submitted',
  'desc_short': 'Date submit',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'date_submit',
  'parents': ['date_time'],
  'property': None,
  'uri': None,
  'vartype': 'datetime'},


 {'children': [],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Objective stigmator deflectors',
  'desc_short': 'Objective stigmator deflectors',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'objective_stigmator_deflectors',
  'parents': [],
  'property': 'count',
  'uri': None,
  'vartype': 'int'},


 {'children': ['title_demonstration',
                'localperson',
                'microscope',
                'visitors',
                'description_goals',
                'name_contact',
                'demonstrator',
                'address_email',
                'phone_voice',
                'comments_text',
                'name_project'],
  'choices': None,
  'controlhint': None,
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'defaultunits': None,
  'desc_long': 'Microscope parameters (remove)',
  'desc_short': 'Microscope parameters (remove)',
  'immutable': None,
  'indexed': True,
  'iter': False,
  'keytype': 'paramdef',
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'microscope_demo',
  'parents': ['equipment', 'descriptive_information'],
  'property': None,
  'uri': None,
  'vartype': 'string'}
]



recorddefs = [


 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A maintenance event on the microscope. Any time there is change to the microscope or maintenance performed, this record should be used. If the microscope is altered in a way that affects imaging parameters, a new microscope record should be created.',
  'desc_short': 'Microscope maintenance',
  'keytype': 'recorddef',
  'mainview': """
# Microscope maintenance
$#performed_by: $$performed_by
$#date_occurred: $$date_occurred

# Service performed
$#service_engineer:  $$service_engineer  
$#service_date:  $$service_date   
(if different than the date occurred above)  
$#service_type:  $$service_type  
$#service_description:  $$service_description  

# Attachments
$$file_binary  
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'microscope_maintenance',
  'owner': 'root',
  'parents': ['equipment_maintenance'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': {'recname': """Maintenance: $$service_type on $$date_occurred"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A manuscript in preparation',
  'desc_short': 'Manuscript',
  'keytype': 'recorddef',
  'mainview': """
# Manuscript in preparation  
$#title_publication: $$title_publication  

# Comments about this manuscript
$$comments

# Attachments  
$$file_binary  
    """,
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'manuscript',
  'owner': 'root',
  'parents': ['information'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': {'recname': """Manuscript: $$title_publication"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'Manual plunger session',
  'desc_short': 'Manual plunger session',
  'keytype': 'recorddef',
  'mainview': """
# Manual plunger freezing session
$#date_occurred: $$date_occurred  
$#performed_by: $$performed_by  
$#frozen_by: $$frozen_by  
$#vitrification_device: $$vitrification_device  
$#title_freezing: $$title_freezing  

# Grids
$$grid_tem_type grids will be used for this freezing session.  

The grids should have a $$select_substrate_grid that was prepared by: $$select_substrate_grid_prep  

Obtain the $$grids_tem_good grid(s) from grid batch $$id_grid_batch.  

Each grid has a mesh size of $$grid_tem_mesh_size with a hole size of $$grid_tem_hole_size  

Check the quality of each grid with a light microscope. Discard any grids that do not meet the experiment's standards.  
    $#grids_tem_lost = $$grids_tem_lost  
    $#grids_tem_used = $$grids_tem_used  

$#description_grid_prefreezing: $$description_grid_prefreezing  

For glow discharge, the discharge time is $$time_glowdischarge  

# Freezing
$#grid_volume_applied: $$grid_volume_applied  

# Plunger settings
$#vitrobot_temp: $$vitrobot_temp    

$#vitrobot_time_blot: $$vitrobot_time_blot   

$#vitrobot_blots: $$vitrobot_blots  

$#direction_blotting:  $$direction_blotting   

$#vitrobot_humid_on: $$vitrobot_humid_on  

Note: If the humidifier is on, then also set  
$#vitrobot_humidity to $$vitrobot_humidity  

# After Freezing
$#description_grid_postfreezing: $$description_grid_postfreezing  

$#select_technique_freezing: $$select_technique_freezing  

$#description_storage: $$description_storage  
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'freezing_manual',
  'owner': 'root',
  'parents': ['freezing'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Freezing session: $$title_freezing using $$vitrification_device by $$performed_by on $$date_occurred"""}},




 {'children': ['tem', 'purification'],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': None,
  'desc_short': 'Experiments',
  'keytype': 'recorddef',
  'mainview': """This protocol is for organizational purposes, and is not intended to be used.""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'experiments',
  'owner': 'root',
  'parents': ['root'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
	  'views': {}},




 {'children': ['vitrobot_maintenance',
                'scanner_maintenance',
                'microscope_maintenance',
                'camera_maintenance'],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'Maintenance record for a piece of equipment',
  'desc_short': 'Equipment Maintenance',
  'keytype': 'recorddef',
  'mainview': """
# Equipment maintenance
$#performed_by: $$performed_by
$#date_occurred: $$date_occurred

# Service performed
$#service_engineer:  $$service_engineer  
$#service_date:  $$service_date  
(if different than the date occurred above)  
$#service_type:  $$service_type  
$#service_description:  $$service_description  

# Attachments
$$file_binary
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'equipment_maintenance',
  'owner': 'root',
  'parents': ['equipment'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': {'recname': """Equipment maintenance: $$service_type on $$date_occurred"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A meeting about a project. Enter the details of the meeting, e.g. agenda, minutes, and any relevant attachments.',
  'desc_short': 'Project meeting',
  'keytype': 'recorddef',
  'mainview': """
# Project meeting  
$#subject_notebook: $$subject_notebook   
$#date_occurred: $$date_occurred   
Attending: $$author_list   

# Meeting notes  
$$description_notebook   

# Attachments  
$$file_binary  
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'project_meeting',
  'owner': 'root',
  'parents': ['information', 'project'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Project meeting: $$subject_notebook with $$author_list on $$date_occurred"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'Bookmarks. This is used by the system and should not be created directly.',
  'desc_short': 'Bookmarks',
  'keytype': 'recorddef',
  'mainview': """
# Bookmarked records
$$bookmarks
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'bookmarks',
  'owner': 'root',
  'parents': [],
  'private': False,
  'typicalchld': [],
  'uri': None,
  'views': {'recname': """Bookmarks"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'Microscope alignment',
  'desc_short': 'Microscope alignment',
  'keytype': 'recorddef',
  'mainview': """
# Microscope alignment
$#performed_by: $$performed_by  
$#date_occurred: $$date_occurred  

Note: this protocol is in the process of being updated.

# Inserting the Specimen Holder
Blank the electron gun.  

Inspect the specimen holder to ensure that the O-rings are dust-free, lubricated, and free of cracks / done in "loading grid on holder" (procedure associated with cryoholder).  

Remove the goniometer's protective cap.   

Grab cryoholder (that was already prepared with a grid on it) while it\'s in its holder.  

Disconnect the temperature reader if connected.  

Remove the cryoholder from its holder and quickly move it to the inside of the scope.  

Align the specimen holder\'s guide pin with the goniometer\'s groove guide and insert the holder straight in until resistance is felt.  

Using the toggle switch under the goniometer, switch to "PUMP".  At this point the orange light above the toggle switch will light up.  

Wait for the orange light to disengage and the green light adjacent to it to engage.  

Turn the specimen holder about 30 degrees counter-clockwise and push the holder in further.  

Turn the specimen holder about 60 degrees counter-clockwise and push the holder in completely.  The liquid nitrogen in the heat-sink container of the specimen holder will likely spill out at this point - this is unavoidable.  

Turn the specimen holder 90 degrees clockwise so that the heat sink is again vertical.  

Switch the toggle switch under the goniometer to "AIR".  

Refill the holder\'s heat-sink with liquid nitrogen.  

Evaporate off the liquid nitrogen so that the level of nitrogen is below the rod in the heat-sink.  

Wait approximately 45 minutes for the stage to stablize.  

# Adjust the Z-height (procedure might vary based on the 'scope).
Unlock the trackball by clicking "Close" (if using FastEM) and make sure that MDS is set to "OFF".  

Use the focus knob to set DV = 0.  

Press "Valve" to open the gun valve.  

Use the trackball to find an open area on the grid.  

Set the imaging magnification to the desired level.  

Press "Wobbler X".  

Rotate the joystick to adjust the z-height.  When properly adjusted, the image should not move.  

Disengage wobbler by pressing "Wobbler X" again.  

Use the X Y shift knobs to center the beam.  

# Aligning the Condenser Aperture
Insert the condenser aperture.  

Spread the beam to cover the outer echelons.  

Center the aperture using the aperture knobs  

# Aligning the FEG
Set the magnification to at least some minimum value, set the spot size to 1, and condense the beam.  

Set the spot size to the smallest setting and center the beam with "Shift XY".  

Set the spot size to the largest setting and center with Gun Shift.  

Repeat the last 2 steps until all spot sizes are centered and beam expansion is symmetrical.  

# Centering the High Voltage
Begin viewing the grid at low magnification.  

Find a noticeable feature on the grid that images will not be collected from.  

Press "Wobbler HT" followed by "Bright tilt".  

Use the "Def XY" knobs to align the current feature of interest.  If the microscope is aligned properly, then this feature should not drift or move.  

Disengage "Wobbler HT" and "Bright tilt".  

Increase the magnification and repeat this procedure until (param needed) magnification magnification is reached.  

# Centering the Objective Aperture
Spread the beam to cover the outer echelons. At this point the microscope magnification should set to (param needed) magnification.  

Press "Diff" and condense the beam with "Diff Focus".  

Set the objective aperture to (param needed) objective_aperture.  

Press "Proj" and use "Shift XY" to center the beam.  

Turn the "Diff Focus" knob counter-clockwise until the edge of the circular aperture is in sharp focus.  

Use the objective arrows to center the objective aperture's shadow.  

Press "Mag 1".

# Correcting Objective Astigmatism  
Locate carbon (grids always carbon?).  

Set the magnification to 400K.  

Press "MSC".  

Using Digitalreconstruction_o, insert the CCD camera (click Camera -> Insert Camera).  

Verify the CCD's setting, then acquire a live image in Focus Mode.  

Create a Fourier transform of the image (Process -> Live -> FFT).  

Use the "Mag/Diff" knob to alter the FFT such that there is only one ring when the microscope is underfocused.  If the ring diameter decreases ... (what is this saying?) ...    " focus so there is only one ring when underfocused. Use the FFT rings to determine if it is under or over focused. When defocusing at underfocused level, the ring diameter decreases".  

Press "Stig" and use "Alignment XY" to adjust the astigmatism; the rings of the FFT should become circular.  

Use the FFT to check for drift / specimen holder stability.  Look at the FFT, if all of the rings are complete then the specimen is stable.  Incomplete rings indicate drift and/or specimen holder instability.  

Stop acquiring CCD images by clicking on the image and pressing "space".  

Retract the camera.  

# Setup Parallel Beam Condition

# Setting the MDS
Set the spot size to (param needed) spot_size and spread the beam to obtain an electron dose of (param needed) dose. Check software or a chart to determine the appropriate dosage.  

Go to the "MDS" tab and click "Set".  

Center the beam with "XY Shift" and recheck that the electron dose is (param needed) dose.  

Click "Search2" under the "MDS" tab.  

Set the spot size to 5 and spread the beam completely.  

Press "Diff" and set the camera length to (param needed) camera_length.  

Use the "Diff Focus" knob to overfocus the image to a level that is appropriate for visualizing and evaluating the specimen\'s ice.  

Go to the "dPhoto" tab and make sure the Photo and Search modes are aligned.  If not aligned then press "Project" on the keyboard and use "Shift XY" to align the modes.  

Go to the "MDS" tab and click on "Focus".  

Burn a hole in the ice in order to see the deflection of the beam.  

Use the "Def XY" knobs to deflect the beam to the correct position for focusing.  

Go through the MDS cycle and make sure all of the modes are correcting.  

# Notes
The Z-height must be aligned when moving to distant areas or when moving to different grid squares.  
(How about instructions on moving to different grid locations??).  
(After astigmatism correction, when do you return the magnification to (param needed) magnification ??).  
Before taking images, wait for the specimen's temperature to reach (param needed) temperature_specimen.  
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'alignment',
  'owner': 'root',
  'parents': ['tem'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Microscope alignment by $$performed_by on $$date_occurred""" }},



 {'children': ['cryoholder_loading',
                'freezing',
                'microscopy',
                'image_capture',
                'grid_preparation',
                'grid_imaging',
                'stack',
                'alignment'],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': None,
  'desc_short': 'Transmission Electron Microscopy protocols',
  'keytype': 'recorddef',
  'mainview': """This protocol is for organizational purposes, and is not intended to be used.""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'tem',
  'owner': 'root',
  'parents': ['experiments'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': {}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': '(Deprecated) Use movie.',
  'desc_short': '(Deprecated) Use movie.',
  'keytype': 'recorddef',
  'mainview': """
# Visualization

Deprecated; use movie.
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'visualization',
  'owner': 'root',
  'parents': [],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': {}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A laboratory group',
  'desc_short': 'Lab group',
  'keytype': 'recorddef',
  'mainview': """
# $#name_group: $$name_group  
$#institution: $$institution    

# Contact info
$#name_contact: $$name_contact  
$#phone_voice: $$phone_voice  
$#phone_fax: $$phone_fax  
$#phone_voice_international: $$phone_voice_international  
$#phone_fax_international: $$phone_fax_international   
$#website: $$website  
$#address_email: $$address_email     

# Address
$#address_street: $$address_street  
$#address_city: $$address_city  
$#address_state: $$address_state  
$#address_zipcode: $$address_zipcode  
$#address_international: $$address_international  
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'group',
  'owner': 'root',
  'parents': ['core', 'people'],
  'private': 0,
  'typicalchld': ['project', 'equipment', 'workshop'],
  'uri': None,
  'views': { 'recname': """$$name_group""",
             'tabularview': """$$name_group $$institution $$name_contact $$address_email"""}},




 {'children': ['publication_abstract', 'publication_book'],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A publication that results from the project. To add references of interest that were not produced by this group, the "reference" protocol may be more appropriate.',
  'desc_short': 'Publication',
  'keytype': 'recorddef',
  'mainview': """
# $#title_publication:  $$title_publication
$#pmid:     $$pmid  
$#pmcid:  $$pmcid  

Note: a PubMed ID or PMCID is sufficient to describe the publication.

# Publication Information  
$#author_corresponding: $$author_corresponding  
$#corresponding_author_contact: $$corresponding_author_contact  

$#author_list: $$author_list  

$#name_journal: $$name_journal  
$#journal_volume: $$journal_volume  
$#journal_date: $$journal_date  
$#page_range: $$page_range  
$#publication_in_press: $$publication_in_press  

# Abstract
$$abstract
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'publication',
  'owner': 'root',
  'parents': ['information'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Article: $$title_publication by $$author_corresponding""",
             'tabularview': """$$title_publication $$author_first $$author_list $$journal_date $$name_journal $$pmid $$pmcid"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'This is a project specifically for software development rather than a biological target.',
  'desc_short': 'Software project',
  'keytype': 'recorddef',
  'mainview': """
# Software project: $$name_project

<div style="border:solid 1px #ccc;padding:10px;margin:10px;margin-left:0px;width:400px">

$#project_status: $$project_status  

$#project_block: $$project_block  

<span class="e2-button e2-record-new" data-rectype="progress_report" data-parent="$$name">New progress report</span>  

<span class="e2-button e2-record-new" data-rectype="labnotebook" data-parent="$$name">New lab notebook</span>  

</div>

# Important note
Please use nested projects going forward, instead of subprojects. This applies to specific project types as well, e.g. software_project.

$#name_pi: $$name_pi  
$#project_investigators: $$project_investigators  

# Project Description

$#project_type: $$project_type  
$#description_goals: $$description_goals  
$#description_background: $$description_background
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'subproject_software',
  'owner': 'root',
  'parents': ['project_software'],
  'private': 0,
  'typicalchld': ['progress_report'],
  'uri': None,
  'views': { 'recname': """Software project: $$name_project""",
             'tabularview': """$$name_project $$name_pi $$project_type $$project_status $$project_block"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'This record represents a single scan of a micrograph. There may be more than one scan record per micrograph.',
  'desc_short': 'Scanned micrograph',
  'keytype': 'recorddef',
  'mainview': """
# Scanned micrograph
$#date_occurred: $$date_occurred  
$#performed_by: $$performed_by  
$#scanned_by (deprecated): $$scanned_by  

# Images
$$file_binary_image

# Scanner
$#scanner_film: $$scanner_film  
$#scanner_cartridge: $$scanner_cartridge  
$#scan_average: $$scan_average  

# Resolution and step size
$#scan_step: $$scan_step  
$#angstroms_per_pixel: $$angstroms_per_pixel  

# Nikon specific
$#nikon_gain: $$nikon_gain  

# Zeiss specific
$#zeiss_contrast: $$zeiss_contrast   
$#zeiss_exposure: $$zeiss_exposure  
$#zeiss_brightness: $$zeiss_brightness  
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'scan',
  'owner': 'root',
  'parents': ['image_capture'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Micrograph scan using $$scanner_film by $$performed_by""",
             'tabularview': """$$scanner_film $$scan_average $$scanner_cartridge $$file_binary_image $$scanned_by"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'Maintenance record for a camera.',
  'desc_short': 'Camera maintenance',
  'keytype': 'recorddef',
  'mainview': """
# Camera maintenance
$#performed_by: $$performed_by
$#date_occurred: $$date_occurred

# Service performed
$#service_engineer:  $$service_engineer  
$#service_date:  $$service_date   
(if different than the date occurred above)  
$#service_type:  $$service_type  
$#service_description:  $$service_description  

# Attachments
$$file_binary
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'camera_maintenance',
  'owner': 'root',
  'parents': ['equipment_maintenance'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Camera maintenance: $$service_type on $$date_occurred"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A camera or other imaging instrument.',
  'desc_short': 'Camera',
  'keytype': 'recorddef',
  'mainview': """
# Camera
$#ccd_id: $$ccd_id

# Comments about this camera
$$comments

# Attachments (e.g. manuals)
$$file_binary
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'camera',
  'owner': 'root',
  'parents': ['equipment'],
  'private': 0,
  'typicalchld': ['camera_maintenance'],
  'uri': None,
  'views': { 'recname': """Camera $$ccd_id"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A folder, which is useful as a general purpose organization device.',
  'desc_short': 'Folder',
  'keytype': 'recorddef',
  'mainview': """
# Folder: $$name_folder

Description: $$folder_description  

""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'folder',
  'owner': 'root',
  'parents': ['core', 'information'],
  'private': False,
  'typicalchld': [],
  'uri': 'http://ncmidb.bcm.edu',
  'views': { 'banner': '$$folder_description $@renderchildren()',
             'recname': """$$name_folder""",
             'tabularview': """$$name_folder"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A presentation given, e.g. at a workshop or lab meeting. For talks given at conferences, the "publication_abstract" protocol may be more appropriate.',
  'desc_short': 'Presentation',
  'keytype': 'recorddef',
  'mainview': """
# Presentation
$#subject_notebook: $$subject_notebook  
$#date_occurred: $$date_occurred  
Authors: $$author_list  

# Notes
$$description_notebook  

# Attachments
$$file_binary
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'presentation',
  'owner': 'root',
  'parents': ['labnotebook'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Presentation: $$subject_notebook by $$author_list""",
             'tabularview': """$$subject_notebook $$file_binary $$author_list"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'This protocol is for storing common forms and templates. Please describe the form, the purpose of the form, any special instructions for submission, and who receives completed forms. You may attach the forms directly, e.g. as PDF, or provide a link where the form may be downloaded.',
  'desc_short': 'Form',
  'keytype': 'recorddef',
  'mainview': """
# Form Name: $$name_folder
Form Description: $$folder_description  
Submit to: $$name_contact  

# Attachments and References
$$file_binary  
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'form',
  'owner': 'root',
  'parents': ['information'],
  'private': False,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Form: $$name_folder""",
             'tabularview': """$$name_folder"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'An aliquot from a purification sample. Parent should be the purification record, children will usually be grid_preparation or freezing sessions.',
  'desc_short': 'Aliquot',
  'keytype': 'recorddef',
  'mainview': """
# Aliquot
$#performed_by: $$performed_by  
$#date_occurred: $$date_occurred

# Aliquot ID and contents
$#id_aliquot:  $$id_aliquot  
$#description_aliquot:  $$description_aliquot 

# Tracking and sample source
$#provided_by: $$provided_by  
$#name_receiver: $$name_receiver  
$#date_occurred: $$date_occurred  
$#date_received: $$date_received  

# Preparation
Dilute the sample in buffer: $$description_buffer_purification  
Final sample concentration: $$concentration_solution

Place $$volume_aliquot of the diluted sample into $$aliquot_count storage vessels

Store the vessels under the following conditions:
$$aliquot_storage
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'aliquot',
  'owner': 'root',
  'parents': ['purification'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Aliquot: $$id_aliquot received by $$name_receiver on $$date_received""",
             'tabularview': """$$name_receiver $$date_received $$aliquot_count $$volume_aliquot $$concentration_solution $$id_aliquot $$description_aliquot"""}},




 {'children': ['freezing_vitrobot',
                'freezing_gatanmkii',
                'freezing_high_pressure',
                'freezing_manual',
                'freezing_gatancp3',
                'freezing_pneumatic',
                'freezing_berriman'],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': None,
  'desc_short': 'Freezing protocols',
  'keytype': 'recorddef',
  'mainview': """This protocol is for organizational purposes, and is not intended to be used.""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'freezing',
  'owner': 'root',
  'parents': ['tem'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': {}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': """A density map. For a finished reconstruction, you may want to use 'structure' protocol.""",
  'desc_short': 'Density map',
  'keytype': 'recorddef',
  'mainview': """
# $#title_structure: $$title_structure   
The structure was completed: 
$#performed_by: $$performed_by  
$#date_occurred: $$date_occurred  

# Comments about this density map
$$comments

# Attachments
$$file_binary   
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'volume',
  'owner': 'root',
  'parents': ['information'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Density map: $$title_structure""",
             'tabularview': """$$title_structure $$file_binary"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A session on the microscope. The start and end times are important for usage accounting. Each grid used in this microscopy session should have a grid_imaging record. Parent record should be the current microscope configuration.',
  'desc_short': 'JEOL 2010F microscope session',
  'keytype': 'recorddef',
  'mainview': """Under construction""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'microscopy_2010',
  'owner': 'root',
  'parents': ['microscopy'],
  'private': 0,
  'typicalchld': ['grid_imaging'],
  'uri': None,
  'views': { 'recname': """JEOL 2010F microscopy session""" }},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': '(Deprecated) All groups',
  'desc_short': '(Deprecated) All groups',
  'keytype': 'recorddef',
  'mainview': """
# All groups

Deprecated. Use the 'group' protocol.
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'all_groups',
  'owner': 'root',
  'parents': [],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': {}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': '(Deprecated) Project meeting or discussion',
  'desc_short': '(Deprecated) Project meeting or discussion',
  'keytype': 'recorddef',
  'mainview': """
# Project meeting

Deprecated; use project_meeting
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'project_discussion',
  'owner': 'root',
  'parents': [],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': {}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': None,
  'desc_short': "Places",
  'keytype': 'recorddef',
  'mainview': """This protocol is for organizational purposes, and is not intended to be used.""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'places',
  'owner': 'root',
  'parents': ['root'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': {}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': '(Deprecated) Meeting',
  'desc_short': '(Deprecated) Meeting',
  'keytype': 'recorddef',
  'mainview': """
# Meeting

Deprecated; use publication_abstract.
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'meeting',
  'owner': 'root',
  'parents': [],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': {}},




 {'children': ['tomography',
                'microscopy_2010',
                'virus',
                'single_particle'],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A session on the microscope. The start and end times are important for usage accounting. Each grid used in this microscopy session should have a grid_imaging record. Parent record should be the current microscope configuration.\n\nNote: microscopy sessions are usually created using EMDash, which manages all the other associated records and relationships, as well as logging the start and end time of the session.',
  'desc_short': 'Microscopy session',
  'keytype': 'recorddef',
  'mainview': """
# Objective  
$#performed_by: $$performed_by  
$#date_start: $$date_start  
$#date_end: $$date_end  

# Session purpose
$#type_session: $$type_session  
$#description_purpose: $$description_purpose  
$#film_type: $$film_type  

# Initial Microscope Status Check:
1. Record the ambient humidity: $$humidity_ambient  
2. Ensure the column vacuum pressure is at an acceptable level (i.e., less than 2x10^-5 Pa)  
3. The CCD camera should be retracted and its temperature should be less than -23 C  
4. The input cooling water temperature should be less than (param needed) C with a differential pressure of (param needed) Pa  

# Setting up the microscope:
1. Fill the anti-contamination device with liquid nitrogen.  It will take approximately 45 minutes for the device to cool.  In the meantime...  
2. Verify that the specimen position is (0,0,0)  
3. Set the microscope's target voltage: $$lens_voltage_objective  
4. Set the total time and the step voltage (typically the total time is set between 30 and 60 minutes with the step voltage scaled appropriately)  
5. Bring up the HT (high tension)  

# Insert the specimen into the microscope:
1. Obtain a grid from the parent freezing session to use for imaging and load it on the specimen holder  
2. Load the specimen in the microscope; see the microscope manual for detailed instructions  
3. The specimen's temperature: $$temperature_specimen  (in Kelvin).
4. Adjust the Z-height for the microscope  

# Alignment:
$#aperture_condenser: $$aperture_condenser   
$#aperture_objective: $$aperture_objective  
$#tem_spot_size: $$tem_spot_size   
$#length_camera: $$length_camera   

Use the alignment protocol for the particular microscope to:  

1. Align the Electron Gun  
2. Center the Objective Aperture  
3. Correct the Objective Astigmatism  
4. Set up a Parallel Beam Condition  

# Collect gain reference and calculate dose
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'microscopy',
  'owner': 'root',
  'parents': ['tem'],
  'private': 0,
  'typicalchld': ['grid_imaging'],
  'uri': None,
  'views': { 'recname': """Microscopy: $@parentvalue(tem_name) by $$performed_by on $$date_start: $$description_purpose""",
             'tabularview': """$@parentvalue(tem_name) $$aperture_condenser $$tem_spot_size $$aperture_objective $$tem_lowdose_method $$assess_ice_thick $@childcount(grid_imaging) $@childcount(ccd) $@childcount(micrograph)"""}},




 {'children': ['workshop',
                'p41_project',
                'subproject',
                'project_software'],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A project. This should be used in a broad sense, such as an entire collaboration. For each specific goal, an additional child project should be created. Parent will usually be a group record.',
  'desc_short': 'Project',
  'keytype': 'recorddef',
  'mainview': """
# $#name_project: $$name_project

<div style="border:solid 1px #ccc;padding:10px;margin:10px;margin-left:0px;width:400px">

$#project_status: $$project_status  

$#project_block: $$project_block  

<span class="e2-button e2-record-new" data-rectype="progress_report" data-parent="$$name">New progress report</span>   <br />

<span class="e2-button e2-record-new" data-rectype="labnotebook" data-parent="$$name">New lab notebook entry</span>  

</div>

$#name_pi: $$name_pi  
$#project_investigators: $$project_investigators  

$#project_type: $$project_type  

# Specimen
$#name_specimen: $$name_specimen  
$#symmetry_particle: $$symmetry_particle  
$#mass_specimen: $$mass_specimen  
$#diameter_max: $$diameter_max   
$#diameter_min:    $$diameter_min  
$#hazard_bl_max: $$hazard_bl_max   

# Project Description
$#description_goals:  $$description_goals  
$#description_medical_relevance:  $$description_medical_relevance  
$#description_background: $$description_background  

# Associated sequence data
$#description_genetic: $$description_genetic  
(Or, for single components):  
$#sequence_dna: $$sequence_dna   
$#sequence_rna: $$sequence_rna  
$#sequence_protein: $$sequence_protein  
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'project',
  'owner': 'root',
  'parents': ['information'],
  'private': 0,
  'typicalchld': [ 'project',
                   'labnotebook',
                   'grid_imaging',
                   'publication',
                   'publication_abstract',
                   'purification',
                   'movie',
                   'volume',
                   'project_meeting',
                   'reference',
                   'manuscript',
                   'progress_report'],
  'uri': None,
  'views': { 'recname': """Project: $$name_project ($$name_pi)""",
             'tabularview': """$$name_project $$name_specimen $$name_pi $$project_type $$project_status $$project_block $@childcount(publication*)"""}},



 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'Cryo-sectioned grid',
  'desc_short': 'Cryo-sectioned grid',
  'keytype': 'recorddef',
  'mainview': """
# Cryo-sectioned grid
$#performed_by: $$performed_by  
$#date_occurred: $$date_occurred

Note: this protocol is under development.

# Grid details
$#title_grid: $$title_grid
$#id_grid_batch: $$id_grid_batch  
$#grid_tem_type: $$grid_tem_type  
$#grid_tem_mesh_size: $$grid_tem_mesh_size

# Grid Preparation

Get a grid from $$description_storage (which canister) canister and fill it with liquid nitrogen.

Add a loading stick into the canister to cool as well.

Add a grid holder and a spider into the vitrobot's black rubber holder outside of the inner copper circle. Fill the rubber holder with liquid nitrogen.

The grids should have a $$select_substrate_grid that was prepared by the following procedure:
$$select_substrate_grid_prep 

Check the quality of each grid with a light microscope. Discard any grids that do not meet the experiment's standards.
$#grids_tem_lost: $$grids_tem_lost  

$#grids_tem_used: $$grids_tem_used  

# Grid Pre-Treatment
$#description_grid_prefreezing: $$description_grid_prefreezing  

If Glow Discharged,
$#time_glowdischarge: $$time_glowdischarge 

# Freezing or Staining

For a frozen-hydrated grid, please make sure a freezing session is linked as a parent. This will allow you to specify the full set of Vitrobot or freezing parameters.

If this particular grid deviates from the parent freezing session, you can override some of the freezing parameters below:

$#vitrobot_temp: $$vitrobot_temp   
$#vitrobot_time_blot: $$vitrobot_time_blot   
$#vitrobot_blots: $$vitrobot_blots  
$#vitrobot_blot_offset:  $$vitrobot_blot_offset   
$#vitrobot_time_wait: $$vitrobot_time_wait   
$#vitrobot_time_step: $$vitrobot_time_step   
$#vitrobot_time_drain: $$vitrobot_time_drain  
$#vitrobot_level_liquid: $$vitrobot_level_liquid   
$#direction_blotting:  $$direction_blotting  
$#vitrobot_humid_on: $$vitrobot_humid_on  
Note: If the vitrobot's humidifier is on, then also set  
$#vitrobot_humidity to $$vitrobot_humidity  

# Post-freezing

$#description_grid_postfreezing:
$$description_grid_postfreezing 

$#description_storage:
$$description_storage""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'grid_cryosection',
  'owner': 'root',
  'parents': ['grid_preparation'],
  'private': False,
  'typicalchld': ['grid_imaging'],
  'uri': None,
  'views': { 'recname': """Cryo-sectioned grid: $$title_grid by $$performed_by on $$date_occurred""",
             'tabularview': """$$title_grid $$vitrobot_time_step $$vitrobot_time_blot $$vitrobot_blots $$vitrobot_blot_offset $$vitrobot_humid_on $$vitrobot_time_wait $$vitrobot_time_drain $$vitrobot_level_liquid"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A microscope. Whenever a major change is made to a microscope, a new microscope record should be created. Parent should be a folder containing configurations of that microscope.',
  'desc_short': 'Microscope',
  'keytype': 'recorddef',
  'mainview': """
# $#tem_name: $$tem_name   
$#microscope_serialno: $$microscope_serialno   
$#lens_voltage_objective: $$lens_voltage_objective  

# Start and end date for this configuration  
$#date_start:  $$date_start  
$#date_end: $$date_end  

$#tem_polepiece: $$tem_polepiece  
$#aberration_chromatic: $$aberration_chromatic   
$#aberration_spherical: $$aberration_spherical  

# Cameras  
$#ccd_screen_ratio: $$ccd_screen_ratio  
$#dose_rate_scaling_factor: $$dose_rate_scaling_factor   
$#film_screen_ratio: $$film_screen_ratio

# Comments about this microscope
$$comments

# Attachments (e.g. manuals)
$$file_binary
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'microscope',
  'owner': 'root',
  'parents': ['equipment'],
  'private': 0,
  'typicalchld': [ 'alignment',
                   'microscope_maintenance',
                   'microscopy'],
  'uri': None,
  'views': { 'recname': """$$tem_name""",
             'tabularview': """$$tem_name $$lens_voltage_objective $$date_start $$date_end $$aberration_spherical $$aberration_chromatic $$dose_rate_scaling_factor $$ccd_screen_ratio $$film_screen_ratio"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'Gatan CP3 session',
  'desc_short': 'Gatan CP3 session',
  'keytype': 'recorddef',
  'mainview': """
# Gatan CP3 Session
$#date_occurred: $$date_occurred  
$#performed_by: $$performed_by  

$#frozen_by: $$frozen_by  
$#vitrification_device: $$vitrification_device  
$#title_freezing: $$title_freezing  

# Grids

Use $$grid_tem_type grids for this freezing session

The grids should have a $$select_substrate_grid substrate that was prepared by doing the following: $$select_substrate_grid_prep

Obtain $$grids_tem_good grids from grid batch $$id_grid_batch

Grids have a mesh size of $$grid_tem_mesh_size with a hole size of $$grid_tem_hole_size  

Check the quality of each grid with a light microscope. Discard any grids that do not meet the experiment's standards  
    $#grids_tem_lost: $$grids_tem_lost  
    $#grids_tem_used: $$grids_tem_used  


$#description_grid_prefreezing: $$description_grid_prefreezing  

For glow discharge, the discharge time is $$time_glowdischarge  

# Freezing

(Ian: under construction)

$#grid_volume_applied: $$grid_volume_applied  

# Plunger settings

$#vitrobot_temp: $$vitrobot_temp    
$#vitrobot_time_blot: $$vitrobot_time_blot   
$#vitrobot_blots: $$vitrobot_blots  
$#direction_blotting:  $$direction_blotting   

$#vitrobot_humid_on: $$vitrobot_humid_on  
Note: If the humidifier is on, then also set  
$#vitrobot_humidity to $$vitrobot_humidity  

# After Freezing

$#description_grid_postfreezing: $$description_grid_postfreezing

$#select_technique_freezing: $$select_technique_freezing

$#description_storage: $$description_storage

""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'freezing_gatancp3',
  'owner': 'root',
  'parents': ['freezing'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Freezing: $$title_freezing by $$performed_by on $$date_occurred"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'Cryo-holder loading',
  'desc_short': 'Cryo-holder loading',
  'keytype': 'recorddef',
  'mainview': """
# Cryo-holder loading

Note: currently being reworked

# Specimen Holder Precheck
Locate the $$specimen_holder specimen holder  

Inspect the tip of the holder; ensure that the stage is clean, not coated with residue, and that an old grid is not loaded  

Verify that the holder's rubber O-rings are dust-free, lubricated, and free of cracks  

# Preparing the Specimen Holder
Place the specimen holder in its own appropriate holder  

Attach the temperature sensor to the cryoholder  

Note that there are two ends to the holder.  The end where the grid will eventually be added will be referred to as the open-end, while the other end will be called the heat-sink end.  

Fill the open-end of the holder with liquid nitrogen  

Continue refilling with liquid nitrogen until the entire stage section is submerged  

Fill the heat-sink end of the holder with liquid nitrogen as well  

Submerge the end of a specimen holder loading stick in the liquid nitrogen in the holder's open-end.  

Wait approximately 10 minutes for the holder to cool down.  Refill liquid nitrogen as needed.  

The temperature should be no higher than -160 degrees C  

# Loading the Grid
Obtain the grid that will be used for imaging  

Remove the grid (and its transfer stick) from its storage container and place it in the specimen holder's holder's open end.   

Unscrew the grid from its transfer stick - make sure the grid remains submerged in the liquid nitrogen during this process.  

Wait approximately 5 minutes.

Now, attach the grid to the specimen holder loading stick by pressing the stick on the grid and turning it clockwise  

Keeping the end of the loading stick submerged, move the grid to the tip of the specimen holder and release it (turn the stick counter-clockwise)  

Now use the end of the loading stick to press the grid down on the tip until there is an audible click  
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'cryoholder_loading',
  'owner': 'root',
  'parents': ['tem'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Cryo-holder loading by $$performed_by on $$date_occcurred"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A vitrification device; e.g. a vitrobot, Gatan plunger, etc.',
  'desc_short': 'Vitrification device',
  'keytype': 'recorddef',
  'mainview': """
# Vitrification device

Note: being reworked

# Comments about this vitrification device
$$comments

# Attachments (e.g. manuals)
$$file_binary
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'vitrification_device',
  'owner': 'root',
  'parents': ['equipment'],
  'private': 0,
  'typicalchld': ['vitrobot_maintenance'],
  'uri': None,
  'views': { 'recname': """Vitrification device"""}},




 {'children': ['core',
                'places',
                'people',
                'processing',
                'equipment',
                'experiments',
                'information'],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'Root protocol. Do not use.',
  'desc_short': 'Root Protocol',
  'keytype': 'recorddef',
  'mainview': """Root Protocol""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'root',
  'owner': 'root',
  'parents': [],
  'private': False,
  'typicalchld': [],
  'uri': 'http://ncmidb.bcm.edu',
  'views': {}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'Berriman freezing session',
  'desc_short': 'Berriman freezing session',
  'keytype': 'recorddef',
  'mainview': """
# Berriman freezing session

Note: this is under development.
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'freezing_berriman',
  'owner': 'root',
  'parents': ['freezing'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Berriman freezing session"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'Maintenance record for a vitrification device',
  'desc_short': 'Vitrobot maintenance',
  'keytype': 'recorddef',
  'mainview': """
# Vitrobot maintenance
$#performed_by: $$performed_by
$#date_occurred: $$date_occurred

# Service performed
$#service_engineer:  $$service_engineer  
$#service_date:  $$service_date   
(if different than the date occurred above)  
$#service_type:  $$service_type  
$#service_description:  $$service_description  

# Attachments
$$file_binary
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'vitrobot_maintenance',
  'owner': 'root',
  'parents': ['equipment_maintenance'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Maintenance: $$service_type on $$date_occurred"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'P41 annual grant report',
  'desc_short': 'P41 annual grant report',
  'keytype': 'recorddef',
  'mainview': """
# Annual P41 Grant Report

This record describes the summary information for an NCRR P41 annual progress report.

$#p41_title:  $$p41_title  
$#p41_serial:  $$p41_serial  
$#p41_year:  $$p41_year  
$#p41_report_start_date:  $$p41_report_start_date  
$#p41_report_end_date:  $$p41_report_end_date  
$#institution:  $$institution  
$#grant_pi: $$grant_pi  
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'p41_grant_info',
  'owner': 'root',
  'parents': ['information'],
  'private': 0,
  'typicalchld': ['p41_project'],
  'uri': None,
  'views': { 'recname': """P41 APR - $$p41_year""",
             'tabularview': """$$p41_year $$p41_title $$p41_report_start_date"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A film scanner.',
  'desc_short': 'Film scanner',
  'keytype': 'recorddef',
  'mainview': """
# Film scanner
$#scanner_film: $$scanner_film

# Comments about this scanner
$$comments

# Attachments (e.g. manuals)
$$file_binary
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'scanner',
  'owner': 'root',
  'parents': ['equipment'],
  'private': 0,
  'typicalchld': ['scanner_maintenance'],
  'uri': None,
  'views': {'recname': """Scanner: $$scanner_film"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A reference to a publication of interest to the project. For articles that your group has published, use the "publication" protocol. You may want to attach a PDF of the paper. Parent should be a project.',
  'desc_short': 'Reference',
  'keytype': 'recorddef',
  'mainview': """
# $#title_publication:  $$title_publication
$#pmid:     $$pmid  
$#pmcid:  $$pmcid  

Note: a PubMed ID or PMCID is sufficient to describe the publication.

# Publication Information  
$#ref_type: $$ref_type

$#author_corresponding: $$author_corresponding  
$#corresponding_author_contact: $$corresponding_author_contact  

$#author_list: $$author_list  

$#name_journal: $$name_journal  
$#journal_volume: $$journal_volume  
$#journal_date: $$journal_date  
$#page_range: $$page_range  
$#publication_in_press: $$publication_in_press  

# Abstract
$$abstract

# Attachments
$$file_binary
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'reference',
  'owner': 'root',
  'parents': ['information'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Reference: $$title_publication""",
             'tabularview': """$$title_publication $$author_first $$author_list $$journal_date $$name_journal $$pmid $$pmcid"""}},




 {'children': ['person', 'group'],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'People and groups',
  'desc_short': 'People and groups',
  'keytype': 'recorddef',
  'mainview': """This protocol is for organizational purposes, and is not intended to be used.""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'people',
  'owner': 'root',
  'parents': ['root'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': {}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': '(Deprecated) Tilt series',
  'desc_short': '(Deprecated) Tilt series',
  'keytype': 'recorddef',
  'mainview': """ 
# Tilt series

Deprecated; use stack.
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ccd_tilt_series',
  'owner': 'root',
  'parents': [],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': {}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'JAMES frame',
  'desc_short': 'JAMES frame',
  'keytype': 'recorddef',
  'mainview': """
# JAMES-acquired CCD frame
$#performed_by: $$performed_by  
$#date_occurred: $$date_occurred

Camera and microscope data recorded by the JEOL Automated-Microscopy Expert System 

This protocol could be improved.

# Details
$#exposure_time:  $$exposure_time   
$#post_blank_status:  $$post_blank_status   
$#defocus:  $$defocus   
$#pre_exposure_delay:  $$pre_exposure_delay   
$#delta_x:  $$delta_x   
$#delta_y:  $$delta_y   
$#delta_z:  $$delta_z   
$#delta_tx:  $$delta_tx   
$#delta_ty:  $$delta_ty   
$#acquire_text:  $$acquire_text   
$#camera_index:  $$camera_index   
$#post_acquisition_screen_status_lowered:  $$post_acquisition_screen_status_lowered   
$#objective_mini_lens:  $$objective_mini_lens   
$#condenser_lens_3:  $$condenser_lens_3   
$#condenser_lens_2:  $$condenser_lens_2   
$#condenser_lens_1:  $$condenser_lens_1   
$#intermediate_lens_2:  $$intermediate_lens_2   
$#intermediate_lens_3:  $$intermediate_lens_3   
$#coarse_objective_lens:  $$coarse_objective_lens   
$#condenser_mini_lens:  $$condenser_mini_lens   
$#fine_objective_lens:  $$fine_objective_lens   
$#intermediate_lens_1:  $$intermediate_lens_1   
$#projector_lens:  $$projector_lens   
$#projector_deflectors:  $$projector_deflectors   
$#gun_tilt_deflectors:  $$gun_tilt_deflectors   
$#condenser_stigmator_deflectors:  $$condenser_stigmator_deflectors   
$#spot_alignment_1_deflectors:  $$spot_alignment_1_deflectors   
$#condenser_tilt_deflectors:  $$condenser_tilt_deflectors   
$#spot_alignment_2_deflectors:  $$spot_alignment_2_deflectors   
$#image_shift_1_deflectors:  $$image_shift_1_deflectors   
$#condenser_shift_deflectors:  $$condenser_shift_deflectors   
$#intermediate_stigmator_deflectors:  $$intermediate_stigmator_deflectors   
$#gun_shift_deflectors:  $$gun_shift_deflectors   
$#objective_stigmator_deflectors:  $$objective_stigmator_deflectors   
$#image_shift_2_deflectors:  $$image_shift_2_deflectors   
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ccd_james',
  'owner': 'root',
  'parents': ['ccd'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """JAMES CCD frame acquired by $$performed_by on $$date_occurred""",
             'tabularview': """$$exposure_time $$ctf_bfactor $$ctf_defocus_measured $$tem_magnification_set"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': '(Deprecated) Tilt series frame',
  'desc_short': '(Deprecated) Tilt series frame',
  'keytype': 'recorddef',
  'mainview': """
# Tilt series frame

Deprecated; use stack.
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ccd_tilt',
  'owner': 'root',
  'parents': [],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': {}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A book chapter resulting from a projects research. Please enter PMID/PMCID if available. Please link against relevant projects.',
  'desc_short': 'Book chapter',
  'keytype': 'recorddef',
  'mainview': """
# Book Chapter
$#pmid:     $$pmid  
$#pmcid:  $$pmcid  

Note: a PubMed ID or PMCID is sufficient to describe the publication.

# Publication Information  
$#author_corresponding:     $$author_corresponding  
$#corresponding_author_contact:     $$corresponding_author_contact  

$#author_list: $$author_list   
$#author_editor_list: $$author_editor_list  
$#name_book: $$name_book  
$#name_chapter: $$name_chapter  
$#page_range: $$page_range  
$#year_published: $$year_published  
$#publisher: $$publisher  

# Abstract
$$abstract

$#publication_in_press: $$publication_in_press

# Attachments
$$file_binary
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'publication_book',
  'owner': 'root',
  'parents': ['information', 'publication'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Book: $$name_book, $$name_chapter""",
             'tabularview': """$$name_chapter $$author_first $$author_list $$name_book $$pmid $$pmcid"""}},




 {'children': ['grid_cryosection'],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'Grid preparation.',
  'desc_short': 'Grid preparation',
  'keytype': 'recorddef',
  'mainview': """
# Grid preparation
$#performed_by: $$performed_by  
$#date_occurred: $$date_occurred  

# Grid type
$#title_grid: $$title_grid  
$#id_grid_batch: $$id_grid_batch   
$#grid_tem_type: $$grid_tem_type  
$#grid_tem_mesh_size: $$grid_tem_mesh_size  

# Grid Preparation
Get a grid $$description_storage (which canister) canister and fill it with liquid nitrogen.  

Add a loading stick into the canister to cool as well.  

Add a grid holder and a spider into the vitrobot's black rubber holder outside of the inner copper circle. Fill the rubber holder with liquid nitrogen.  

The grids should have a $$select_substrate_grid that was prepared by the following procedure: $$select_substrate_grid_prep  

Check the quality of each grid with a light microscope. Discard any grids that do not meet the experiment's standards.  
$#grids_tem_lost: $$grids_tem_lost 

$#grids_tem_used: $$grids_tem_used  

# Grid Pre-Treatment
$#description_grid_prefreezing: $$description_grid_prefreezing  

If Glow Discharged:
$#time_glowdischarge: $$time_glowdischarge 

# Freezing or Staining
For a frozen-hydrated grid, please make sure a freezing session is linked as a parent. This will allow you to specify the full set of Vitrobot or freezing parameters.  

If this particular grid deviates from the parent freezing session, you can override some of the freezing parameters below:  
$#vitrobot_temp: $$vitrobot_temp   
$#vitrobot_time_blot: $$vitrobot_time_blot   
$#vitrobot_blots: $$vitrobot_blots  
$#vitrobot_blot_offset:  $$vitrobot_blot_offset   
$#vitrobot_time_wait: $$vitrobot_time_wait   
$#vitrobot_time_step: $$vitrobot_time_step   
$#vitrobot_time_drain: $$vitrobot_time_drain  
$#vitrobot_level_liquid: $$vitrobot_level_liquid   
$#direction_blotting:  $$direction_blotting  
$#vitrobot_humid_on: $$vitrobot_humid_on  

Note: If the vitrobot's humidifier is on, then also set  
$#vitrobot_humidity to $$vitrobot_humidity  

# Post-freezing
$#description_grid_postfreezing: $$description_grid_postfreezing  

$#description_storage: $$description_storage  
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'grid_preparation',
  'owner': 'root',
  'parents': ['tem'],
  'private': 0,
  'typicalchld': ['grid_imaging'],
  'uri': None,
  'views': { 'recname': """Grid: $$title_grid by $$performed_by on $$date_occurred""",
             'tabularview': """$$title_grid $$vitrobot_time_step $$vitrobot_time_blot $$vitrobot_blots $$vitrobot_blot_offset $$vitrobot_humid_on $$vitrobot_time_wait $$vitrobot_time_drain $$vitrobot_level_liquid"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'JADAS frame',
  'desc_short': 'JADAS frame',
  'keytype': 'recorddef',
  'mainview': """
# JADAS frame

$#id_ccd_frame:   $$id_ccd_frame   
$#number_exposure:   $$number_exposure    
$#tem_magnification_set:   $$tem_magnification_set  
$#ctf_defocus_set:   $$ctf_defocus_set   

$#tem_dose_rate:   $$tem_dose_rate  
$#tem_dose:   $$tem_dose  
$#time_exposure_tem:   $$time_exposure_tem     

$#angstroms_per_pixel:   $$angstroms_per_pixel  
$#current_screen:    $$current_screen  
$#beam_diameter_tem:   $$beam_diameter_tem  
$#status_energy_filter:   $$status_energy_filter 

# Camera

$#ccd_id: $$ccd_id  
$#ccd_process_identifier: $$ccd_process_identifier    
$#type_frame: $$type_frame    
$#binning: $$binning  
$#size_image_ccd_x: $$size_image_ccd_x $#size_image_ccd_y: $$size_image_ccd_y      

# Stage

$#position_stage_x: $$position_stage_x $#position_stage_y: $$position_stage_y  
$#specimen_tilt:   $$specimen_tilt      

$#ctf_astig_defocus_diff: $$ctf_astig_defocus_diff  
$#ctf_drift_bfactor:   $$ctf_drift_bfactor  
$#ctf_astig_angle:   $$ctf_astig_angle  
$#ctf_drift_angle:   $$ctf_drift_angle   

# Assessment

$#ice_type: $$ice_type  
$#assess_ice_comments: $$assess_ice_comments  
$#assess_ice_thick: $$assess_ice_thick  
$#assess_image_quality: $$assess_image_quality

# Corrected CTF Parameters

$#ctf_defocus_measured: $$ctf_defocus_measured  
$#tem_magnification_measured: $$tem_magnification_measured  
$#ctf_bfactor: $$ctf_bfactor  
$#ctf_snr_max: $$ctf_snr_max  
$#ctf_ampcont: $$ctf_ampcont

# Images

$$file_binary_image

# JADAS Parameters

(*Note: This mapping is still under development. Basic parameters like defocus are available in the normal CCD parameters.)

$#def_beamshiftx:  $$def_beamshiftx  
$#def_beamshifty:  $$def_beamshifty  
$#def_beamtiltx:  $$def_beamtiltx  
$#def_beamtilty:  $$def_beamtilty  
$#def_clstigx:  $$def_clstigx  
$#def_clstigy:  $$def_clstigy  
$#def_gunshiftx:  $$def_gunshiftx  
$#def_gunshifty:  $$def_gunshifty  
$#def_guntiltx:  $$def_guntiltx  
$#def_guntilty:  $$def_guntilty  
$#def_ilstigx:  $$def_ilstigx  
$#def_ilstigy:  $$def_ilstigy  
$#def_imageshiftx:  $$def_imageshiftx  
$#def_imageshifty:  $$def_imageshifty  
$#def_olstigx:  $$def_olstigx  
$#def_olstigy:  $$def_olstigy  
$#def_plax:  $$def_plax  
$#def_play:  $$def_play  

$#defocus_absdac:  $$defocus_absdac  
$#defocus_realphysval:  $$defocus_realphysval  

$#digicamcond_blankbeam:  $$digicamcond_blankbeam  
$#digicamcond_blankingtime:  $$digicamcond_blankingtime  
$#digicamcond_closescreen:  $$digicamcond_closescreen  
$#digicamcond_dataformat:  $$digicamcond_dataformat  
$#digicamcond_preirradiation:  $$digicamcond_preirradiation  

$#digicamprm_areabottom:  $$digicamprm_areabottom  
$#digicamprm_arealeft:  $$digicamprm_arealeft  
$#digicamprm_arearight:  $$digicamprm_arearight   
$#digicamprm_areatop:  $$digicamprm_areatop  
$#digicamprm_binning:  $$digicamprm_binning  
$#digicamprm_cameraname:  $$digicamprm_cameraname  
$#digicamprm_exposure:  $$digicamprm_exposure  

$#eos_alpha:  $$eos_alpha  
$#eos_brightdarkmode:  $$eos_brightdarkmode  
$#eos_darklevel:  $$eos_darklevel  
$#eos_htlevel:  $$eos_htlevel  
$#eos_illuminationmode:  $$eos_illuminationmode  

$#eos_imagingmode:  $$eos_imagingmode  
$#eos_magcamindex:  $$eos_magcamindex  
$#eos_spectrummode:  $$eos_spectrummode  
$#eos_spot:  $$eos_spot  
$#eos_stiglevel:  $$eos_stiglevel  
$#eos_temasidmode:  $$eos_temasidmode  

$#goniopos_rotortilty:  $$goniopos_rotortilty   
$#goniopos_tiltx:  $$goniopos_tiltx  
$#goniopos_x:  $$goniopos_x   
$#goniopos_y:  $$goniopos_y  
$#goniopos_z:  $$goniopos_z  

$#ht_energyshift:  $$ht_energyshift  
$#ht_ht:  $$ht_ht  

$#intendeddefocus_valinnm:  $$intendeddefocus_valinnm   

$#lens_cl1dac:  $$lens_cl1dac  
$#lens_cl2dac:  $$lens_cl2dac  
$#lens_cl3dac:  $$lens_cl3dac  
$#lens_cmdac:  $$lens_cmdac  
$#lens_il1dac:  $$lens_il1dac  
$#lens_il2dac:  $$lens_il2dac  
$#lens_il3dac:  $$lens_il3dac  
$#lens_il4dac:  $$lens_il4dac  
$#lens_pl1dac:  $$lens_pl1dac  
$#lens_pl2dac:  $$lens_pl2dac  
$#lens_pl3dac:  $$lens_pl3dac  

$#mds_blankingdef:  $$mds_blankingdef  
$#mds_blankingtime:  $$mds_blankingtime  
$#mds_blankingtype:  $$mds_blankingtype  
$#mds_defx:  $$mds_defx  
$#mds_defy:  $$mds_defy  
$#mds_mdsmode:  $$mds_mdsmode  
$#mds_shutterdelay:  $$mds_shutterdelay  

$#photo_exposuremode:  $$photo_exposuremode  
$#photo_filmnumber:  $$photo_filmnumber  
$#photo_filmtext:  $$photo_filmtext  
$#photo_manualexptime:  $$photo_manualexptime""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ccd_jadas',
  'owner': 'root',
  'parents': ['ccd'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """JADAS: $$file_binary_image""",
             'tabularview': """$@thumbnail() $$file_binary_image $$ctf_defocus_set $$ctf_defocus_measured $$tem_magnification_set $$ctf_bfactor $$time_exposure_tem $$tem_dose_rate $$assess_image_quality"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'Tomography session',
  'desc_short': 'Tomography session',
  'keytype': 'recorddef',
  'mainview': """
# Tomography session

This protocol is being worked on
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'tomography',
  'owner': 'root',
  'parents': ['grid_imaging', 'microscopy'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Tomography session""",
             'tabularview': """$$tem_magnification_set $$temperature_specimen $$ice_type"""}},




 {'children': ['presentation'],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'General purpose lab notebook entry; stores general notes, observations, results, etc. Attach any relevant files.',
  'desc_short': 'Lab notebook entry',
  'keytype': 'recorddef',
  'mainview': """

# $#subject_notebook: $$subject_notebook
$$description_notebook

# Attachments
$$file_binary
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'labnotebook',
  'owner': 'root',
  'parents': ['information'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Lab notebook: $$subject_notebook""",
             'tabularview': """$$subject_notebook $$file_binary"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': '(Deprecated) JEOL Demo',
  'desc_short': '(Deprecated) JEOL Demo',
  'keytype': 'recorddef',
  'mainview': """
# JEOL Demo

Deprecated
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'jeoldemo',
  'owner': 'root',
  'parents': [],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': {}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': '(Deprecated) Microscope suite',
  'desc_short': '(Deprecated) Microscope suite',
  'keytype': 'recorddef',
  'mainview': """
# Microscope suite

Deprecated.
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'all_microscopes',
  'owner': 'root',
  'parents': [],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': {}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A Vitrobot session. For each grid frozen, there should be a grid_preparation record. Parent should be a purification aliquot.',
  'desc_short': 'Vitrobot session',
  'keytype': 'recorddef',
  'mainview': """
# Vitrobot Session
$#performed_by: $$performed_by  
$#date_occurred: $$date_occurred  

$#title_freezing: $$title_freezing  
$#vitrification_device: $$vitrification_device  
(Which Vitrobot is being used)

# Software Setup

Obtain blotting paper and puncture it using the puncture tool. Load the blotting paper into the vitrobot so that the smoother sides of the blotting paper face each other. Start the vitrobot software program and set the following parameters:

$#vitrobot_temp: $$vitrobot_temp   
$#vitrobot_time_blot: $$vitrobot_time_blot   
$#vitrobot_blots: $$vitrobot_blots  
$#vitrobot_blot_offset:  $$vitrobot_blot_offset   
$#vitrobot_time_wait: $$vitrobot_time_wait   
$#vitrobot_time_step: $$vitrobot_time_step   
$#vitrobot_time_drain: $$vitrobot_time_drain  
$#vitrobot_level_liquid: $$vitrobot_level_liquid   
$#direction_blotting:  $$direction_blotting   

$#vitrobot_humid_on: $$vitrobot_humid_on  
Note: If the vitrobot's humidifier is on, then also set  
$#vitrobot_humidity to $$vitrobot_humidity  

# Vitrobot Freezing

1. Using the vitrobot tweezers, carefully pick up a treated grid, lock the tweezers and load them into the vitrobot. Load the grid by attaching the tweezers to the vitrobot and then pressing the vitrobot's foot pedal once.    
2. Attach a tip to a liquid ethane bottle and pour ethane into the copper circle inside of the vitrobot's rubber holder. Take care that no liquid ethane comes into contact with the liquid nitrogen outside of the copper ring -- contamination may form.   
3. Remove the spider and place the rubber holder underneath the vitrobot. Press the foot pedal once for the vitrobot to load the loader.   
4. From aliquot, apply $$grid_volume_applied ($#grid_volume_applied) sample of in a pipette using the vitrobot's side entry opening.  
5. Press the foot pedal to have the vitrobot blot the sample. Once blotted, the vitrobot will automatically lower the grid, the tweezers it is attached with, and the rubber holder.  
6. Remove the tweezers from the vitrobot while keeping the grid submerged in the liquid ethane.  Quickly move the tweezers from the liquid ethane into the liquid nitrogen on the outside of the copper ring.  
7. Place the grid inside of the grid holder and disengage the tweezers. Remove the loading stick from the $$description_storage container and attach the gridholder to it.  
8. Finally, return the loading stick to the storage container.""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'freezing_vitrobot',
  'owner': 'root',
  'parents': ['freezing'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Vitrobot: $$title_freezing by $$performed_by on $$date_occurred""",
             'tabularview': """$$select_technique_freezing $$aliquot_used $$grids_tem_used $$grid_tem_type $$vitrification_device $$grid_tem_hole_size $$id_grid_batch $$grid_volume_applied"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'An abstract based on the project\'s research; generally from a conference. Please enter PMID/PMCID if available. Please link against relevant subprojects. Attach any relevant files, such as posters or talk slides.',
  'desc_short': 'Conference abstract',
  'keytype': 'recorddef',
  'mainview': """# $#title_publication:  $$title_publication

$#pmid:     $$pmid  
$#pmcid:  $$pmcid  

(Note: PubMed ID is self-sufficient to describe the publication; additional information below will be completed automatically)

# Abstract Information

$#author_corresponding:     $$author_corresponding  
$#corresponding_author_contact:     $$corresponding_author_contact  

$#author_list:    $$author_list  

$#abstract:
$$abstract

$#publication_in_press:    $$publication_in_press  

# Date and Location

$#name_conference:    $$name_conference  
$#city_conference:    $$city_conference  
$#year_published:  $$year_published

# Attachments
$$file_binary
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'publication_abstract',
  'owner': 'root',
  'parents': ['information', 'publication'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Abstract: $$title_publication. $$name_conference, $$year_published, $$city_conference""",
             'tabularview': """$$year_published $$p41_year $$author_list $$title_publication $$name_conference $$city_conference $@recid() $$modifytime"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A P41 Project. These are used for the NCRR reporting system. Generally, each top level project will have a p41_project record.',
  'desc_short': 'P41 project',
  'keytype': 'recorddef',
  'mainview': """$#p41_project_title  $$p41_project_title  
$#p41_abstract  $$p41_abstract  
$#p41_project_type  $$p41_project_type  
$#p41_project_pi  $$p41_project_pi  
$#p41_project_investigators  $$p41_project_investigators  
$#p41_progress  $$p41_progress  
$#p41_percent  $$p41_percent  
$#p41_project_ready  $$p41_project_ready""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'p41_project',
  'owner': 'root',
  'parents': ['project', 'information'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """P41 Report: $$p41_project_title ($$p41_project_pi)""",
             'tabularview': """$$p41_project_title
$$p41_project_pi
$$p41_project_investigators  
$$p41_project_type
$$p41_percent
$@childcount(publication*)
$$modifytime
$$modifyuser
"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'Represents a funding source',
  'desc_short': 'Grant',
  'keytype': 'recorddef',
  'mainview': """
# $#grant_title: $$grant_title  
$#grant_pi:     $$grant_pi  
$#grant_copi:  $$grant_copi  

# Sources
$#grant_source:     $$grant_source  
$#grant_source_type:  $$grant_source_type  
$#grant_number:     $$grant_number  
$#grant_funds:    $$grant_funds  

# Dates
$#grant_start_date:     $$grant_start_date  
$#grant_end_date:  $$grant_end_date  
$#grant_p41_ref_start:    $$grant_p41_ref_start  
$#grant_p41_ref_end:  $$grant_p41_ref_end""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'grant',
  'owner': 'root',
  'parents': ['information'],
  'private': 0,
  'typicalchld': ['publication'],
  'uri': None,
  'views': { 'recname': """Grant: $$grant_source ($$grant_number)""",
             'tabularview': """$$grant_source $$grant_number $$grant_pi $$grant_funds $$grant_start_date $$grant_title"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'Pneumatic plunger session',
  'desc_short': 'Pneumatic plunger session',
  'keytype': 'recorddef',
  'mainview': """
# Pneumatic freezing plunger session
$#date_occurred: $$date_occurred   
$#performed_by: $$performed_by   

# Details
$#frozen_by:  $$frozen_by   
$#vitrification_device: $$vitrification_device   
$#title_freezing:  $$title_freezing   

# Freezing procedure
$$grid_tem_type grids will be used for this freezing sessionThe grids should have a $$select_substrate_grid that was prepared by:
$$select_substrate_grid_prep 
Obtain the $$grids_tem_good grid(s) from grid batch $$id_grid_batch. 
Each grid has a mesh size of $$grid_tem_mesh_size with a hole size of $$grid_tem_hole_size 
Check the quality of each grid with a light microscope. Discard any grids that do not meet the experiment's standards 
$#grids_tem_lost = $$grids_tem_lost 
$#grids_tem_used = $$grids_tem_used 
For each grid, conduct the following $#description_grid_prefreezing: $$description_grid_prefreezing 
For glow discharge, the discharge time is $$time_glowdischarge 

# After Freezing: 
$#description_grid_postfreezing: $$description_grid_postfreezing   
$#select_technique_freezing: $$select_technique_freezing  
$#description_storage: $$description_storage  
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'freezing_pneumatic',
  'owner': 'root',
  'parents': ['freezing'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Pneumatic freezing session: $$title_freezing by $$performed_by on $$date_occurred"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': '(Deprecated) Discussion',
  'desc_short': '(Deprecated) Discussion',
  'keytype': 'recorddef',
  'mainview': """
# Discussion

Deprecated; use project_meeting
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'discussion',
  'owner': 'root',
  'parents': [],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': {}},




 {'children': [ 'scanner',
                'microscope',
                'camera',
                'equipment_maintenance',
                'vitrification_device'],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'Specialized folder for equipment records',
  'desc_short': 'Equipment folder',
  'keytype': 'recorddef',
  'mainview': """
# Equipment folder: $$name_folder

Description: $$folder_description  
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'equipment',
  'owner': 'root',
  'parents': ['root'],
  'private': 0,
  'typicalchld': ['equipment_maintenance'],
  'uri': None,
  'views': { 'recname': """Equipment: $$name_folder"""}},




 {'children': ['subproject_software'],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'This is a project specifically targeted at software development rather than a biological target.',
  'desc_short': 'Software project',
  'keytype': 'recorddef',
  'mainview': """
# Software project: $$name_project

<div style="border:solid 1px #ccc;padding:10px;margin:10px;margin-left:0px;width:400px">

$#project_status: $$project_status  

$#project_block: $$project_block  

<span class="e2-button e2-record-new" data-rectype="progress_report" data-parent="$$name">New progress report</span>   <br />

<span class="e2-button e2-record-new" data-rectype="labnotebook" data-parent="$$name">New lab notebook entry</span>  

</div>

$#name_pi: $$name_pi
$#project_investigators: $$project_investigators

# Project Description

$#project_type: $$project_type 
$#description_goals: $$description_goals
$#description_background: $$description_background
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'project_software',
  'owner': 'root',
  'parents': ['project'],
  'private': 0,
  'typicalchld': ['progress_report'],
  'uri': None,
  'views': { 'recname': """Project $$name_project ($$name_specimen)""",
             'tabularview': """$$name_project $$name_pi  $$project_type $$project_status $$project_block"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'Reconstruction',
  'desc_short': 'Reconstruction',
  'keytype': 'recorddef',
  'mainview': """
# Reconstruction

The purpose of this record is to store the parameter values associated with density maps and representations of the reconstruction itself.

$#mapname:  $$mapname   
$#date_occurred:  $$date_occurred       
$#angstroms_per_pixel:  $$angstroms_per_pixel  

$#resolution_cutoff:  $$resolution_cutoff     
$#shell_corr_fourier:  $$shell_corr_fourier  

$#description_reconstruction:  $$description_reconstruction        
$#parameters_reconstruction:  $$parameters_reconstruction        

$#z_value:  $$z_value     
$#y_value:  $$y_value     
$#x_value:  $$x_value     

# Comments
$#comment_reconstruction:  $$comment_reconstruction

Additional comments about this reconstruction:
$$comments

# Attachments
$$file_binary
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'reconstruction',
  'owner': 'root',
  'parents': ['information'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Reconstruction: $$mapname ($$resolution_cutoff)""",
             'tabularview': """$$mapname $$comment_reconstruction $$angstroms_per_pixel $$x_value $$y_value $$z_value $$resolution_cutoff $$shell_corr_fourier"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'Please use nested "project" records, instead of the "subproject" protocol.',
  'desc_short': 'Subproject',
  'keytype': 'recorddef',
  'mainview': """
# Subproject: $$name_project

<div style="border:solid 1px #ccc;padding:10px;margin:10px;margin-left:0px;width:400px">

$#project_status: $$project_status  

$#project_block: $$project_block  

<span class="e2-button e2-record-new" data-rectype="progress_report" data-parent="$$name">New progress report</span>   <br />

<span class="e2-button e2-record-new" data-rectype="labnotebook" data-parent="$$name">New lab notebook entry</span>  

</div>

# Subproject-specific information, if different from main project

$#name_pi: $$name_pi  
$#project_investigators: $$project_investigators  
$#project_type: $$project_type  

# Specimen
$#name_specimen: $$name_specimen  
$#symmetry_particle: $$symmetry_particle  
$#mass_specimen: $$mass_specimen  
$#diameter_max: $$diameter_max   
$#diameter_min:    $$diameter_min  
$#hazard_bl_max: $$hazard_bl_max   

# Project Description
$#description_goals:  $$description_goals  
$#description_medical_relevance:  $$description_medical_relevance  
$#description_background: $$description_background  

# Associated sequence data
$#description_genetic: $$description_genetic  
(Or, for single components):   
$#sequence_dna: $$sequence_dna   
$#sequence_rna: $$sequence_rna  
$#sequence_protein: $$sequence_protein   
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'subproject',
  'owner': 'root',
  'parents': ['project', 'information'],
  'private': 0,
  'typicalchld': [ 'project',
                 'labnotebook',
                 'grid_imaging',
                 'publication',
                 'publication_abstract',
                 'purification',
                 'movie',
                 'volume',
                 'project_meeting',
                 'reference',
                 'manuscript',
                 'progress_report'],
  'uri': None,
  'views': { 'recname': """Subproject: $$name_project""",
             'tabularview': """$$name_project $$name_specimen $$name_pi $$project_status $$project_block $@childcount(publication*) $@childcount(grid_imaging)"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'This record represents a single frame from an uploaded image stack (usually tomogram). This protocol is somewhat deprecated; individual frames are no longer separated out from the main stack.',
  'desc_short': 'Tilt-series image',
  'keytype': 'recorddef',
  'mainview': """
# Tilt-series image

See parent record for full details.

This protocol is somewhat deprecated; individual frames are no longer separated out from the main stack.

$#specimen_tilt: $$specimen_tilt  
$#stack_data_montage: $$stack_data_montage  
$#stack_stagepos: $$stack_stagepos  
$#tem_magnification_set: $$tem_magnification_set  
$#stack_intensity: $$stack_intensity
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stackimage',
  'owner': 'root',
  'parents': ['stack'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Slice: tilt angle, $$specimen_tilt""",
             'tabularview': """$@thumbnail() $$specimen_tilt $$stack_data_montage $$stack_stagepos $$tem_magnification_set $$stack_intensity $$stack_dose"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A Direct Electron Detector frame. Please enter defocus, magnification, and dose at a minimum. The measured defocus and B-factor may be set after CTF correction by EMAN/EMAN2 scripts. Parent should be a grid_imaging session.',
  'desc_short': 'DDD frame',
  'keytype': 'recorddef',
  'mainview': """ 
# DDD frame
$#performed_by: $$performed_by  
$#date_occurred: $$date_occurred

$#ccd_process_identifier:   $$ccd_process_identifier   
$#number_exposure:  $$number_exposure    
$#id_ccd_frame:   $$id_ccd_frame   
$#binning:   $$binning   

# Images
Summed image:  
$$file_binary_image

Raw data:  
$$file_binary

# MDS Setup:    
Set up and note the following for Photo mode:       
$#tem_dose_rate:   $$tem_dose_rate   
$#tem_dose:   $$tem_dose   
$#time_exposure_tem:   $$time_exposure_tem   
$#beam_diameter_tem: $$beam_diameter_tem   
$#tem_magnification_set: $$tem_magnification_set   

# Setup
Camera $$ccd_id will be used to take images with a frame size of $$size_image_ccd_x pixels by $$size_image_ccd_y pixels  

Using DigitalMicrograph or the appropriate method, insert the CCD camera (click Camera -> Insert Camera)  

Move the microscope stage to a completely empty area  

Click Camera -> Prepare Gain Reference to properly minimize the CCD's quadrant effect  

Start the appropriate software (e.g., pydb) and log in  

# Imaging:  
Switch MDS mode to "Search Mode"  

Move to an area of interest at ($$position_stage_x, $$position_stage_y)  

# Switch to "Focus Mode" under MDS
Check the Z-height if necessary (this is usually only necessary when moving from one grid square to another)  

Check that DV is close to 0  

Check that the image is neither underfocused nor overfocused  

Blank beam and set defocus value  

Switch to "Photo Mode" under MDS  

$#specimen_tilt to $$specimen_tilt   

$#status_energy_filter to $$status_energy_filter  

Choose whether a single image or focal pair will be taken  

Set the defocus value(s) to $$ctf_defocus_set  

Wait some time for the stage to stabilize  

Acquire image (e.g. select "Acquire" or "Start Capture" etc.)   

It is crucial that all vibrations from outside sources (such as talking and walking) be kept to a minimum at this pointOnce the image(s) have been taken, the "Acquire" button will become clickable again  

Optionally, the grid hole can now be "marked" as imaged by burning a hole in it  

Check the dose and screen current in an empty area  

Switch to "Focus Mode" under MDS, intensify the electron beam, and melt the ice in the grid circle.

Remember to deintensify the beam once the ice has been meltedAt this point additional images can be taken by repeating the procedure above with new grid coordinates    

# Assessment
$#ice_type: $$ice_type  
$#assess_ice_comments: $$assess_ice_comments  
$#assess_ice_thick: $$assess_ice_thick  
$#assess_image_quality: $$assess_image_quality

# Corrected CTF Parameters
$#ctf_defocus_measured: $$ctf_defocus_measured  
$#tem_magnification_measured: $$tem_magnification_measured  
$#ctf_bfactor: $$ctf_bfactor  
$#ctf_snr_max: $$ctf_snr_max  
$#ctf_ampcont: $$ctf_ampcont
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ddd',
  'owner': 'root',
  'parents': ['image_capture'],
  'private': False,
  'typicalchld': ['box'],
  'uri': None,
  'views': { 'recname': """DDD $$file_binary_image""",
             'tabularview': """$@thumbnail() $$file_binary_image $$ctf_defocus_set $$ctf_defocus_measured $$tem_magnification_set $$ctf_bfactor $$time_exposure_tem $$tem_dose_rate $$assess_image_quality"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A group of people collaborating on some project or sharing a common interest.',
  'desc_short': 'Working group',
  'keytype': 'recorddef',
  'mainview': """
# Working group

This group was organized by $$localperson

for the purpose of discussing $$comment_purpose

Detailed description:
$$description_goals

Members of this group include:
$$project_investigators
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'working_group',
  'owner': 'root',
  'parents': ['information'],
  'private': 0,
  'typicalchld': ['presentation'],
  'uri': None,
  'views': { 'recname': """$$comment_purpose Working Group""",
             'tabularview': """$$localperson $$comment_purpose"""}},




 {'children': ['p41_grant_info',
                'reference',
                'project_meeting',
                'labnotebook',
                'working_group',
                'publication_abstract',
                'p41_project',
                'manuscript',
                'grant',
                'movie',
                'reconstruction',
                'folder',
                'subproject',
                'form',
                'progress_report',
                'volume',
                'structure',
                'publication',
                'publication_book',
                'project'],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': None,
  'desc_short': 'Information and reports',
  'keytype': 'recorddef',
  'mainview': """This protocol is for organizational purposes, and is not intended to be used.""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'information',
  'owner': 'root',
  'parents': ['root'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': {}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'Gatan MkII freezing session',
  'desc_short': 'Gatan MkII freezing session',
  'keytype': 'recorddef',
  'mainview': """ 
# Gatam MkII Freezing session
$#date_occurred: $$date_occurred  
$#performed_by: $$performed_by  
$#frozen_by: $$frozen_by  
$#vitrification_device: $$vitrification_device  
$#title_freezing: $$title_freezing  

Note: this protocol is under development.

# Grids
$$grid_tem_type grids will be used for this freezing session.  
The grids should have a $$select_substrate_grid that was prepared by: $$select_substrate_grid_prep  
Obtain the $$grids_tem_good grid(s) from grid batch $$id_grid_batch.  
Each grid has a mesh size of $$grid_tem_mesh_size with a hole size of $$grid_tem_hole_size  
Check the quality of each grid with a light microscope. Discard any grids that do not meet the experiment's standards.  
    $#grids_tem_lost = $$grids_tem_lost  
    $#grids_tem_used = $$grids_tem_used  
$#description_grid_prefreezing: $$description_grid_prefreezing  
For glow discharge, the discharge time is $$time_glowdischarge  

# Freezing
$#grid_volume_applied: $$grid_volume_applied  

# Plunger settings
$#vitrobot_temp: $$vitrobot_temp    
$#vitrobot_time_blot: $$vitrobot_time_blot   
$#vitrobot_blots: $$vitrobot_blots  
$#direction_blotting:  $$direction_blotting   
$#vitrobot_humid_on: $$vitrobot_humid_on  
Note: If the humidifier is on, then also set  
$#vitrobot_humidity to $$vitrobot_humidity  

# After Freezing
$#description_grid_postfreezing: $$description_grid_postfreezing  
$#select_technique_freezing: $$select_technique_freezing  
$#description_storage: $$description_storage
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'freezing_gatanmkii',
  'owner': 'root',
  'parents': ['freezing'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': {  'recname': """Gatan MkII freezing session: $$title_freezing by $$performed_by on $$date_occurred"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'High pressure freezing session',
  'desc_short': 'High pressure freezing session',
  'keytype': 'recorddef',
  'mainview': """
# High pressure freezing session
$#date_occurred: $$date_occurred  
$#performed_by: $$performed_by  
$#frozen_by: $$frozen_by  
$#vitrification_device: $$vitrification_device  
$#title_freezing: $$title_freezing  

Note: this protocol is under development.

# Grids
$$grid_tem_type grids will be used for this freezing session.  

The grids should have a $$select_substrate_grid that was prepared by: $$select_substrate_grid_prep  

Obtain the $$grids_tem_good grid(s) from grid batch $$id_grid_batch.  

Each grid has a mesh size of $$grid_tem_mesh_size with a hole size of $$grid_tem_hole_size  

Check the quality of each grid with a light microscope. Discard any grids that do not meet the experiment's standards.  
    $#grids_tem_lost = $$grids_tem_lost  
    $#grids_tem_used = $$grids_tem_used  

$#description_grid_prefreezing: $$description_grid_prefreezing  

For glow discharge, the discharge time is $$time_glowdischarge  

# Freezing
$#grid_volume_applied: $$grid_volume_applied  

# Plunger settings
$#vitrobot_temp: $$vitrobot_temp    

$#vitrobot_time_blot: $$vitrobot_time_blot   

$#vitrobot_blots: $$vitrobot_blots  

$#direction_blotting:  $$direction_blotting   

$#vitrobot_humid_on: $$vitrobot_humid_on  

Note: If the humidifier is on, then also set  
$#vitrobot_humidity to $$vitrobot_humidity  

# After Freezing
$#description_grid_postfreezing: $$description_grid_postfreezing  

$#select_technique_freezing: $$select_technique_freezing  

$#description_storage: $$description_storage
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'freezing_high_pressure',
  'owner': 'root',
  'parents': ['freezing'],
  'private': False,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """High pressure freezing session: $$title_freezing by $$performed_by on $$date_occurred"""}},




 {'children': ['box'],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': None,
  'desc_short': 'Processing',
  'keytype': 'recorddef',
  'mainview': """This protocol is for organizational purposes, and is not intended to be used.""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'processing',
  'owner': 'root',
  'parents': ['root'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': {}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'An update on progress in the project. Attach any relevant files.',
  'desc_short': 'Progress Report',
  'keytype': 'recorddef',
  'mainview': """
# Progress report
$$description_progress

# Attachments
$$file_binary
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'progress_report',
  'owner': 'root',
  'parents': ['information'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Progress Report by $$performed_by on $$date_occurred""",
             'tabularview': """$$description_progress $$file_binary"""}},




 {'children': ['ccd', 'micrograph', 'scan', 'stack', 'ddd'],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': None,
  'desc_short': 'Image types',
  'keytype': 'recorddef',
  'mainview': """This protocol is for organizational purposes, and is not intended to be used.""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'image_capture',
  'owner': 'root',
  'parents': ['tem'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': {}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'Single particle (virus) session',
  'desc_short': 'Single particle (virus) session',
  'keytype': 'recorddef',
  'mainview': """
# Virus imaging session

Reserved for future use.
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'virus',
  'owner': 'root',
  'parents': ['grid_imaging', 'microscopy'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': {}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'Single particle microscopy session',
  'desc_short': 'Single particle microscopy session',
  'keytype': 'recorddef',
  'mainview': """
# Single particle microscopy session

Reserved for future use
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'single_particle',
  'owner': 'root',
  'parents': ['grid_imaging', 'microscopy'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': {}},




 {'children': ['person', 'folder', 'group'],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'Core Protocols',
  'desc_short': 'Core',
  'keytype': 'recorddef',
  'mainview': """This protocol is for organizational purposes, and is not intended to be used.""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'core',
  'owner': 'root',
  'parents': ['root'],
  'private': False,
  'typicalchld': [],
  'uri': 'http://ncmidb.bcm.edu',
  'views': {}},




 {'children': ['tomography', 'virus', 'single_particle'],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'This record represents a single grid during an imaging session. There may be several grid_imaging records per microscopy session. Children will be ccd, micrograph, or stack. Parents should be the project or subproject, the grid_preparation record (see freezing session), and the microscopy session.\n\nNote: grid imaging sessions are usually created using EMDash, which manages all the other associated records and relationships.',
  'desc_short': 'Grid imaging session',
  'keytype': 'recorddef',
  'mainview': """
# Grid Imaging Session
$#performed_by: $$performed_by  
$#date_occurred: $$date_occurred  
$#description_purpose: $$description_purpose  
$#cryoholder: $$cryoholder  
$#temperature_specimen: $$temperature_specimen  
$#tem_lowdose_method: $$tem_lowdose_method  

# Micrograph Defaults
$#ctf_defocus_set: $$ctf_defocus_set  
$#tem_magnification_set: $$tem_magnification_set  
$#time_exposure_tem: $$time_exposure_tem  
$#tem_dose_rate: $$tem_dose_rate  
$#binning: $$binning  
$#status_energy_filter: $$status_energy_filter
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'grid_imaging',
  'owner': 'root',
  'parents': ['tem'],
  'private': 0,
  'typicalchld': ['ccd', 'stack', 'micrograph', 'ddd'],
  'uri': None,
  'views': { 'recname': """Imaging: $@parentvalue(title_grid) on $@parentvalue(tem_name,2) by $$performed_by on $$date_occurred: $@childcount(image_capture*) images""",
             'tabularview': """$$tem_magnification_set $$temperature_specimen $$description_purpose $@parentvalue(title_freezing) $@childcount(ccd) $@childcount(ddd) $@childcount(micrograph) $@childcount(scan)"""}},




 {'children': ['stackimage'],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A stack of images, usually a tomogram. Parent is a grid_imaging record, with stackimage records as children.',
  'desc_short': 'Image stack',
  'keytype': 'recorddef',
  'mainview': """
# Tilt-Series
$#performed_by: $$performed_by  
$#date_occurred: $$date_occurred  

# Attachments
$$file_binary

Note: uploading very large (&gt;1gb) files with this form may cause browser crashes; please use the "Attachments" tool (paper clip icon) after the record has been created.

The following values will be harvested from the image stack header.

# Values from header
$#stack_size_nx: $$stack_size_nx  
$#stack_size_ny: $$stack_size_ny  
$#stack_size_nz: $$stack_size_nz  
$#stack_maxangle: $$stack_maxangle  
$#stack_minangle: $$stack_minangle  

$#stack_slitwidth: $$stack_slitwidth  
$#aperture_objective: $$aperture_objective  
$#stack_saxtonincrement: $$stack_saxtonincrement  
$#stack_fixedincrement: $$stack_fixedincrement  
$#ctf_defocus_set: $$ctf_defocus_set  
$#tem_magnification_set: $$tem_magnification_set  
$#binning: $$binning  

$#stack_data_nlabl: $$stack_data_nlabl  
$#stack_data_labels: $$stack_data_labels 

# Additional Values from Header
$#stack_data_mode: $$stack_data_mode  

$#stack_start_nx: $$stack_start_nx  
$#stack_start_ny: $$stack_start_ny  
$#stack_start_nz: $$stack_start_nz  

$#stack_size_mx: $$stack_size_mx  
$#stack_size_my: $$stack_size_my  
$#stack_size_mz: $$stack_size_mz  

$#stack_size_xlen: $$stack_size_xlen  
$#stack_size_ylen: $$stack_size_ylen  
$#stack_size_zlen: $$stack_size_zlen  

$#stack_angle_alpha: $$stack_angle_alpha  
$#stack_angle_beta: $$stack_angle_beta  
$#stack_angle_gamma: $$stack_angle_gamma  

$#stack_map_mapc: $$stack_map_mapc  
$#stack_map_mapr: $$stack_map_mapr  
$#stack_map_maps: $$stack_map_maps  

$#stack_pixel_min: $$stack_pixel_min  
$#stack_pixel_max: $$stack_pixel_max  
$#stack_pixel_mean: $$stack_pixel_mean  

$#stack_data_ispg: $$stack_data_ispg  
$#stack_data_nsymbt: $$stack_data_nsymbt  
$#stack_data_extheadersize: $$stack_data_extheadersize  
$#stack_data_creatid: $$stack_data_creatid  
$#stack_data_bytespersection: $$stack_data_bytespersection  
$#stack_data_extheaderflags: $$stack_data_extheaderflags  
$#stack_data_idtype: $$stack_data_idtype  
$#stack_data_lens: $$stack_data_lens  
$#stack_data_nd1: $$stack_data_nd1   
$#stack_data_nd2: $$stack_data_nd2  
$#stack_data_vd1: $$stack_data_vd1  
$#stack_data_vd2: $$stack_data_vd2  
$#stack_data_montage: $$stack_data_montage  
$#stack_stagepos: $$stack_stagepos  
$#stack_intensity: $$stack_intensity  
$#stack_data_xorg: $$stack_data_xorg  
$#stack_data_yorg: $$stack_data_yorg  
$#stack_data_zorg: $$stack_data_zorg  
$#stack_data_cmap: $$stack_data_cmap  
$#stack_data_stamp: $$stack_data_stamp  
$#stack_data_rms: $$stack_data_rms  

$#stack_data_tiltangles_orig: $$stack_data_tiltangles_orig   
$#stack_data_tiltangles_current: $$stack_data_tiltangles_current
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'stack',
  'owner': 'root',
  'parents': ['image_capture', 'tem'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Image Stack: $$stack_size_nx x $$stack_size_ny x $$stack_size_nz ( $$stack_minangle : $$stack_maxangle )""",
             'tabularview': """$$stack_filename $$stack_size_nx $$stack_size_ny $$stack_size_nz $$stack_maxangle $$stack_minangle"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A refined 3D structure.',
  'desc_short': 'Structure',
  'keytype': 'recorddef',
  'mainview': """ 
# Structure
$#performed_by: $$performed_by  
$#date_occurred: $$date_occurred  

# Details
$#title_structure:  $$title_structure   
$#source_sample:  $$source_sample   
$#provided_by:  $$provided_by   
$#processed_structure:  $$processed_structure   

# Attachments
$#file_binary:  $$file_binary                
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'structure',
  'owner': 'root',
  'parents': ['information'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Structure: $$title_structure"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'Protocol for box coordinates',
  'desc_short': 'Box',
  'keytype': 'recorddef',
  'mainview': """

# $#box_label: $$box_label
$#box_size: $$box_size

Box Coordinates:
$$box_coords

# Box file attachment (old way)
$$box
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'box',
  'owner': 'root',
  'parents': ['processing'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """$$box_count Boxes""",
             'tabularview': """$$box_size $$box_count"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A Cryo-EM, EMAN, or other type of workshop. This will generally serve as an area for linking public data sets, uploading presentations and posters, and registering users.',
  'desc_short': 'Workshop',
  'keytype': 'recorddef',
  'mainview': """

# Workshop: $$name_project
$#description_goals: $$description_goals   
$#organizers: $$organizers  
$#instructors: $$instructors  

# Address
$#address_street:    $$address_street  
$#address_city:  $$address_city  
$#address_state:  $$address_state   
$#address_zipcode:     $$address_zipcode     
$#address_international:  $$address_international     

# Dates
$#date_start: $$date_start  
$#date_end: $$date_end  

# Agenda  
$$agenda   
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'workshop',
  'owner': 'root',
  'parents': ['project'],
  'private': 0,
  'typicalchld': ['presentation'],
  'uri': None,
  'views': { 'recname': """$$name_project Workshop on $$date_start""",
             'tabularview': """$$name_project $$date_start $$date_end"""}},




 {'children': ['aliquot'],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A biochemical purification. There should be at least one aliquot child record.',
  'desc_short': 'Purification',
  'keytype': 'recorddef',
  'mainview': """
# Purification

$#title_purification: $$title_purification

# Tracking / Source

$#provided_by: $$provided_by  
$#name_receiver: $$name_receiver  
$#date_occurred: $$date_occurred  
$#date_received: $$date_received  

# Storage

$#description_storage_conditions: $$description_storage_conditions

# Buffer Details and Properties

$#volume_aliquot: $$volume_aliquot  
$#concentration_solution: $$concentration_solution  
$#description_buffer_purification: $$description_buffer_purification  
$#description_buffer_dilution: $$description_buffer_dilution  

$#description_specimen_stability: $$description_specimen_stability  
$#absorbance_at_wavelength: $$absorbance_at_wavelength  
$#wavelength_at_absorbance: $$wavelength_at_absorbance  

# Purification Protocol

$$description_purification

(* describe the protocol or provide a reference)
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'purification',
  'owner': 'root',
  'parents': ['experiments'],
  'private': 0,
  'typicalchld': ['aliquot'],
  'uri': None,
  'views': { 'recname': """Purification: $$title_purification by $$creator @ $$creationtime: $@childcount(aliquot) aliquots""",
             'tabularview': """$$date_received $$provided_by $$name_receiver $$title_purification $$description_storage_conditions $$concentration_solution $@childcount(aliquot)"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'Contact details for a person. These are usually associated with User accounts, but can also be used to store contact details in other places, e.g. a project or report.',
  'desc_short': 'Person',
  'keytype': 'recorddef',
  'mainview': """
# Person

Do not edit directly. Use the user profile view.
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'person',
  'owner': 'root',
  'parents': ['core', 'people'],
  'private': False,
  'typicalchld': [],
  'uri': 'http://ncmidb.bcm.edu',
  'views': { 'recname': '$$name_first $$name_last'}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'Maintenance record for a scanner.',
  'desc_short': 'Scanner maintenance',
  'keytype': 'recorddef',
  'mainview': """
# Scanner maintenance
$#performed_by: $$performed_by
$#date_occurred: $$date_occurred

# Service performed
$#service_engineer:  $$service_engineer  
$#service_date:  $$service_date   
(if different than the date occurred above)  
$#service_type:  $$service_type  
$#service_description:  $$service_description  

# Attachments
$$file_binary
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'scanner_maintenance',
  'owner': 'root',
  'parents': ['equipment_maintenance'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Scanner maintenance: $$service_type on $$service_date"""}},



 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A visualization or movie. Attach any relevant files.',
  'desc_short': 'Movie',
  'keytype': 'recorddef',
  'mainview': """
# Visualization / animation / movie
$#visualization_name: $$visualization_name  
$#visualization_accession: $$visualization_accession  
$#visualization_synopsis: $$visualization_synopsis  
$#visualization_length: $$visualization_length   

# Status and Contact
$#project_status: $$project_status  
$#date_due: $$date_due   
$#date_complete: $$date_complete  
$#contact_technical: $$contact_technical  

# Comments
$#comments_editor: $$comments_editor  
$#comments_creator: $$comments_creator  
$#talk_audience: $$talk_audience  

# Attachments
$$file_binary
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'movie',
  'owner': 'root',
  'parents': ['information'],
  'private': 0,
  'typicalchld': [],
  'uri': None,
  'views': { 'recname': """Visualization: $$visualization_name ($$visualization_length) by $$performed_by (status: $$project_status)""",
             'tabularview': """$$visualization_name $$visualization_length $$project_status $$date_due"""}},




 {'children': ['ccd_james', 'ccd_jadas'],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A CCD frame. Please enter defocus, magnification, and dose at a minimum. The measured defocus and B-factor may be set after CTF correction by EMAN/EMAN2 scripts. Parent should be a grid_imaging session.\n\nNote: Please use EMDash to create images.',
  'desc_short': 'CCD frame',
  'keytype': 'recorddef',
  'mainview': """
# CCD frame
$#performed_by: $$performed_by  
$#date_occurred: $$date_occurred

$#ccd_process_identifier:   $$ccd_process_identifier   
$#number_exposure:  $$number_exposure    
$#id_ccd_frame:   $$id_ccd_frame   
$#binning:   $$binning   

# Image file
$$file_binary_image

# MDS Setup:    
Set up and note the following for Photo mode:       
$#tem_dose_rate:   $$tem_dose_rate   
$#tem_dose:   $$tem_dose   
$#time_exposure_tem:   $$time_exposure_tem   
$#beam_diameter_tem: $$beam_diameter_tem   
$#tem_magnification_set: $$tem_magnification_set   
  
# Setup
Camera $$ccd_id will be used to take images with a frame size of $$size_image_ccd_x pixels by $$size_image_ccd_y pixels  

Using DigitalMicrograph or the appropriate method, insert the CCD camera (click Camera -> Insert Camera)  

Move the microscope stage to a completely empty area  

Click Camera -> Prepare Gain Reference to properly minimize the CCD's quadrant effect  

Start the appropriate software (e.g., pydb) and log in  

# Imaging:  
Switch MDS mode to "Search Mode"  

Move to an area of interest at ($$position_stage_x, $$position_stage_y)  

# Switch to "Focus Mode" under MDS
Check the Z-height if necessary (this is usually only necessary when moving from one grid square to another)  

Check that DV is close to 0  

Check that the image is neither underfocused nor overfocused  

Blank beam and set defocus value  

Switch to "Photo Mode" under MDS  

$#specimen_tilt to $$specimen_tilt   

$#status_energy_filter to $$status_energy_filter  

Choose whether a single image or focal pair will be taken  

Set the defocus value(s) to $$ctf_defocus_set  

Wait some time for the stage to stabilize  

Acquire image (e.g. select "Acquire" or "Start Capture" etc.)   

It is crucial that all vibrations from outside sources (such as talking and walking) be kept to a minimum at this pointOnce the image(s) have been taken, the "Acquire" button will become clickable again  

Optionally, the grid hole can now be "marked" as imaged by burning a hole in it  

Check the dose and screen current in an empty area  

Switch to "Focus Mode" under MDS, intensify the electron beam, and melt the ice in the grid circle.

Remember to deintensify the beam once the ice has been meltedAt this point additional images can be taken by repeating the procedure above with new grid coordinates    

# Assessment
$#ice_type: $$ice_type  
$#assess_ice_comments: $$assess_ice_comments  
$#assess_ice_thick: $$assess_ice_thick  
$#assess_image_quality: $$assess_image_quality

# Corrected CTF Parameters
$#ctf_defocus_measured: $$ctf_defocus_measured  
$#tem_magnification_measured: $$tem_magnification_measured  
$#ctf_bfactor: $$ctf_bfactor  
$#ctf_snr_max: $$ctf_snr_max  
$#ctf_ampcont: $$ctf_ampcont 
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'ccd',
  'owner': 'root',
  'parents': ['image_capture'],
  'private': 0,
  'typicalchld': ['box'],
  'uri': None,
  'views': { 'defaultview': """
# CCD Frame
$#date_occurred: $$date_occurred  
$#performed_by: $$performed_by

$#tem_magnification_set:   $$tem_magnification_set  
$#ctf_defocus_set:   $$ctf_defocus_set   
$#angstroms_per_pixel:   $$angstroms_per_pixel  

$#time_exposure_tem:   $$time_exposure_tem     
$#tem_dose_rate:   $$tem_dose_rate  
$#tem_dose:   $$tem_dose  

$#ccd_id: $$ccd_id  
$#id_ccd_frame: $$id_ccd_frame  
$#type_frame: $$type_frame    
$#binning: $$binning  
$#size_image_ccd_x: $$size_image_ccd_x $#size_image_ccd_y: $$size_image_ccd_y      

# Image file
$$file_binary_image  

# Additional details
$#number_exposure:   $$number_exposure    
$#status_energy_filter:   $$status_energy_filter  
$#beam_diameter_tem:   $$beam_diameter_tem  
$#current_screen:    $$current_screen  

# Stage
$#position_stage_x: $$position_stage_x $#position_stage_y: $$position_stage_y  
$#specimen_tilt:   $$specimen_tilt      

$#ctf_astig_defocus_diff: $$ctf_astig_defocus_diff  
$#ctf_drift_bfactor: $$ctf_drift_bfactor  
$#ctf_astig_angle: $$ctf_astig_angle  
$#ctf_drift_angle: $$ctf_drift_angle   

# Assessment
$#ice_type: $$ice_type  
$#assess_ice_comments: $$assess_ice_comments  
$#assess_ice_thick: $$assess_ice_thick  
$#assess_image_quality: $$assess_image_quality

# Corrected CTF Parameters
$#ctf_defocus_measured: $$ctf_defocus_measured  
$#tem_magnification_measured: $$tem_magnification_measured  
$#ctf_bfactor: $$ctf_bfactor  
$#ctf_snr_max: $$ctf_snr_max  
$#ctf_ampcont: $$ctf_ampcont
""",
             'recname': """CCD $$file_binary_image""",
             'tabularview': """$@thumbnail() $$file_binary_image $$ctf_defocus_set $$ctf_defocus_measured $$tem_magnification_set $$ctf_bfactor $$time_exposure_tem $$tem_dose_rate $$assess_image_quality"""}},




 {'children': [],
  'creationtime': '2011-12-08T11:39:12Z',
  'creator': 'root',
  'desc_long': 'A micrograph taken on film. If the image is scanned, there should be a scan child. There may be multiple scans per micrograph. Parent should be a grid_imaging session.',
  'desc_short': 'Film micrograph',
  'keytype': 'recorddef',
  'mainview': """
# Film micrograph
$#date_occurred: $$date_occurred  
$#performed_by: $$performed_by
$#id_micrograph: $$id_micrograph  
$#number_exposure: $$number_exposure   

$#tem_magnification_set:   $$tem_magnification_set  
$#ctf_defocus_set:   $$ctf_defocus_set   
$#angstroms_per_pixel:   $$angstroms_per_pixel  

$#time_exposure_tem:   $$time_exposure_tem     
$#tem_dose_rate:   $$tem_dose_rate  
$#tem_dose:   $$tem_dose  

$#ccd_id: $$ccd_id  
$#id_ccd_frame: $$id_ccd_frame  
$#type_frame: $$type_frame    
$#binning: $$binning  
$#size_image_ccd_x: $$size_image_ccd_x $#size_image_ccd_y: $$size_image_ccd_y      

# Additional details
$#number_exposure:   $$number_exposure    
$#status_energy_filter:   $$status_energy_filter 
$#beam_diameter_tem:   $$beam_diameter_tem  
$#current_screen:    $$current_screen  

# Stage
$#position_stage_x: $$position_stage_x $#position_stage_y: $$position_stage_y  
$#specimen_tilt:   $$specimen_tilt      

$#ctf_astig_defocus_diff: $$ctf_astig_defocus_diff  
$#ctf_drift_bfactor: $$ctf_drift_bfactor  
$#ctf_astig_angle: $$ctf_astig_angle  
$#ctf_drift_angle: $$ctf_drift_angle   

# Assessment
$#ice_type: $$ice_type  
$#assess_ice_comments: $$assess_ice_comments  
$#assess_ice_thick: $$assess_ice_thick  
$#assess_image_quality: $$assess_image_quality

# Corrected CTF Parameters
$#ctf_defocus_measured: $$ctf_defocus_measured  
$#tem_magnification_measured: $$tem_magnification_measured  
$#ctf_bfactor: $$ctf_bfactor  
$#ctf_snr_max: $$ctf_snr_max  
$#ctf_ampcont: $$ctf_ampcont
""",
  'modifytime': '2011-12-08T11:39:12Z',
  'modifyuser': 'root',
  'name': 'micrograph',
  'owner': 'root',
  'parents': ['image_capture'],
  'private': 0,
  'typicalchld': ['scan'],
  'uri': None,
  'views': { 'recname': """Micrograph $$id_micrograph""",
             'tabularview': """$$id_micrograph $$ctf_defocus_set $$ctf_defocus_measured $$tem_magnification_set $$ctf_bfactor $$time_exposure_tem  $$tem_dose_rate $$assess_image_quality $@childcount(scan)"""}}
]


if __name__ == "__main__":
	if os.path.exists(sys.argv[1]):
		print "Warning: File %s exists"%sys.argv[1]
	print "Saving output to %s"%sys.argv[1]
	# print "ParamDefs:"
	# print set([i.get('name') for i in paramdefs])
	# print "RecordDefs:"
	# print set([i.get('name') for i in recorddefs])

	with open(sys.argv[1],'w') as f:
		for pd in paramdefs:
			pd['keytype'] = 'paramdef'
			pd['uri'] = 'http://ncmidb.bcm.edu/paramdef/%s'%pd['name']
			print pd['name']
			f.write(json.dumps(pd)+"\n")
		for rd in recorddefs:
			rd['keytype'] = 'recorddef'
			rd['uri'] = 'http://ncmidb.bcm.edu/recorddef/%s'%rd['name']
			print rd['name']
			f.write(json.dumps(rd)+"\n")


