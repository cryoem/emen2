<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 
<%namespace name="forms" file="/forms"  /> 
<%namespace name="user_util" file="/pages/user"  /> 


<%block name="js_ready">
	${parent.js_ready()}
	${user_util.newuser_js_ready()}
</%block>

<h1>Welcome to ${EMEN2DBNAME}</h1>

<p>
	Please complete this form to create an account. 
	We request detailed contact information because this is included in our grant reports.
</p>

<p>
	If you are requesting access to a particular project, 
	please let us know in the comments.
</p>	

<p>
	New accounts must be approved by an administrator before you may login.
	You will receive an email acknowledging your request, and a second email when your account is approved.
</p>

% if error:
	<div class="notify error">${error}</div>
% endif

% if invalid-set(['password','password2']):
	<div class="notify error">Please complete the following items marked in red</div>
% endif

<br />

<form action="${EMEN2WEBROOT}/users/new/" method="post">

${user_util.newuser_required(kwargs)}

<%include file="/pages/user.profile" />

<div class="e2l-controls">
	<input value="Create Account" type="submit" class="save">
</div>

</form>
	
