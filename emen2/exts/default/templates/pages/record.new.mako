<%!import jsonrpc.jsonutil %>
<%inherit file="/pages/record" />
<%namespace name="buttons" file="/buttons" />

<%block name="javascript_ready">
	caches['record'][null] = ${jsonrpc.jsonutil.encode(newrec)};
	caches['recorddef'][${jsonrpc.jsonutil.encode(recdef.name)}] = ${jsonrpc.jsonutil.encode(recdef)};
	var rec = caches['record'][null]

	// New Record Information
	$('#e2l-editbar-newrecord-info').EditbarControl({show: true, width:640});

	// Pad the rendered area
	// $('#rendered').css('margin-top', $('#e2l-editbar-newrecord-info div.hidden').height()+10);

	// Save Record
	$('#e2-newrecord-save').MultiEditControl({
		name: rec.name,
		form: '#rendered',
		show: true
		});

	// Permissions Editor
	$('#e2l-editbar-newrecord-permissions').EditbarControl({width: 640});
	$('#e2-newrecord-permissions').PermissionControl({
		name: rec.name,
		edit: true,
		embed: true
		});	

	// Change the text of file upload elements..
	$('.editable_files .label').html('(The record must be saved before files can be attached)');

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

<ul class="menu editbar e2l-float-list e2l-clearfix">

	<li id="e2l-editbar-newrecord-recorddef">
		<span class="clickable label">Change Protocol <img src="${EMEN2WEBROOT}/static/images/caret_small.png" alt="^" /></span>
	</li>
	
	<li id="e2l-editbar-newrecord-permissions">
		<span class="clickable label">
			Permissions
			<img src="${EMEN2WEBROOT}/static/images/caret_small.png" alt="^" />
		</span>
		<div id="e2-newrecord-permissions" class="hidden"></div>
	</li>

</ul>


## <table cellpadding="0" cellspacing="0" style="padding-left:10px;padding-right:10px;border-bottom:solid 1px #ccc">
## 	<tbody>
## 		<tr>
## 			<td style="width:150px">New Record</td>
## 			<td>You are creating a new ${recdef.desc_short} record as a child of ${recnames.get(rec.name, rec.name)}</td>
## 		</tr>
## 		<tr>
## 			<td>Protocol</td>
## 			<td>${recdef.desc_long}</td>
## 		</tr>
## 	</tbody>
## </table>

	##	You are creating a new <a href="${ctxt.reverse('RecordDef', action=None, name=rec.rectype)}">${recdef.desc_short} (${recdef.name})</a>
	##	record as a child of <a href="${ctxt.reverse('Record', name=rec.name)}">${recnames.get(rec.name, rec.name)}</a>			
	##	<h4>Protocol Description</h4>

## <div id="rendered" class="e2-view" data-viewtype="${viewtype}" data-name="None" data-edit="true">
## 	${rendered}
## </div>

## Main rendered record
<form id="rendered" name="rendered" method="post" action="${EMEN2WEBROOT}/record/${rec.name}/edit/" class="e2-view" data-viewtype="${viewtype}" data-name="${rec.name}" data-edit="True">
	${rendered}
</form>

<div class="e2l-clearfix save">
	<div id="e2-newrecord-save" class="label">Edit</div>
</div>

