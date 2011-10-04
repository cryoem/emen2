<%inherit file="/page" />
<%namespace name="login" file="/auth/login"  /> 

<h1>${error}</h1>

% if not USER or USER == 'anonymous':
	${login.login(location=location)}
% endif