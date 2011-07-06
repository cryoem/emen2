<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 
<%namespace name="user_util" file="/pages/user.util" /> 


% if user.disabled:
	<div class="notify deleted">Disabled User</div>
% endif


<h1>${user_util.page_title(user, True)}</h1>

${user_util.page_userrec(user, True)}

<br /><br />

<%call expr="buttons.singlepage('_email','Change Email')">		
	${user_util.page_email(user, True)}
</%call>
	
<%call expr="buttons.singlepage('_password','Change Password')">	
	${user_util.page_password(user, True)}
</%call>

<%call expr="buttons.singlepage('_photo','Update Photo')">
	${user_util.page_photo(user, True)}
</%call>		

<%call expr="buttons.singlepage('_privacy','Set Privacy')">		
	${user_util.page_privacy(user, True)}
</%call>

% if admin:
	<%call expr="buttons.singlepage('_status','Set Account Status')">		
		${user_util.page_status(user, True)}
	</%call>	
% endif

<%call expr="buttons.singlepage('_groups','Groups')">		
	${user_util.page_groups(user, True)}
</%call>

<%call expr="buttons.singlepage('_history','History')">		
	${user_util.page_history(user, True)}
</%call>
	