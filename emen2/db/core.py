import sys
import emen2.db.dump

#######################################
# Core
#######################################

core_paramdefs = [
    # Root
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
    {"name": "host", "keytype": "paramdef", "parents": ["core"], "vartype": "string", "desc_short": "Host"}
]

# Core RecordDefs
core_recorddefs = [
    {"name":"root", "keytype":"recorddef", "mainview":"# {{desc_short}}  \n{{desc_long}} \n", "views":{"recname":"Root: {{desc_short}}", "banner":"{{desc_long}}"}, "desc_short":"Root protocol"}   
]



#######################################
# Base
#######################################
base_paramdefs = [
    {"name": "base", "vartype": "none", "keytype": "paramdef", "parents": ["root"], "desc_short": "Parameters for base protocols"},
    {"name": "academic_degrees", "vartype": "string", "iter":True, "keytype": "paramdef", "parents": ["base"], "desc_short": "Academic degrees"},
    {"name": "address_city", "vartype": "string", "keytype": "paramdef", "parents": ["base"], "desc_short": "City"},
    {"name": "address_state", "vartype": "string", "keytype": "paramdef", "parents": ["base"], "desc_short": "State"},
    {"name": "address_street", "vartype": "string", "keytype": "paramdef", "parents": ["base"], "desc_short": "Street address"},
    {"name": "address_street2", "vartype": "string", "keytype": "paramdef", "parents": ["base"], "desc_short": "Street address (2)"},
    {"name": "address_zipcode", "vartype": "string", "keytype": "paramdef", "parents": ["base"], "desc_short": "Zip code"},
    {"name": "address_international", "vartype": "string", "keytype": "paramdef", "parents": ["base"], "desc_short": "International address"},
    {"name": "date_end", "vartype": "datetime", "keytype": "paramdef", "parents": ["base"], "desc_short": "Date ended"},
    {"name": "date_occurred", "vartype": "datetime", "keytype": "paramdef", "parents": ["base"], "desc_short": "Date occurred"},
    {"name": "date_start", "vartype": "datetime", "keytype": "paramdef", "parents": ["base"], "desc_short": "Date started"},
    {"name": "department", "vartype": "string", "keytype": "paramdef", "parents": ["base"], "desc_short": "Department"},
    {"name": "description_background", "vartype": "text", "keytype": "paramdef", "parents": ["base"], "desc_short": "Background information"},
    {"name": "description_goals", "vartype": "text", "keytype": "paramdef", "parents": ["base"], "desc_short": "Project goals"},
    {"name": "file_binary_image", "vartype": "binary", "keytype": "paramdef", "parents": ["base"], "desc_short": "Image attachment"},
    {"name": "folder_description", "parents": ["base"], "keytype": "paramdef", "vartype": "string", "desc_short": "Description"},
    {"name": "institution", "vartype": "string", "keytype": "paramdef", "parents": ["base"], "desc_short": "Institution"},
    {"name": "name_contact", "vartype": "string", "keytype": "paramdef", "parents": ["base"], "desc_short": "Contact person"},
    {"name": "name_folder", "parents": ["base"], "keytype": "paramdef", "vartype": "string", "desc_short": "Folder name"},
    {"name": "name_group", "vartype": "string", "keytype": "paramdef", "parents": ["base"], "desc_short": "Group name"},
    {"name": "name_pi", "desc_long": "Principal investigator", "keytype": "paramdef", "iter": True, "parents": ["base"], "vartype": "user", "desc_short": "PI"},
    {"name": "name_project", "vartype": "string", "keytype": "paramdef", "parents": ["base"], "desc_short": "Project title"},
    {"name": "performed_by", "vartype": "user", "keytype": "paramdef", "parents": ["base"], "desc_short": "Performed by"},
    {"name": "person_photo", "parents": ["base"], "keytype": "paramdef", "vartype": "binary", "desc_short": "Profile photo"},
    {"name": "phone_fax", "vartype": "string", "keytype": "paramdef", "parents": ["base"], "desc_short": "Phone (fax)"},
    {"name": "project_block", "desc_long": "This person is responsible for the next progress in this project. It should be updated to reflect who is currently responsible for periodic progress updates. This field should not relate to authorship expectations.", "keytype": "paramdef", "iter": True, "parents": ["base"], "vartype": "user", "desc_short": "Current workflow"},
    {"name": "project_investigators", "desc_long": "Project Investigators", "keytype": "paramdef", "iter": True, "parents": ["base"], "vartype": "user", "desc_short": "Investigators"},
    {"name": "project_status", "keytype": "paramdef", "parents": ["base"], "vartype": "choice", "desc_short": "Project status", "desc_long": "The current state of this project", "choices": ["Rejected", "Indefinite Hold", "Wait for Sample", "Complete", "Screening", "Analysis", "Imaging", "Manuscript Prep.", "In Progress"]},
    {"name": "project_type", "keytype": "paramdef", "choices": ["N/A", "Service", "Collaborative", "Core", "Unkown"], "parents": ["base"], "vartype": "choice", "desc_short": "Project type", "desc_long": "Project type"},
    {"name": "website", "vartype": "uri", "keytype": "paramdef", "parents": ["base"], "desc_short": "Website"},
]


