<%!
	import jsonrpc.jsonutil
	import markdown
%>
<%inherit file="/pages/record" />

<%namespace name="buttons" file="/buttons" />

<%block name="js_inline">
	${parent.js_inline()}
	${buttons.tocache(newrec)}
	${buttons.tocache(recdef)}
</%block>


<%block name="js_ready">
	${parent.js_ready()}
	
	// Save Record
	$('#e2-edit').MultiEditControl({
		show: true,
		permissions: $('#e2-permissions')
	});

	var tab = $('#e2-editbar-newrecord');
	tab.TabControl({});

	// Permissions editor
	tab.TabControl('setcb','permissions', function(page){
		console.log('perm');
		$('#e2-permissions', page).PermissionsControl({
			name: 'None',
			show: true,
			edit: true
		});
	});
	
</%block>


<div class="e2-tab e2-editbar" id="e2-editbar-newrecord" data-group="newrecord">

	<ul class="e2l-cf">
		<li data-tab="newrecord"><a>Change Protocol ${buttons.caret()}</a></li>
		<li data-tab="info" class="e2-tab-active"><a>Info ${buttons.caret()}</a></li>
		<li data-tab="permissions"><a>Permissions ${buttons.caret()}</a></li>
	</ul>

	<div data-tab="newrecord">
		Change protocol...
	</div>
	
	<div data-tab="info" class="e2-tab-active">
		<p>
			You are creating a new <a href="">${recdef.desc_short}</a> record as a child of <a href="">${recnames.get(rec.name, rec.name)}</a>
		</p>
		${markdown.markdown('<strong>Protocol description:</strong>\n'+recdef.desc_long)}
	</div>

	<div data-tab="permissions">
		## This form will be copied into the main form during submit
		<form id="e2-permissions"></form>
	</div>

</div>


## Main rendered record

<form id="e2-edit" data-name="None" method="post" action="${EMEN2WEBROOT}/record/${rec.name}/new/${newrec.rectype}/" >

	<div id="rendered" class="e2-view" data-viewtype="${viewtype}">
		${rendered}
	</div>
	
	<div class="e2l-controls">
		<input type="submit" value="Save">
	</div>

</form>



