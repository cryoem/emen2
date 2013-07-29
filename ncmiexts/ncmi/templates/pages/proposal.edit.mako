<%inherit file="/page" />

% if user==None:

<p>You must request a <a href="${ctxt.root}/users/new/">new user account</a> to begin the proposal process. Please enter all contact information.</p>

<p>If you have created your account, please <a href="${ctxt.root}/login/?uri=${ctxt.root}/proposals/edit/">login to begin</a>.</p>

% else:

edit proposal...

% endif