base_recorddefs = [
    # Base RecordDefs
    {"name":"base", "keytype":"recorddef", "mainview":"Base protocols.", "desc_short":"Base protocols", "parents":["root"]},
    {"name":"experiments", "keytype":"recorddef", "mainview":"Experimental protocols.", "desc_short":"Experimental protocols", "parents":["root"]},
    {
        "name": "person",
        "desc_long": "Contact details for a person. Do not edit directly.",
        "desc_short": "Person",
        "keytype": "recorddef",
        "mainview": """
        # Person
        Do not edit directly. Use the user profile view.
        """,
        "parents": ["base"],
        "views": { "recname": "Person: {{name_first}} {{name_last}}"}
    },
    {
        "desc_long": "A group group or organization",
        "desc_short": "Group",
        "keytype": "recorddef",
        "mainview": """
        # $#name_group: $$name_group  

        $#institution: $$institution    
        $#name_contact: $$name_contact  
        $#phone: $$phone    
        $#website: $$website  
        $#email: $$email     
        """,
        "name": "group",
        "parents": ["base"],
        "views": { "recname": """$$name_group""",
                 "tabularview": """$$name_group $$institution $$name_contact"""}
    },
    {
        "name": "folder",        
        "desc_long": "A folder, which is useful as a general purpose organization device.",
        "desc_short": "Folder",
        "keytype": "recorddef",
        "mainview": """
        # Folder: {{name_folder}}  
        Description: {{folder_description}}
        """,
        "parents": ["base"],
        "typicalchld": [],
        "views": { "banner": "{{folder_description}}", "recname": """{{name_folder}}""", "tabularview": """{{name_folder}} {{folder_description}}"""}
    },
    {
        "name": "project",
        "parents": ["base"],
        "desc_long": "A project. This should be used in a broad sense, such as an entire collaboration. For each specific goal, an additional child project should be created. Parent will usually be a group record.",
        "desc_short": "Project",
        "keytype": "recorddef",
        "mainview": """
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
        "typicalchld": [ "project", "labnotebook", "grid_imaging", "publication", "publication_abstract", "purification", "movie", "volume", "project_meeting", "reference", "manuscript", "progress_report"],
        "views": { "recname": """Project: {{name_project}} ({{name_pi}})""", "tabularview": """{{name_project}} {{name_pi}} {{project_investigators}} {{project_status}} {{project_block}} {{childcount()}}"""}
    }
]

if __name__ == "__main__":
    emen2.db.dump.dump_json("core.json", items=core_paramdefs+core_recorddefs, uri="http://ncmidb.bcm.edu")
    emen2.db.dump.dump_json("base.json", items=base_paramdefs+base_recorddefs, uri="http://ncmidb.bcm.edu")


