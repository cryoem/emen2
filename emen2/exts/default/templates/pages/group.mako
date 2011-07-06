<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 
<%namespace name="pages_user_util" file="/pages/user.util"  /> 


<% 
import jsonrpc.jsonutil 
%>


<script type="text/javascript">
//<![CDATA[
	$(document).ready(function() {
		
		var edit = ${jsonrpc.jsonutil.encode(edit)};

		caches['groups'][${jsonrpc.jsonutil.encode(group.name)}] = ${jsonrpc.jsonutil.encode(group)};

		$('#group_members').PermissionControl({
			keytype: 'group',
			name: ${jsonrpc.jsonutil.encode(group.name)},
			edit: edit,
			embed: true
		});

		$('input[name=save]').click(function() {
			var g = caches['groups'][${jsonrpc.jsonutil.encode(group.name)}];
			g["permissions"] = $('#group_members').PermissionControl('getusers');
			g["displayname"] = $('input[name=group_displayname]').val();
			g["name"] = $('input[name=group_name]').val();
			
			$.jsonRPC("putgroup", [g], function(group) {
				//notify_post(EMEN2WEBROOT+'/group/'+group.name, []);
				window.location = EMEN2WEBROOT+'/group/'+group.name+'/';
			})

		});

	});	

//]]>
</script>



<h1>
	${group.get('displayname')} (${group.name})
	% if admin and not edit:
		<span class="label"><a href="${EMEN2WEBROOT}/group/${group.name}/edit/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> Edit</a></span>
	% endif
	
	% if new or edit:
		<div class="controls save" id="ext_save">
			<img class="spinner hide" src="${EMEN2WEBROOT}/static/images/spinner.gif" alt="Loading" />
			<input type="submit" value="Save" name="save">
		</div>
	% endif	
	
</h1>

<%call expr="buttons.singlepage('_groupinfo','Group Info')">

	<table>
		<tr>
			<td>Group Name:</td>

			% if new:
				<td><input type="text" name="group_name" value="" /></td>
			% else:
				<td>${group.name}<input type="hidden" name="group_name" value="${group.name}" /></td>		
			% endif
		
		</tr>

		<tr>
			<td>Display Name:</td>

			% if edit or new:
				<td><input type="text" name="group_displayname" value="${group.displayname}" /></td>
			% else:
				<td>${group.displayname}</td>		
			% endif

		</tr>

		% if not new:

			<tr>
				<td>Created:</td>
				<td>${group.creationtime}</td>
			</tr>
	

			<tr>
				<td>Modified:</td>
				<td>${group.modifytime}</td>
			</tr>

		% endif


	</table>

</%call>



<%call expr="buttons.singlepage('_groupinfo','Group Members')">

<div id="group_members">
</div>


</%call>


