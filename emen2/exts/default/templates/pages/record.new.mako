<%!import jsonrpc.jsonutil %>
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
	$('#e2l-editbar-newrecord-permissions').EditbarControl({width: 720});
	$('#e2-newrecord-permissions').PermissionControl({
		name: 'None',
		edit: true,
		embed: true
	});	

	// Change the text of file upload elements..
	$('.e2l-editable-binary .e2l-label').html('(The record must be saved before files can be attached)');

	// Change the Record type
	$('#e2l-editbar-newrecord-recorddef').EditbarControl({
		width:300,
		cb: function(self){
			self.popup.NewRecordControl({
				embedselector: true,
				showselector: true,
				parent: parent.name
				});
			}
	});
</%block>

<ul class="e2l-menu e2l-editbar e2l-clearfix">

	<li id="e2l-editbar-newrecord-recorddef">
		<span class="e2l-a e2l-label">Change Protocol <img src="${EMEN2WEBROOT}/static/images/caret_small.png" alt="^" /></span>
	</li>
	
	<li id="e2l-editbar-newrecord-permissions">
		<span class="e2l-a e2l-label">
			Permissions
			<img src="${EMEN2WEBROOT}/static/images/caret_small.png" alt="^" />
		</span>
		<div id="e2-newrecord-permissions" class="e2l-menu-hidden"></div>
	</li>

</ul>


<div style="background:#eee;padding:10px;border:solid 1px #ccc;border-top:none">
	<p>
		You are creating a new <a href="">${recdef.desc_short} (${recdef.name})</a> record as a child of <a href="">${recnames.get(rec.name, rec.name)}</a>
	</p>
	<p><strong>Protocol description:</strong> ${recdef.desc_long}</p>
</div>


## Main rendered record
<form id="newrecord" name="rendered" method="post" action="${EMEN2WEBROOT}/record/${rec.name}/edit/" class="e2-view" data-viewtype="${viewtype}" data-name="${rec.name}" data-edit="True">
	${rendered}
	<div class="e2l-controls">
		<input type="button" value="Save">
	</div>
</form>



