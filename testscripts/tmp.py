#begin parameter: project_title
project_title =  Database.ParamDef()
project_title.name = 'project_title'
project_title.vartype = 'string'
project_title.desc_short = '''project title'''
db.addparamdef(project_title,ctxid)
#end parameter: project_title

#begin parameter: project_dates
project_dates =  Database.ParamDef()
project_dates.name = 'project_dates'
project_dates.vartype = 'string'
project_dates.desc_short = '''project dates'''
db.addparamdef(project_dates,ctxid)
#end parameter: project_dates

#begin parameter: project_type
project_type =  Database.ParamDef()
project_type.name = 'project_type'
project_type.vartype = 'string'
project_type.desc_short = '''type of project'''
db.addparamdef(project_type,ctxid)
#end parameter: project_type

#begin parameter: project_description
project_description =  Database.ParamDef()
project_description.name = 'project_description'
project_description.vartype = 'text'
project_description.desc_short = '''project description'''
db.addparamdef(project_description,ctxid)
#end parameter: project_description

#begin parameter: project_reprints
project_reprints =  Database.ParamDef()
project_reprints.name = 'project_reprints'
project_reprints.vartype = 'text'
project_reprints.desc_short = '''reprints/publications of the project'''
db.addparamdef(project_reprints,ctxid)
#end parameter: project_reprints

#begin record definition: project
project = Database.RecordDef()
project.name = 'project'
project.mainview = """$$project_title $$project_dates $$project_type $$project_description $$project_reprints"""
project.views['tabularview'] = """$$project_title"""
project.views['defaultview'] = """$$project_title"""
project.views['recname'] = """$$project_title"""
db.addrecorddef(project,ctxid)
#end record definition: project

#begin parameter: grant_agency_name
grant_agency_name =  Database.ParamDef()
grant_agency_name.name = 'grant_agency_name'
grant_agency_name.vartype = 'string'
grant_agency_name.desc_short = '''Name of the Grant Agency'''
db.addparamdef(grant_agency_name,ctxid)
#end parameter: grant_agency_name

#begin parameter: grant_number
grant_number =  Database.ParamDef()
grant_number.name = 'grant_number'
grant_number.vartype = 'integer'
grant_number.desc_short = '''Grant Number'''
db.addparamdef(grant_number,ctxid)
#end parameter: grant_number

#begin parameter: grant_title
grant_title =  Database.ParamDef()
grant_title.name = 'grant_title'
grant_title.vartype = 'string'
grant_title.desc_short = '''Grant Title'''
db.addparamdef(grant_title,ctxid)
#end parameter: grant_title

#begin parameter: grant_duration
grant_duration =  Database.ParamDef()
grant_duration.name = 'grant_duration'
grant_duration.vartype = 'string'
grant_duration.desc_short = '''Grant Duration'''
db.addparamdef(grant_duration,ctxid)
#end parameter: grant_duration

#begin parameter: grant_total_cost
grant_total_cost =  Database.ParamDef()
grant_total_cost.name = 'grant_total_cost'
grant_total_cost.vartype = 'float'
grant_total_cost.desc_short = '''Grant Total Cost'''
db.addparamdef(grant_total_cost,ctxid)
#end parameter: grant_total_cost

#begin record definition: grant
grant = Database.RecordDef()
grant.name = 'grant'
grant.mainview = """$$grant_agency_name $$grant_number $$grant_title $$grant_duration $$grant_total_cost"""
grant.views['tabularview'] = """$$grant_title from $$grant_agency_name"""
grant.views['defaultview'] = """$$grant_title"""
grant.views['recname'] = """$$grant_title"""
db.addrecorddef(grant,ctxid)
#end record definition: grant

#begin parameter: investigator_name
investigator_name =  Database.ParamDef()
investigator_name.name = 'investigator_name'
investigator_name.vartype = 'string'
investigator_name.desc_short = '''Name'''
db.addparamdef(investigator_name,ctxid)
#end parameter: investigator_name

#begin parameter: investigator_degrees
investigator_degrees =  Database.ParamDef()
investigator_degrees.name = 'investigator_degrees'
investigator_degrees.vartype = 'string'
investigator_degrees.desc_short = '''Degrees'''
db.addparamdef(investigator_degrees,ctxid)
#end parameter: investigator_degrees

#begin parameter: investigator_department
investigator_department =  Database.ParamDef()
investigator_department.name = 'investigator_department'
investigator_department.vartype = 'string'
investigator_department.desc_short = '''Department'''
db.addparamdef(investigator_department,ctxid)
#end parameter: investigator_department

#begin parameter: investigator_institution
investigator_institution =  Database.ParamDef()
investigator_institution.name = 'investigator_institution'
investigator_institution.vartype = 'string'
investigator_institution.desc_short = '''Institution'''
db.addparamdef(investigator_institution,ctxid)
#end parameter: investigator_institution

#begin parameter: investigator_phone
investigator_phone =  Database.ParamDef()
investigator_phone.name = 'investigator_phone'
investigator_phone.vartype = 'string'
investigator_phone.desc_short = '''Phone Number'''
db.addparamdef(investigator_phone,ctxid)
#end parameter: investigator_phone

#begin parameter: investigator_fax
investigator_fax =  Database.ParamDef()
investigator_fax.name = 'investigator_fax'
investigator_fax.vartype = 'string'
investigator_fax.desc_short = '''Fax'''
db.addparamdef(investigator_fax,ctxid)
#end parameter: investigator_fax

#begin record definition: investigator
investigator = Database.RecordDef()
investigator.name = 'investigator'
investigator.mainview = """$$investigator_name $$investigator_degrees $$investigator_department $$investigator_institution $$investigator_phone $$investigator_fax"""
investigator.views['tabularview'] = """$$investigator_name"""
investigator.views['defaultview'] = """$$investigator_name"""
investigator.views['recname'] = """$$investigator_name"""
db.addrecorddef(investigator,ctxid)
#end record definition: investigator

#begin parameter: address_top
address_top =  Database.ParamDef()
address_top.name = 'address_top'
address_top.vartype = 'string'
address_top.desc_short = '''Address Top Line(s)'''
db.addparamdef(address_top,ctxid)
#end parameter: address_top

#begin parameter: address_city
address_city =  Database.ParamDef()
address_city.name = 'address_city'
address_city.vartype = 'string'
address_city.desc_short = '''City'''
db.addparamdef(address_city,ctxid)
#end parameter: address_city

#begin parameter: address_state
address_state =  Database.ParamDef()
address_state.name = 'address_state'
address_state.vartype = 'string'
address_state.desc_short = '''State'''
db.addparamdef(address_state,ctxid)
#end parameter: address_state

#begin parameter: address_zip
address_zip =  Database.ParamDef()
address_zip.name = 'address_zip'
address_zip.vartype = 'integer'
address_zip.desc_short = '''Zipcode'''
db.addparamdef(address_zip,ctxid)
#end parameter: address_zip

#begin parameter: address_country
address_country =  Database.ParamDef()
address_country.name = 'address_country'
address_country.vartype = 'string'
address_country.desc_short = '''Country'''
db.addparamdef(address_country,ctxid)
#end parameter: address_country

#begin record definition: address
address = Database.RecordDef()
address.name = 'address'
address.mainview = """$$address_top<br />$$address_city,$$address_state $$address_zip<br />$$address_country"""
address.views['tabularview'] = """$$address_top"""
address.views['defaultview'] = """$$address_top"""
address.views['recname'] = """$$address_top"""
db.addrecorddef(address,ctxid)
#end record definition: address
