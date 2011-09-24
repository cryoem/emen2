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

		caches['group'][${jsonrpc.jsonutil.encode(group.name)}] = ${jsonrpc.jsonutil.encode(group)};

		$('#group_members').PermissionControl({
			keytype: 'group',
			name: ${jsonrpc.jsonutil.encode(group.name)},
			edit: edit,
			embed: true
		});

		$('input[name=save]').click(function() {
			var g = caches['group'][${jsonrpc.jsonutil.encode(group.name)}];
			g["permissions"] = $('#group_members').PermissionControl('getusers');
			g["displayname"] = $('input[name=group_displayname]').val();
			g["name"] = $('input[name=group_name]').val();
			$.jsonRPC.call("putgroup", [g], function(group) {
				window.location = EMEN2WEBROOT+'/group/'+group.name+'/';
			})

		});

	});

//]]>
</script>



<h1>

	% if new:
		New Group
	% else:
		${group.get('displayname')} (${group.name})
	% endif

	% if admin and not edit:
		<span class="label"><a href="${EMEN2WEBROOT}/group/${group.name}/edit/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> Edit</a></span>
	% endif

	% if new or edit:
		<div class="controls save" id="ext_save">
			<img class="e2l-spinner hide" src="${EMEN2WEBROOT}/static/images/spinner.gif" alt="Loading" />
			<input type="submit" value="Save" name="save">
		</div>
	% endif

</h1>

<%buttons:singlepage label='Group Info'>
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

			% if new:
				<td><input type="text" name="group_displayname" value="" /></td>
			% elif edit:
				<td><input type="text" name="group_displayname" value="${group.get('displayname')}" /></td>
			% else:
				<td>${group.get('displayname')}</td>
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
</%buttons:singlepage>



<%buttons:singlepage label='Group Members'>
	<div id="group_members"></div>
</%buttons:singlepage>


