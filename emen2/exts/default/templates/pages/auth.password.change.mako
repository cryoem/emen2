<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

<h1>${title}</h1>


% if errmsg:

	<div class="notify error">${errmsg}</div>

% endif


% if msg:
	
	<div class="notify">
		${msg}
	</div>
	
% else:


	<form action="${EMEN2WEBROOT}/auth/password/change/" method="post">

		<input type="hidden" name="location" value="${location}" />
		<input type="hidden" name="name" value="${name or ''}" />
	
		<table>
			% if not admin:
				<tr><td>Current Password:</td><td><input type="password" name="opw" /></td></tr>
			% endif
			<tr><td style="width:150px">New Password:</td><td><input type="password" name="on1" /></td></tr>
			<tr><td>Confirm New Password:</td><td><input type="password" name="on2" /></td></tr>

			<tr><td /><td><input type="submit" value="Change Password" /></td></tr>
		
		</table>
	</form>

% endif