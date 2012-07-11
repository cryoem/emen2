<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  />
<%namespace name="pages_user_util" file="/pages/user"  />

<%block name="js_ready">
	${parent.js_ready()}
	${buttons.tocache(group)}
	var edit = ${jsonrpc.jsonutil.encode(edit)};
	$('#members').PermissionsControl({
		keytype: 'group',
		name: ${jsonrpc.jsonutil.encode(group.name)},
		edit: edit,
		embed: true,
		groups: false
	});
</%block>



<h1>
	% if new:
		New User Group
	% else:
		${group.get('displayname')}
	% endif
	
	<ul class="e2l-actions">
		% if (ADMIN or group.isowner()) and not edit:
			<li><a class="e2-button" href="${EMEN2WEBROOT}/group/${group.name}/edit/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> Edit</a></li>
		% endif	
	</ul>

</h1>

% if new:
	<form method="post" action="${ctxt.reverse('Group/new')}">
% else:
	<form method="post" action="${ctxt.reverse('Group/edit', name=group.name)}">
% endif

<%buttons:singlepage label='Details'>
	<table>
		<tr>
			<td>User Group Name:</td>

			% if new:
				<td><input type="text" name="name" value="" /></td>
			% else:
				<td>${group.name}<input type="hidden" name="name" value="${group.name}" /></td>
			% endif

		</tr>

		<tr>
			<td>Display Name:</td>

			% if new:
				<td><input type="text" name="displayname" value="" /></td>
			% elif edit:
				<td><input type="text" name="displayname" value="${group.get('displayname')}" /></td>
			% else:
				<td>${group.get('displayname')}</td>
			% endif

		</tr>

		% if not new:

			<tr>
				<td>Created:</td>
				<td><time class="e2-localize" datetime="${group.creationtime}">${group.creationtime}</time></td>
			</tr>


			<tr>
				<td>Modified:</td>
				<td><time class="e2-localize" datetime="${group.modifytime}">${group.modifytime}</time></td>
			</tr>

		% endif


	</table>
</%buttons:singlepage>



<%buttons:singlepage label='Members'>
	<div id="members"></div>
</%buttons:singlepage>


% if new or edit:
	<div class="e2l-controls" id="ext_save">
		${buttons.spinner(false)}
		<input type="submit" value="Save">
	</div>
% endif


</form>
