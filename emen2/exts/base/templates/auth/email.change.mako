<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

<h1>${ctxt.title}</h1>

<form method="post" action="${ROOT}/auth/email/change/">

    <input type="hidden" name="name" value="${name or ''}" />

    <table>
        % if not admin:
            <tr><td>Current password:</td><td><input type="password" name="opw" /></td></tr>        
        % endif
    
        <tr><td>New email:</td><td><input type="text" name="email" value="${email or ''}" /></td>
        <tr><td></td><td><input type="submit" value="Change Email" name="save"></td></tr>

    </table>

</form>

