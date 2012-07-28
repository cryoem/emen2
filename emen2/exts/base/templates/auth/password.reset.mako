<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

<h1>${title}</h1>

% if secret:
    <p>Please enter a new password to complete the password reset process.</p>
% else:
    <p>Forgot your password? Please enter your email below, and the system will attempt to locate your account details and email you a link to reset your password.</p>    
% endif


<form method="post" action="">
    <table cellpadding="0" cellspacing="0">
    % if not secret:
        <tr>
            <td>Email:</td>
            <td><input type="text" name="email" value="${email or ''}" /></td>
        </tr>
    % else:
        <tr>
            <td>Email:</td>
            <td>${email or ''}</td>
        </tr><tr>
            <td>New Password:</td>
            <td><input type="password" name="newpassword" value="" /></td>
        </tr>
    % endif

        <tr>
            <td />
            <td><input type="submit" value="Submit" /></td>
        </tr>

    </table>
</form>
