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
<%block name="js_ready">
	${parent.js_ready()}
	//$('#bookmarks').hover(
	//	function() {
	//		$(this).BookmarksControl();
	//		$(this).BookmarksControl('showbookmarks')
	//	}, function(){}
	//);
</%block>

## Basic page template:
<div id="container">

	## Page header and navigation
	<%block name="header">
		<%include file="/header" />
	</%block>
	
	<div id="precontent">

	## Alerts and notifications
	<%block name="alert">
		<ul class="e2-alert e2-alert-main" role="alert">
			% for msg in NOTIFY:
			   <li>${msg}</li>
			% endfor
			% for msg in ERRORS:
			   <li class="e2l-error">${msg}</li>
			% endfor
	   </ul>
	</%block>

	## Precontent -- usually a Relationship tree
	<%block name="precontent" />

	## Tabs
	<%block name="tabs">
		${buttons.newtabs(pages or context.get('title','No Title'), cls='e2-tab-main')}
	</%block>

	</div>

	<div id="content" role="main">
		${next.body()}
	</div>

	<%block name="footer">
		<div id="footer"></div>
	</%block>

</div>
