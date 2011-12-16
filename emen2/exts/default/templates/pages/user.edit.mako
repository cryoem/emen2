<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 
<%namespace name="user_util" file="/pages/user" /> 

<h1>${user_util.page_title(user, True)}</h1>

% if user.name != 'root' and user.record != None:

	${user_util.page_userrec(user, True)}

	<br />

	<%buttons:singlepage label='Update Photo'>
		${user_util.page_photo(user, True)}
	</%buttons:singlepage>

% endif

<%buttons:singlepage label='Change Email'>
	${user_util.page_email(user, True)}
</%buttons:singlepage>

<%buttons:singlepage label='Change Password'>
	${user_util.page_password(user, True)}
</%buttons:singlepage>

<%buttons:singlepage label='Set Privacy'>
	${user_util.page_privacy(user, True)}
</%buttons:singlepage>

% if ADMIN:
	<%buttons:singlepage label='Account Status'>
		${user_util.page_status(user, True)}
	</%buttons:singlepage>
% endif

## <%buttons:singlepage label='Groups'>
##	${user_util.page_groups(user, True)}
## </%buttons:singlepage>

## <%buttons:singlepage label='History'>
##	${user_util.page_history(user, True)}
## </%buttons:singlepage>
