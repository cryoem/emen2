<%inherit file="/page" />
<%namespace name="pages_user_util" file="/pages/user"  /> 


<p>
	<form method="post" action="${EMEN2WEBROOT}/users/admin/">
		% if q:
			<input type="text" name="q" length="30" value="${q}" />
		% else:
			<input type="text" name="q" length="30" />
		% endif
		<input type="submit" value="Search" />
	</form>	
</p>

<br /><br />

<div>

	${pages_user_util.userlist(users, sortby=sortby, reverse=reverse, admin=admin)}

</div>