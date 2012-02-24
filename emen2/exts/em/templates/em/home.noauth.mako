<%inherit file="/page" />
<%namespace name="login" file="/auth/login"  /> 

<%block name="js_ready">
	$('input[name=name]').focus();
</%block>

<h1>Welcome to ${EMEN2DBNAME}</h1>

<div>${render_banner or ''}</div>

${login.login()}
