<%inherit file="/base" />
<%namespace name="buttons"  file="/buttons"  /> 

## Overriding templates
## 	must export named blocks:
## => header
## => footer
## => tabs
## => alert
## => precontent

## Javascript to run when the page is loaded
<%block name="javascript_ready">
	${parent.javascript_ready()}
	$('#bookmarks').hover(
		function() {
			$(this).BookmarksControl();
			$(this).BookmarksControl('showbookmarks')
		}, function(){}
	);
</%block>

## Basic page template:
<div id="container">

	## Page header and navigation
	<%block name="header">
		<%include file="/header" />
	</%block>

	## Alerts and notifications
	<%block name="alert">
		<ul id="e2l-alert" class="e2l-alert e2l-nonlist e2l-precontent">
			% for msg in notify:
			   <li>${msg}</li>
			% endfor
			% for msg in errors:
			   <li class="e2l-error">${msg}</li>
			% endfor
	   </ul>
	</%block>

	## Precontent -- usually a relationship Map
	<%block name="precontent" />

	## Tabs
	<%block name="tabs">
		% if pages:
			<div class="e2l-precontent">${buttons.buttons(pages)}</div>
		% else:
			<div class="e2l-precontent">${buttons.titlebutton(title)}</div>
		% endif	
	</%block>

	<div id="content">
		${next.body()}
	</div>

	<%block name="footer">
		<div id="footer"></div>
	</%block>

</div>
