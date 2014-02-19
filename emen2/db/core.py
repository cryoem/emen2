import sys
import emen2.db.dump

core = [
# Core ParamDefs
{"name": "root", "keytype": "paramdef", "parents": [], "vartype": "none", "desc_short": "Root parameter"},
{"name": "core", "keytype": "paramdef", "parents": ["root"], "vartype": "none", "desc_short": "Core parameters"},
{"name": "keytype", "keytype": "paramdef", "parents": ["core"], "vartype": "none", "desc_short": "Type", "desc_long": "Object type"},
{"name": "name", "keytype": "paramdef", "parents": ["core"], "vartype": "none", "desc_short": "ID", "desc_long": "Object ID"},
{"name": "keywords", "keytype": "paramdef", "vartype": "keywords", "parents": ["core"], "desc_short": "Keywords"},

# Common
{"name": "creator", "keytype": "paramdef","parents": ["core"], "vartype": "user", "desc_short": "Created by", "desc_long": "The user that originally created the record"},
{"name": "creationtime", "keytype": "paramdef","parents": ["core"], "vartype": "datetime", "desc_short": "Creation time", "desc_long": "Timestamp of original record creation"},
{"name": "modifyuser", "keytype": "paramdef", "parents": ["core"], "vartype": "user", "desc_short": "Modified by", "desc_long": "The user that last changed the record"},
{"name": "modifytime", "keytype": "paramdef","parents": ["core"], "vartype": "datetime", "desc_short": "Modification time", "desc_long": "Timestamp of last modification"},
{"name": "uri", "keytype": "paramdef","parents": ["core"], "vartype": "uri", "desc_short": "URI", "desc_long": "Resource location of an imported object"},
{"name": "permissions", "keytype": "paramdef","parents": ["core"], "vartype": "acl", "desc_short": "Permissions"},
{"name": "hidden", "keytype": "paramdef", "vartype": "boolean", "parents": ["core"], "desc_short": "Hidden"},

# Links
{"name": "record", "keytype": "paramdef", "parents": ["core"], "vartype": "record", "desc_short": "Record"},
{"name": "paramdef", "keytype": "paramdef", "parents": ["core"], "vartype": "paramdef", "desc_short": "Parameter"},
{"name": "user", "keytype": "paramdef","parents": ["core"], "vartype": "user", "desc_short": "User"},
{"name": "group", "keytype": "paramdef","parents": ["core"], "vartype": "group", "desc_short": "Group"},
{"name": "groups", "keytype": "paramdef","parents": ["core"], "vartype": "group", "iter": True, "desc_short": "Groups"},
{"name": "binary", "keytype": "paramdef","parents": ["core"], "vartype": "binary", "desc_short": "Binary"},
{"name": "parents", "keytype": "paramdef","parents": ["core"], "vartype": "link", "desc_short": "Parents"},
{"name": "children", "keytype": "paramdef","parents": ["core"], "vartype": "link", "desc_short": "Children"},

# ParamDef
{"name": "vartype", "keytype": "paramdef", "parents": ["core"], "vartype": "string", "desc_short": "Value type"},
{"name": "iter", "keytype": "paramdef", "parents": ["core"], "vartype": "boolean", "desc_short": "Iterable"},
{"name": "property", "keytype": "paramdef", "parents": ["core"], "vartype": "string", "desc_short": "Physical property"},
{"name": "defaultunits", "keytype": "paramdef", "parents": ["core"], "vartype": "string", "desc_short": "Default units"},
{"name": "indexed", "keytype": "paramdef", "parents": ["core"], "vartype": "boolean", "desc_short": "Indexed"},
{"name": "choices", "iter": True, "keytype": "paramdef", "parents": ["core"], "vartype": "string", "desc_short": "Choices"},
{"name": "desc_short", "keytype": "paramdef", "parents": ["core"], "vartype": "string", "desc_short": "Short description"},
{"name": "desc_long", "keytype": "paramdef", "parents": ["core"], "vartype": "text", "desc_short": "Long description"},
{"name": "privacy", "keytype": "paramdef", "parents": ["core"], "vartype": "int", "desc_short": "User privacy"},

# RecordDef
{"name": "views", "keytype": "paramdef", "parents": ["core"], "vartype": "dict", "desc_short": "Views"},
{"name": "mainview", "keytype": "paramdef", "parents": ["core"], "vartype": "text", "desc_short": "Main view"},
{"name": "typicalchld", "iter": True, "keytype": "paramdef", "parents": ["core"], "vartype": "paramdef", "desc_short": "Typical children"},

# User
{"name": "email", "keytype": "paramdef","parents": ["core"], "vartype": "email", "desc_short": "Email"},
{"name": "disabled", "keytype": "paramdef", "parents": ["core"], "vartype": "boolean", "desc_short": "Disabled account"},
{"name": "password", "keytype": "paramdef", "parents": ["core"], "vartype": "password", "desc_short": "Password"},
{"name": "name_first", "keytype": "paramdef", "parents": ["core"], "vartype": "string", "desc_short": "First name"},
{"name": "name_middle", "keytype": "paramdef", "parents": ["core"], "vartype": "string", "desc_short": "Middle name"},
{"name": "name_last", "keytype": "paramdef", "parents": ["core"], "vartype": "string", "desc_short": "Last name"},
{"name": "displayname", "keytype": "paramdef","parents": ["core"], "vartype": "string", "desc_short": "Display name"},
{"name": "secret", "keytype": "paramdef","parents": ["core"], "vartype": "none", "desc_short": "Hidden"},
{"name": "signupinfo", "keytype": "paramdef","parents": ["core"], "vartype": "none", "desc_short": "Signup Details"},

# Record
{"name": "rectype", "keytype": "paramdef", "parents": ["core"], "vartype": "recorddef", "desc_short": "Protocol"},
{"name": "history", "keytype": "paramdef", "parents": ["core"], "vartype": "history", "desc_short": "History"},
{"name": "comments", "keytype": "paramdef", "parents": ["core"], "vartype": "comments", "desc_short": "Comments"},

# Binary
{"name": "filename", "keytype": "paramdef", "parents": ["core"], "vartype": "string", "desc_short": "Filename"},
{"name": "filesize", "keytype": "paramdef", "parents": ["core"], "vartype": "int", "property": "bytes", "defaultunits": "B", "desc_short": "Filesize"},
{"name": "md5", "keytype": "paramdef", "parents": ["core"], "vartype": "md5", "desc_short": "MD5 Checksum"},
{"name": "file_binary", "keytype": "paramdef", "parents": ["core"], "vartype": "binary", "iter": True, "desc_short": "Attachments"},
{"name": "compress", "keytype": "paramdef", "parents":["core"], "vartype": "string", "desc_short": "Compressed format"},

# Context
{"name": "host", "keytype": "paramdef", "parents": ["core"], "vartype": "string", "desc_short": "Host"},

# Core RecordDefs
{"name":"root", "keytype":"recorddef", "mainview":"# {{desc_short}}  \n{{desc_long}} \n", "views":{"recname":"Root: {{desc_short}}", "banner":"{{desc_long}}"}, "desc_short":"Root protocol"}
]

