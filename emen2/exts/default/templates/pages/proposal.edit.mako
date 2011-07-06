<%inherit file="/page" />

% if user==None:

<p>You must request a <a href="${EMEN2WEBROOT}/users/new/">new user account</a> to begin the proposal process. Please enter all contact information.</p>

<p>If you have created your account, please <a href="${EMEN2WEBROOT}/login/?uri=${EMEN2WEBROOT+"/proposals/edit/"|u}">login to begin</a>.</p>

% else:

edit proposal...

% endif