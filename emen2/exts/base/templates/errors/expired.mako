<%inherit file="/page" />

<h1>Expired password</h1>

<p>Your password has expired. You must create a new password before you can login.</p>

<form action="${ctxt.root}/auth/password/change/" method="post">
    <input type="hidden" name="name" value="${name or ''}" />
    <table class="e2l-kv">
        <tr><td>Current password:</td><td><input type="password" name="opw" /></td></tr>
        <tr><td>New password:</td><td><input type="password" name="on1" /></td></tr>
        <tr><td>Confirm new password:</td><td><input type="password" name="on2" /></td></tr>
        <tr><td></td><td><input type="submit" value="Change Password" /></td></tr>
    </table>
</form>
