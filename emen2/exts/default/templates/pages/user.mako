<%inherit file="/page" />
<%namespace name="pages_user_util" file="/pages/user.util"  /> 


% if user.disabled:
	<div class="notify deleted">Disabled User</div>
% endif




<h1>
	${pages_user_util.page_title(user, False)} 
	% if admin:
		<span class="label"><a href="${EMEN2WEBROOT}/user/${user.name}/edit/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> Edit Profile</a></span>
	% endif
</h1>


<!-- Profile View; photo and tools are to the left of this -->
<div class="clearfix">

	<div class="floatright">
		${pages_user_util.page_photo(user, False)}
	</div>

	<div class="floatleft">
		${pages_user_util.page_userrec(user, False)}
	</div>

</div>


