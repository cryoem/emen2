<%!
	import jsonrpc.jsonutil
	import markdown
%>
<%inherit file="/record/record" />
<%namespace name="buttons" file="/buttons" />

<%block name="css_inline">
	${parent.css_inline()}
	#content {
		width: auto;
		padding: 0px;
	}
	#content_inner {
		padding: 0px;
		padding-top: 10px;
		padding-left: 30px;
		padding-right: 30px;
	}
</%block>


<%block name="js_ready">
	${parent.js_ready()}
	${buttons.tocache(newrec)}
	${buttons.tocache(recdef)}
	
	// Save Record
	$('#e2-edit').MultiEditControl({
		show: true,
		permissions: $('#e2-permissions')
	});

	var tab = $('#e2-tab-editbar');
	tab.TabControl({});

	// Permissions editor
	tab.TabControl('setcb','permissions', function(page){
		// console.log('perm');
		$('#e2-permissions', page).PermissionsControl({
			name: 'None',
			show: true,
			edit: true
		});
	});
	
</%block>


<div id="e2-tab-editbar" class="e2-tab e2-tab-editbar" role="tab" data-tabgroup="newrecord">
	<ul class="e2l-cf" role="menubar tablist" data-tabgroup="newrecord">
		<li data-tab="newrecord"><a>New record</a></li>
		<li data-tab="info" class="e2-tab-active"><a>Help ${buttons.caret()}</a></li>
		<li data-tab="permissions"><a>Permissions ${buttons.caret()}</a></li>
	</ul>
</div>
<div class="e2-tab e2-tab-editbar" data-tabgroup="newrecord" role="tabpanel">
	<div data-tab="newrecord">
		Change protocol...
	</div>
	
	<div data-tab="info" class="e2-tab-active">
		<p>
			You are creating a new <a href="${ctxt.reverse('RecordDef/main', name=recdef.name)}">${recdef.desc_short}</a> record as a child of <a href="${ctxt.reverse('Record/main', name=rec.name)}">${recnames.get(rec.name, rec.name)}</a>
		</p>
		${markdown.markdown('<strong>Protocol description:</strong>\n'+recdef.desc_long)}
	</div>

	<div data-tab="permissions">
		## This form will be copied into the main form during submit
		<form id="e2-permissions"></form>
	</div>
</div>


## Main rendered record

<form id="e2-edit" data-name="None" method="post" action="${EMEN2WEBROOT}/record/${rec.name}/new/${newrec.rectype}/" enctype="multipart/form-data">
	<div id="content_inner">
		<div id="rendered" class="e2-view" data-viewname="${viewname}">
			${rendered}
		</div>
	
		<div class="e2l-controls">
			<input type="submit" value="Save">
		</div>
	</div>
</form>



