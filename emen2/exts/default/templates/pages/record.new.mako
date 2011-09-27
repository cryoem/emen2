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
	$('#newrecord').MultiEditControl({show: true});

	//$('#newrecord .e2l-editable').each(function() {
	//	$(this).EditControl({show:true});
	//});

	// Permissions Editor
	$('#e2l-editbar-permissions').EditbarControl({
		'box':'#e2l-editbar-permissions-box'
	});
	$('#e2l-editbar-newrecord').EditbarControl({
		'box':'#e2l-editbar-newrecord-box'
	})

	// $('#e2-newrecord-permissions').PermissionControl({
	//	name: 'None',
	//	edit: true,
	//	embed: true
	//});	

	// Change the text of file upload elements..
	$('.e2l-editable-binary .e2l-label').html('(The record must be saved before files can be attached)');

	// Change the Record type
	//$('#e2l-editbar-newrecord-recorddef').EditbarControl({
	//	width:300,
	//	cb: function(self){
	//		self.popup.NewRecordControl({
	//			embedselector: true,
	//			showselector: true,
	//			parent: parent.name
	//			});
	//		}
	//});
</%block>

<ul class="e2l-menu e2l-editbar e2l-clearfix">

	<li id="e2l-editbar-newrecord">
		<span class="e2l-a e2l-label">Change Protocol <img src="${EMEN2WEBROOT}/static/images/caret_small.png" alt="^" /></span>
	</li>
	
	<li id="e2l-editbar-permissions">
		<span class="e2l-a e2l-label">
			Permissions
			<img src="${EMEN2WEBROOT}/static/images/caret_small.png" alt="^" />
		</span>
	</li>

</ul>

<div class="e2l-editbar-area">
	<div class="e2l-menu-box e2l-hide" id="e2l-editbar-newrecord-box">Change Protocol...</div>

	<div class="e2l-menu-box e2l-hide" id="e2l-editbar-permissions-box">Permissions...</div>

	<div class="e2l-menu-box">
		<p>
			You are creating a new <a href="">${recdef.desc_short}</a> record as a child of <a href="">${recnames.get(rec.name, rec.name)}</a>
		</p>
		##<p><strong>Protocol description:</strong></p>
		${markdown.markdown(recdef.desc_long)}
	</div>
</div>

## Main rendered record
<form id="newrecord" name="rendered" method="post" action="${EMEN2WEBROOT}/record/${rec.name}/edit/" class="e2-view" data-viewtype="${viewtype}" data-name="None" data-edit="True">
	${rendered}
	<div class="e2l-controls">
		<input type="button" value="Save">
	</div>
</form>



