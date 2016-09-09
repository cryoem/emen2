import sys
import emen2.db.dump

core_paramdefs = [
# Core ParamDefs
{"name": "root", "keytype": "paramdef", "parents": [], "vartype": "none", "desc_short": "Root parameter"},
{"name": "core", "keytype": "paramdef", "parents": ["root"], "vartype": "none", "desc_short": "Core parameters"},
{"name": "base", "keytype": "paramdef", "parents": ["root"], "vartype": "none", "desc_short": "Parameters for base protocols"},

# Links
{"name": "record", "keytype": "paramdef", "parents": ["core"], "vartype": "record", "desc_short": "Record"},
{"name": "paramdef", "keytype": "paramdef", "parents": ["core"], "vartype": "paramdef", "desc_short": "Parameter"},
{"name": "user", "keytype": "paramdef","parents": ["core"], "vartype": "user", "desc_short": "User"},
{"name": "group", "keytype": "paramdef","parents": ["core"], "vartype": "group", "desc_short": "Group"},
{"name": "groups", "keytype": "paramdef","parents": ["core"], "vartype": "group", "iter": True, "desc_short": "Groups"},
{"name": "binary", "keytype": "paramdef","parents": ["core"], "vartype": "binary", "desc_short": "Binary"},

# Common
{"name": "keytype", "immutable": True, "keytype": "paramdef", "parents": ["core"], "indexed": False, "vartype": "string", "desc_short": "Type", "desc_long": "Object type"},
{"name": "name", "immutable": True, "keytype": "paramdef", "parents": ["core"], "indexed": False, "vartype": "string", "desc_short": "ID", "desc_long": "Object ID"},
{"name": "creator", "immutable": True, "keytype": "paramdef","parents": ["core"], "vartype": "user", "desc_short": "Created by", "desc_long": "The user that originally created the record"},
{"name": "creationtime", "immutable": True, "keytype": "paramdef","parents": ["core"], "vartype": "datetime", "desc_short": "Creation time", "desc_long": "Timestamp of original record creation"},
{"name": "modifytime", "immutable": True, "keytype": "paramdef","parents": ["core"], "vartype": "datetime", "desc_short": "Modification time", "desc_long": "Timestamp of last modification"},
{"name": "modifyuser", "immutable": True, "keytype": "paramdef", "parents": ["core"], "vartype": "user", "desc_short": "Modified by", "desc_long": "The user that last changed the record"},
{"name": "uri", "immutable": True, "keytype": "paramdef","parents": ["core"], "vartype": "uri", "desc_short": "Resource location", "desc_long": "Resource location of an imported object"},
{"name": "parents", "keytype": "paramdef","parents": ["core"], "vartype": "link", "iter": True, "desc_short": "Parents"},
{"name": "children", "keytype": "paramdef","parents": ["core"], "vartype": "link", "iter": True, "desc_short": "Children"},
{"name": "permissions", "keytype": "paramdef","parents": ["core"], "vartype": "acl", "desc_short": "Permissions"},
{"name": "keywords", "keytype": "paramdef","parents": ["core"], "vartype": "keywords", "desc_short": "Keywords"},

# ParamDef
{"name": "vartype", "immutable": True, "keytype": "paramdef", "parents": ["core"], "vartype": "string", "desc_short": "Value type"},
{"name": "immutable", "immutable": True, "keytype": "paramdef", "parents": ["core"], "vartype": "boolean", "desc_short": "Default units"},
{"name": "iter", "immutable": True, "keytype": "paramdef", "parents": ["core"], "vartype": "boolean", "desc_short": "Iterable"},
{"name": "controlhint", "keytype": "paramdef","parents": ["core"], "vartype": "string", "desc_short": "Control hint"},
{"name": "desc_short", "keytype": "paramdef", "parents": ["core"], "vartype": "string", "desc_short": "Short description"},
{"name": "desc_long", "keytype": "paramdef", "parents": ["core"], "vartype": "text", "desc_short": "Long description"},
{"name": "property", "keytype": "paramdef", "parents": ["core"], "vartype": "string", "desc_short": "Physical property"},
{"name": "defaultunits", "keytype": "paramdef", "parents": ["core"], "vartype": "string", "desc_short": "Default units"},
{"name": "indexed", "keytype": "paramdef", "parents": ["core"], "vartype": "boolean", "desc_short": "Indexed"},
{"name": "choices", "iter": True, "keytype": "paramdef", "parents": ["core"], "vartype": "string", "desc_short": "Choices"},

# RecordDef
{"name": "views", "keytype": "paramdef", "parents": ["core"], "vartype": "dict", "desc_short": "Views"},
{"name": "mainview", "keytype": "paramdef", "parents": ["core"], "vartype": "text", "desc_short": "Main view"},
{"name": "private", "keytype": "paramdef", "parents": ["core"], "vartype": "boolean", "desc_short": "Private"},
{"name": "typicalchld", "iter": True, "keytype": "paramdef", "parents": ["core"], "vartype": "string", "desc_short": "Typical children"},

# User
{"name": "email", "keytype": "paramdef","parents": ["core"], "vartype": "string", "desc_short": "Email"},
{"name": "privacy", "keytype": "paramdef", "parents": ["core"], "vartype": "int", "desc_short": "User privacy"},
{"name": "disabled", "keytype": "paramdef", "parents": ["core"], "vartype": "boolean", "desc_short": "Disabled account"},
# ... these just exist for validation.
{"name": "displayname", "keytype": "paramdef", "parents": ["core"], "vartype": "string", "desc_short": "Display name"},
{"name": "password", "keytype": "paramdef", "parents": ["core"], "vartype": "string", "desc_short": "Password"},
{"name": "signupinfo", "keytype": "paramdef", "parents": ["core"], "vartype": "dict", "desc_short": "Signup Info"},

# Record
{"name": "rectype", "immutable": True, "keytype": "paramdef","parents": ["core"], "vartype": "recorddef", "desc_short": "Protocol"},
{"name": "history", "immutable": True, "keytype": "paramdef","parents": ["core"], "vartype": "history", "desc_short": "History"},
{"name": "comments", "keytype": "paramdef","parents": ["core"], "vartype": "comments", "desc_short": "Comments", "iter": True},

# Binary
{"name": "filename", "keytype": "paramdef", "parents": ["core"], "vartype": "string", "desc_short": "Filename"},
{"name": "filesize", "keytype": "paramdef", "parents": ["core"], "vartype": "int", "property": "bytes", "defaultunits": "B", "desc_short": "Filesize"},
{"name": "filesize_compress", "keytype": "paramdef", "parents": ["core"], "vartype": "int", "property": "bytes", "defaultunits": "B", "desc_short": "Filesize (compressed)"},
{"name": "md5", "keytype": "paramdef", "parents": ["core"], "vartype": "md5", "desc_short": "MD5 Checksum"},
{"name": "md5_compress", "keytype": "paramdef", "parents": ["core"], "vartype": "md5", "desc_short": "MD5 Checksum (compressed)"},
{"name": "file_binary", "keytype": "paramdef", "parents": ["core"], "vartype": "binary", "iter": True, "desc_short": "Attachments"},
{"name": "compress", "keytype": "paramdef", "parents":["core"], "vartype": "string", "desc_short": "Compressed format"}
]

