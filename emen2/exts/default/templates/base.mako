<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" version="-//W3C//DTD XHTML 1.1//EN" xml:lang="en">

<%namespace name="buttons"  file="/buttons"  /> 

#################
## Functions that child templates might implement

## Any additional items for <head>
<%def name="head()"></%def>


## Inline styles
<%def name="extrastyle()"></%def>


## Page Title
<%def name="title()" filter="trim">
	${context.get('title','')}
</%def>


## Page Title / Header
<%def name="header()">
	<div id="title">
		<%include file="/header" />
	</div>
</%def>


## Relationship Map
<%def name="precontent()"></%def>

#################
## Page
<%def name="footer()">
	<div id="footer"></div>
</%def>


## Alerts and notifications
<%def name="alert()">
	<ul id="alert" class="alert nonlist precontent"></ul>
</%def>


## Tabs
<%def name="tabs()">
	% if pages:
		<div class="precontent">${buttons.buttons(pages)}</div>
	% else:
		<div class="precontent">${buttons.titlebutton(self.title)}</div>
	% endif	
</%def>

#################
## Page

<head>

	<meta http-equiv="Content-type" content="text/html; charset=utf-8" />
	<meta http-equiv="Content-Language" content="en-us" />

	<title>${EMEN2DBNAME}: ${self.title()}</title>

    % for css in css_files:
		<link rel="StyleSheet" href="${css}" type="text/css" />
    % endfor

    % for script in js_files:
		<script src="${script}" type="text/javascript"></script>
    % endfor

	<script type="text/javascript">
		$(document).ready(function() {
			$("#e2-header-search").focus(function() {
				if( this.value == this.defaultValue ) {
					this.value = "";
				}
			}).blur(function() {
				if( !this.value.length ) {
					this.value = this.defaultValue;
				}
			});
		});		
	</script>

	<%self:head />
	
	<style type="text/css">
		<%self:extrastyle />
	</style>

</head>

<body>

	${next.body()}

</body></html>
