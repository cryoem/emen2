<%!
	import jsonrpc.jsonutil
	import markdown
%>
<%inherit file="/pages/record" />

<%namespace name="buttons" file="/buttons" />

<%block name="js_ready">
	${parent.js_ready()}
	caches['record']['None'] = ${jsonrpc.jsonutil.encode(newrec)};
	caches['recorddef'][${jsonrpc.jsonutil.encode(recdef.name)}] = ${jsonrpc.jsonutil.encode(recdef)};
	var rec = caches['record'][null]

	// Save Record
	$('#e2-form-newrecord').MultiEditControl({
		show: true,
		permissions: $('#e2-form-permissions')
	});

	$('.e2l-newtab').TabControl({});

	$('.e2l-newtab').TabControl('setcb','permissions', function(page){
		$('#e2-form-permissions', page).PermissionsControl({
			name: 'None',
			show: true
		})
	})
</%block>



<div class="e2l-newtab e2l-cf" data-group="newrecord">

	<ul class="e2l-cf">
		<li data-tab="newrecord"><a>Change Protocol ${buttons.caret()}</a></li>
		<li data-tab="info" class="e2l-newtab-active"><a>Info ${buttons.caret()}</a></li>
		<li data-tab="permissions"><a>Permissions ${buttons.caret()}</a></li>
	</ul>

	<div data-tab="newrecord">
		Change protocol...
	</div>
	
	<div data-tab="info" class="e2l-newtab-active">
		<p>
			You are creating a new <a href="">${recdef.desc_short}</a> record as a child of <a href="">${recnames.get(rec.name, rec.name)}</a>
		</p>
		<p><strong>Protocol description:</strong></p>
		${markdown.markdown(recdef.desc_long)}
	</div>

	<div data-tab="permissions">
		## This form will be copied into the main form during submit
		<form id="e2-form-permissions"></form>
	</div>

</div>


## Main rendered record

<form id="e2-form-newrecord" data-name="None" method="post" action="${EMEN2WEBROOT}/record/${rec.name}/new/${newrec.rectype}/" >

	<div id="rendered" class="e2-view" data-viewtype="${viewtype}" data-name="None">
		${rendered}
	</div>
	
	<div class="e2l-controls">
		<input type="submit" value="Save">
	</div>

</form>



