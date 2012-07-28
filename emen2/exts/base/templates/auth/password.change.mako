<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

<h1>${title}</h1>

<form action="${EMEN2WEBROOT}/auth/password/change/" method="post">

    <input type="hidden" name="location" value="${location}" />
    <input type="hidden" name="name" value="${name or ''}" />

    <table class="e2l-kv">
        % if not admin:
            <tr><td>Current password:</td><td><input type="password" name="opw" /></td></tr>
        % endif
        <tr><td>New password:</td><td><input type="password" name="on1" /></td></tr>
        <tr><td>Confirm new password:</td><td><input type="password" name="on2" /></td></tr>

        <tr><td /><td><input type="submit" value="Change Password" /></td></tr>
    
    </table>
</form>
