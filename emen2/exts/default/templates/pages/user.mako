<%inherit file="/page" />
<%namespace name="pages_user_util" file="/pages/user.util"  /> 

<h1>
	${pages_user_util.page_title(user, False)} 
	% if admin:
		<span class="e2l-label"><a href="${EMEN2WEBROOT}/user/${user.name}/edit/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> Edit Profile</a></span>
	% endif
</h1>


<div class="e2l-cf">

	<div class="e2l-float-right">
		${pages_user_util.page_photo(user, False)}
	</div>

	<div class=".e2l-float-left">
		${pages_user_util.page_userrec(user, False)}
	</div>

</div>











