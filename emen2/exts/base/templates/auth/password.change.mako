<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

<h1>${ctxt.title}</h1>

<form action="${ctxt.root}/auth/password/change/" method="post">

    <input type="hidden" name="name" value="${name or ''}" />

    <table class="e2l-kv">
        <tr>
            <td>Current password</td>
            <td>
        % if ADMIN:
            <input type="password" disabled="disabled" placeholder="Admin" /> <span class="e2l-small">(Admin may directly change email)</span>
        % else:
            <input type="password" name="opw" value="" /> <span class="e2l-small">(required to change email)</span>
        % endif
    </td>
    </tr>

        <tr><td>New password:</td><td><input type="password" name="on1" /></td></tr>
        <tr><td>Confirm new password:</td><td><input type="password" name="on2" /></td></tr>

        <tr><td></td><td><input type="submit" value="Change Password" /></td></tr>
    
    </table>
</form>
