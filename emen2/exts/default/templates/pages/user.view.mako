<%inherit file="/page" />
<%namespace name="user_util" file="/pages/user"  /> 

<h1>
	${user.displayname}
	% if ADMIN:
		<span class="e2l-label"><a href="${EMEN2WEBROOT}/user/${user.name}/edit/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> Edit Profile</a></span>
	% endif
</h1>


<div class="e2l-cf">

	${user_util.profile(user=user, userrec=user.userrec, edit=False)}

</div>