# For base RecordDefs
base = [
{"name": "base", "keytype": "paramdef", "parents": ["root"], "vartype": "none", "desc_short": "Parameters for base protocols"},
{"name": "performed_by", "keytype": "paramdef", "parents": ["base"], "vartype": "user", "desc_short": "Performed by"},
{"name": "date_occurred", "keytype": "paramdef", "parents": ["base"], "vartype": "datetime", "desc_short": "Date occurred"},
{"name": "name_folder", "keytype": "paramdef", "vartype": "string", "parents": ["base"], "desc_short": "Folder name"},
{"name": "folder_description", "keytype": "paramdef", "vartype": "string", "parents": ["base"], "desc_short": "Description"},
{'desc_short': 'Project title', 'keytype': 'paramdef', 'name': 'name_project', 'parents': ['base'], 'vartype': 'string'},

{'choices': ['Rejected',
           'Indefinite Hold',
           'Wait for Sample',
           'Complete',
           'Screening',
           'Analysis',
           'Imaging',
           'Manuscript Prep.'],
'desc_long': 'The current state of this project',
'desc_short': 'Project status',
'keytype': 'paramdef',
'name': 'project_status',
'parents': ['base'],
'vartype': 'choice'},

{'desc_long': 'This person is responsible for the next progress in this project. It should be updated to reflect who is currently responsible for periodic progress updates. This field should not relate to authorship expectations.',
'desc_short': 'Current workflow',
'iter': True,
'keytype': 'paramdef',
'name': 'project_block',
'parents': ['base'],
'vartype': 'user'},

{'desc_long': 'Principal investigator',
'desc_short': 'PI',
'iter': True,
'keytype': 'paramdef',
'name': 'name_pi',
'parents': ['base'],
'vartype': 'user'},

{'desc_long': 'Project Investigators',
'desc_short': 'Investigators',
'iter': True,
'keytype': 'paramdef',
'name': 'project_investigators',
'parents': ['base'],
'vartype': 'user'},

{'choices': ['N/A', 'Service', 'Collaborative', 'Core'],'desc_long': 'Project type',
'desc_short': 'Project type',
'keytype': 'paramdef',
'name': 'project_type',
'parents': ['base'],
'vartype': 'choice'},

{
'desc_short': 'Project goals',
'keytype': 'paramdef',
'name': 'description_goals',
'parents': ['base'],
'vartype': 'text'
},

{
'desc_short': 'Background information',
'keytype': 'paramdef',
'name': 'description_background',
'parents': ['base'],
'vartype': 'text'
},

{"name": "person_photo", "keytype": "paramdef", "vartype": "binary", "parents": ["base"], "desc_short": "Profile photo"},
{"name": "name_group", "keytype": "paramdef", "parents": ["base"], "vartype": "string", "desc_short": "Group name"},
{"name": "department", "keytype": "paramdef", "parents": ["base"], "vartype": "string", "desc_short": "Department"},
{"name": "institution", "keytype": "paramdef", "parents": ["base"], "vartype": "string", "desc_short": "Institution"},
{"name": "name_contact", "keytype": "paramdef", "parents": ["base"], "vartype": "string", "desc_short": "Contact person"},
{"name": "phone", "keytype": "paramdef", "parents": ["base"], "vartype": "string", "desc_short": "Phone"},
{"name": "website", "keytype": "paramdef", "parents": ["base"], "vartype": "uri", "desc_short": "Website"},

# Base RecordDefs
{"name":"base", "keytype":"recorddef", "mainview":"Base protocols.", "desc_short":"Base protocols", "parents":["root"]},
{"name":"experiments", "keytype":"recorddef", "mainview":"Experimental protocols.", "desc_short":"Experimental protocols", "parents":["root"]},

{
'name': 'person',
'desc_long': 'Contact details for a person. Do not edit directly.',
'desc_short': 'Person',
'keytype': 'recorddef',
'mainview': """
# Person
Do not edit directly. Use the user profile view.
""",
'parents': ['base'],
'views': { 'recname': 'Person: {{name_first}} {{name_last}}'}
},

{
'desc_long': 'A group group or organization',
'desc_short': 'Group',
'keytype': 'recorddef',
'mainview': """
# $#name_group: $$name_group  

$#institution: $$institution    
$#name_contact: $$name_contact  
$#phone: $$phone    
$#website: $$website  
$#email: $$email     
""",
'name': 'group',
'parents': ['base'],
'views': { 'recname': """$$name_group""",
         'tabularview': """$$name_group $$institution $$name_contact"""}
},

{
'desc_long': 'A folder, which is useful as a general purpose organization device.',
'desc_short': 'Folder',
'keytype': 'recorddef',
'mainview': """
# Folder: {{name_folder}}  
Description: {{folder_description}}
""",
'name': 'folder',
'parents': ['base'],
'private': False,
'typicalchld': [],
'views': { 'banner': '{{folder_description}}', 'recname': """{{name_folder}}""", 'tabularview': """{{name_folder}} {{folder_description}}"""}
},

{
'name': 'project',
'parents': ['base'],
'desc_long': 'A project. This should be used in a broad sense, such as an entire collaboration. For each specific goal, an additional child project should be created. Parent will usually be a group record.',
'desc_short': 'Project',
'keytype': 'recorddef',
'mainview': """
# {{name_project?}}: {{name_project}}  
{{project_status?}}: {{project_status}}  
{{project_block?}}: {{project_block}}  

{{name_pi?}}: {{name_pi}}  
{{project_investigators?}}: {{project_investigators}}  
{{project_type?}}: {{project_type}}  

# Project Description  
{{description_goals?}}: {{description_goals}}  
{{description_background?}}: {{description_background}}  
""",
'private': 0,
'typicalchld': [ 'project', 'labnotebook', 'grid_imaging', 'publication', 'publication_abstract', 'purification', 'movie', 'volume', 'project_meeting', 'reference', 'manuscript', 'progress_report'],
'views': { 'recname': """Project: {{name_project}} ({{name_pi}})""", 'tabularview': """{{name_project}} {{name_pi}} {{project_investigators}} {{project_status}} {{project_block}} {{childcount()}}"""}
}
]

if __name__ == "__main__":
    emen2.db.dump.dump_json('core.json', items=core, uri="http://ncmidb.bcm.edu")
    emen2.db.dump.dump_json('base.json', items=base, uri="http://ncmidb.bcm.edu")