base_paramdefs = [
# For base RecordDefs
{"name": "name_first", "keytype": "paramdef", "parents": ["base"], "vartype": "string", "desc_short": "First name"},
{"name": "name_middle", "keytype": "paramdef", "parents": ["base"], "vartype": "string", "desc_short": "Middle name"},
{"name": "name_last", "keytype": "paramdef", "parents": ["base"], "vartype": "string", "desc_short": "Last name"},
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
'parents': ['textual_descriptions', 'biology_of_project'],
'vartype': 'text'
},

{"name": "name_group", "keytype": "paramdef", "parents": ["base"], "vartype": "string", "desc_short": "Group name"},
{"name": "institution", "keytype": "paramdef", "parents": ["base"], "vartype": "string", "desc_short": "Institution"},
{"name": "name_contact", "keytype": "paramdef", "parents": ["base"], "vartype": "string", "desc_short": "Contact person"},
{"name": "phone", "keytype": "paramdef", "parents": ["base"], "vartype": "string", "desc_short": "Phone"},
{"name": "website", "keytype": "paramdef", "parents": ["base"], "vartype": "string", "desc_short": "Website"},
]





core_recorddefs = [
{"name":"root", "keytype":"recorddef", "mainview":"# {{desc_short}}  \n{{desc_long}} \n", "views":{"recname":"Root: {{desc_short}}", "banner":"{{desc_long}}"}, "desc_short":"Root protocol"}
]

base_recorddefs = [
{"name":"base", "keytype":"recorddef", "mainview":"Core protocols.", "desc_short":"Core protocols", "parents":["root"]},
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
'parents': ['core'],
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
'parents': ['core'],
'views': { 'recname': """$$name_group""",
         'tabularview': """$$name_group $$institution $$name_contact"""}},


{
'desc_long': 'A folder, which is useful as a general purpose organization device.',
'desc_short': 'Folder',
'keytype': 'recorddef',
'mainview': """
# Folder: {{desc_short}}  
Description: {desc_long}  
""",
'name': 'folder',
'parents': ['core'],
'private': False,
'typicalchld': [],
'views': { 'banner': '{{desc_long}}', 'recname': """{{desc_short}}""", 'tabularview': """Folder: {{desc_short}}"""}
},

{
'name': 'project',
'parents': ['core'],
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
    emen2.db.dump.dump_json(sys.argv[1], items=core_paramdefs+base_paramdefs+core_recorddefs+base_recorddefs, uri="http://ncmidb.bcm.edu")

