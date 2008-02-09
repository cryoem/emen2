from test import *

#begin parameter: template_name
template_name =  Database.ParamDef()
template_name.name = 'template_name'
template_name.vartype = 'string'
template_name.desc_short = '''the template of the current record'''
db.addparamdef(template_name,ctxid)
#end parameter: template_name

#begin parameter: event_name
event_name =  Database.ParamDef()
event_name.name = 'event_name'
event_name.vartype = 'string'
event_name.desc_short = '''The name of the event'''
db.addparamdef(event_name,ctxid)
#end parameter: event_name

#begin parameter: event_date
event_date =  Database.ParamDef()
event_date.name = 'event_date'
event_date.vartype = 'datetime'
event_date.desc_short = '''The date of the event'''
db.addparamdef(event_date,ctxid)
#end parameter: event_date

#begin parameter: event_agenda
event_agenda =  Database.ParamDef()
event_agenda.name = 'event_agenda'
event_agenda.vartype = 'text'
event_agenda.desc_short = '''The event's agenda'''
db.addparamdef(event_agenda,ctxid)
#end parameter: event_agenda

#begin record definition: event
event = Database.RecordDef()
event.name = 'event'
event.mainview = """$$event_name<br />$$event_date<br />$$event_agenda"""
event.views['tabularview'] = """$$event_name $$event_date"""
event.views['defaultview'] = """$$event_name on $$event_date"""
event.views['recname'] = """$$event_name"""
db.addrecorddef(event,ctxid)
#end record definition: event

#begin parameter: presentation_presenter
presentation_presenter =  Database.ParamDef()
presentation_presenter.name = 'presentation_presenter'
presentation_presenter.vartype = 'user'
presentation_presenter.desc_short = '''The person making the presentation'''
db.addparamdef(presentation_presenter,ctxid)
#end parameter: presentation_presenter

#begin parameter: presentation_title
presentation_title =  Database.ParamDef()
presentation_title.name = 'presentation_title'
presentation_title.vartype = 'string'
presentation_title.desc_short = '''The title of the presentation'''
db.addparamdef(presentation_title,ctxid)
#end parameter: presentation_title

#begin parameter: presentation_file
presentation_file =  Database.ParamDef()
presentation_file.name = 'presentation_file'
presentation_file.vartype = 'binary'
presentation_file.desc_short = '''The presentation's slides'''
db.addparamdef(presentation_file,ctxid)
#end parameter: presentation_file

#begin record definition: presentation
presentation = Database.RecordDef()
presentation.name = 'presentation'
presentation.mainview = """$$presentation_presenter<br />$$presentation_title<br />$$presentation_file some more stuff... continue"""
presentation.views['tabularview'] = """$$presentation_presenter $$presentation_title"""
presentation.views['defaultview'] = """$$presentation_title presented by $$presentation_presenter"""
presentation.views['recname'] = """$$presentation_title"""
db.addrecorddef(presentation,ctxid)
#end record definition: presentation

#begin parameter: sponsor_name
sponsor_name =  Database.ParamDef()
sponsor_name.name = 'sponsor_name'
sponsor_name.vartype = 'string'
sponsor_name.desc_short = '''The sponsor's name'''
db.addparamdef(sponsor_name,ctxid)
#end parameter: sponsor_name

#begin parameter: sponsor_website
sponsor_website =  Database.ParamDef()
sponsor_website.name = 'sponsor_website'
sponsor_website.vartype = 'string'
sponsor_website.desc_short = '''The sponsor's website'''
db.addparamdef(sponsor_website,ctxid)
#end parameter: sponsor_website

#begin parameter: sponsor_logo
sponsor_logo =  Database.ParamDef()
sponsor_logo.name = 'sponsor_logo'
sponsor_logo.vartype = 'binaryimage'
sponsor_logo.desc_short = '''The sponsor's logo'''
db.addparamdef(sponsor_logo,ctxid)
#end parameter: sponsor_logo

#begin record definition: sponsor
sponsor = Database.RecordDef()
sponsor.name = 'sponsor'
sponsor.mainview = """$$sponsor_name<br />$$sponsor_website<br />$$sponsor_logo"""
sponsor.views['tabularview'] = """$$sponsor_name $$sponsor_website"""
sponsor.views['defaultview'] = """<a href="$$sponsor_website">$$sponsor_name</a>"""
sponsor.views['recname'] = """$$sponsor_name"""
db.addrecorddef(sponsor,ctxid)
#end record definition: sponsor

#begin parameter: location_name
location_name =  Database.ParamDef()
location_name.name = 'location_name'
location_name.vartype = 'string'
location_name.desc_short = '''The name of the location'''
db.addparamdef(location_name,ctxid)
#end parameter: location_name

