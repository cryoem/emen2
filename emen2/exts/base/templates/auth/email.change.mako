<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

<h1>${title}</h1>

<form method="post" action="${EMEN2WEBROOT}/auth/email/change/">

	<input type="hidden" name="location" value="${location or ''}" />
	<input type="hidden" name="name" value="${name or ''}" />

	<table>
		% if not admin:
			<tr><td>Current Password:</td><td><input type="password" name="opw" /></td></tr>		
		% endif
	
		<tr><td>New Email:</td><td><input type="text" name="email" value="${email or ''}" /></td>
		<tr><td/><td><input type="submit" value="Change Email" name="save"></td></tr>

	</table>

</form>

