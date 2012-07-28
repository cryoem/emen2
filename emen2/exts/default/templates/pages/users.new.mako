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
    We request detailed contact information because this is included 
    in our grant reports.
</p>

<p>
    If you are requesting access to a particular project, 
    please let us know in the comments.
</p>    

<p>
    New accounts must be approved by an administrator before you may login.
    You will receive an email acknowledging your request, and a second email 
    when your account is approved.
</p>

<form action="${EMEN2WEBROOT}/users/new/" method="post">

    <%buttons:singlepage label='Account Details'>
        ${user_util.newuser(user=user)}
    </%buttons:singlepage>

    <%buttons:singlepage label='Profile'>
        ${user_util.profile(userrec=userrec, edit=True)}
    </%buttons:singlepage>

    <%buttons:singlepage label='Comments'>
        <p>Please let us know why you are requesting an account:</p>
        <p>
            <textarea class="e2l-fw" name="userrec.comments">${userrec.get('comments','')}</textarea>
        </p>
    </%buttons:singlepage>

    <div class="e2l-controls">
        <input value="Create Account" type="submit" class="save">
    </div>

</form>
    