#begin parameter: location_address
location_address =  Database.ParamDef()
location_address.name = 'location_address'
location_address.vartype = 'string'
location_address.desc_short = '''The address of the location'''
db.addparamdef(location_address,ctxid)
#end parameter: location_address

#begin record definition: location
location = Database.RecordDef()
location.name = 'location'
location.mainview = """$$location_name<br />$$location_address"""
location.views['tabularview'] = """$$location_name"""
location.views['defaultview'] = """$$location_name"""
location.views['recname'] = """$$location_name"""
db.addrecorddef(location,ctxid)
#end record definition: location

#begin parameter: folder_name
folder_name =  Database.ParamDef()
folder_name.name = 'folder_name'
folder_name.vartype = 'string'
folder_name.desc_short = '''The name of a folder'''
db.addparamdef(folder_name,ctxid)
#end parameter: folder_name

#begin record definition: folder
folder = Database.RecordDef()
folder.name = 'folder'
folder.mainview = """$$folder_name"""
folder.views['tabularview'] = """$$folder_name"""
folder.views['defaultview'] = """$$folder_name"""
folder.views['recname'] = """$$folder_name"""
db.addrecorddef(folder,ctxid)
#end record definition: folder

#begin parameter: template_name
template_name =  Database.ParamDef()
template_name.name = 'template_name'
template_name.vartype = 'string'
template_name.desc_short = '''the name of the template'''
db.addparamdef(template_name,ctxid)
#end parameter: template_name

#begin parameter: template_template
template_template =  Database.ParamDef()
template_template.name = 'template_template'
template_template.vartype = 'text'
template_template.desc_short = '''the template's context'''
db.addparamdef(template_template,ctxid)
#end parameter: template_template

#begin record definition: template
template = Database.RecordDef()
template.name = 'template'
template.mainview = """$$template_name $$template_template"""
template.views['tabularview'] = """$$template_name"""
template.views['defaultview'] = """$$template_name<br />$$template_template"""
template.views['recname'] = """$$template_name"""
db.addrecorddef(template,ctxid)
#end record definition: template

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
grant_number.vartype = 'int'
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

#begin parameter: investigator_email
investigator_email =  Database.ParamDef()
investigator_email.name = 'investigator_email'
investigator_email.vartype = 'string'
investigator_email.desc_short = '''Phone Number'''
db.addparamdef(investigator_email,ctxid)
#end parameter: investigator_email

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
investigator.mainview = """$$investigator_name $$investigator_degrees $$investigator_department  $$investigator_institution $$investigator_phone $$investigator_fax  $$investigator_emai"""
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
address_zip.vartype = 'int'
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

#begin parameter: menu_label
menu_label =  Database.ParamDef()
menu_label.name = 'menu_label'
menu_label.vartype = 'string'
menu_label.desc_short = '''Displayed menu item name'''
db.addparamdef(menu_label,ctxid)
#end parameter: menu_label

#begin parameter: menu_link
menu_link =  Database.ParamDef()
menu_link.name = 'menu_link'
menu_link.vartype = 'string'
menu_link.desc_short = '''Menu Item target'''
db.addparamdef(menu_link,ctxid)
#end parameter: menu_link

#begin record definition: menu_item
menu_item = Database.RecordDef()
menu_item.name = 'menu_item'
menu_item.mainview = """$$menu_label $$menu_link"""
menu_item.views['tabularview'] = """$$menu_label"""
menu_item.views['defaultview'] = """$$menu_label"""
menu_item.views['recname'] = """$$menu_label"""
db.addrecorddef(menu_item,ctxid)
#end record definition: menu_item

#begin parameter: page_name
page_name =  Database.ParamDef()
page_name.name = 'page_name'
page_name.vartype = 'string'
page_name.desc_short = '''Page Name'''
db.addparamdef(page_name,ctxid)
#end parameter: page_name

#begin parameter: page_menus
page_menus =  Database.ParamDef()
page_menus.name = 'page_menus'
page_menus.vartype = 'string'
page_menus.desc_short = '''Page Menus'''
db.addparamdef(page_menus,ctxid)
#end parameter: page_menus

#begin parameter: page_content
page_content =  Database.ParamDef()
page_content.name = 'page_content'
page_content.vartype = 'text'
page_content.desc_short = '''Page Content'''
db.addparamdef(page_content,ctxid)
#end parameter: page_content

#begin record definition: page
page = Database.RecordDef()
page.name = 'page'
page.mainview = """$$page_name $$page_menus $$page_content"""
page.views['tabularview'] = """$$page_name"""
page.views['defaultview'] = """$$page_name $$page_menus $$page_content"""
page.views['recname'] = """$$page_name"""
db.addrecorddef(page,ctxid)
#end record definition: page