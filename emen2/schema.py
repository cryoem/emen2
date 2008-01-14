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