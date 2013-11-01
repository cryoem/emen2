<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 
<%namespace name="forms" file="/forms"  /> 
<%namespace name="user_util" file="/pages/user"  /> 

<%block name="js_ready">
    ${parent.js_ready()}
    ${user_util.newuser_js_ready()}
</%block>

<h1>Welcome to ${TITLE}</h1>

<p>
    Please complete this form to create an account. 
</p>

## <p>
##    We request detailed contact information because this is included 
##    in our grant reports.
## </p>
## <p>
##    If you are requesting access to a particular project, 
##    please let us know in the comments.
## </p>    

<p>
    New accounts must be approved by an administrator before you may login.
    You will receive an email acknowledging your request, and a second email 
    when your account is approved.
</p>

<form action="${ctxt.root}/users/new/" method="post">

    <%buttons:singlepage label='Account Details'>
        <table class="e2l-kv">    
            <tbody> 

                <tr>
                    <td>First Name:</td>
                    <td><input name="user.name_first" type="text" value="${user.get('name_first','')}" required autocomplete="off" /></td>
                </tr>
                <tr>
                    <td>Middle Name:</td>
                    <td><input name="user.name_middle" type="text" value="${user.get('name_middle','')}" autocomplete="off" /></td>
                </tr>
                <tr>
                    <td>Last Name:</td>
                    <td><input name="user.name_last" type="text" value="${user.get('name_last','')}" required autocomplete="off" /></td>
                </tr>

                <tr>
                    <td>Email:</td>
                    <td><input name="user.email" type="email" value="${user.get('email','')}" required autocomplete="off" /></td>
                </tr>

                <tr>
                    <td>Password:</td>
                    <td>
                        <input name="password" type="password" required />
                        <span class="e2l-small">Minimum 8 characters</span>
                    </td>
                </tr>

                <tr>
                    <td>Confirm Password:</td>
                    <td>
                        <input name="user.password" type="password" required />
                        <span id="e2-newuser-passwordmatch" class="e2l-small"></span>
                    </td>
                </tr>
            </tbody>
        </table>
    </%buttons:singlepage>

    ## <%buttons:singlepage label='Profile'>
    ##    ${user_util.profile(userrec=userrec, edit=True)}
    ## </%buttons:singlepage>
    ## <%buttons:singlepage label='Comments'>
    ##    <p>Please let us know why you are requesting an account:</p>
    ##    <p>
    ##        <textarea class="e2l-fw" name="userrec.comments">${userrec.get('comments','')}</textarea>
    ##    </p>
    ## </%buttons:singlepage>

    <div class="e2l-controls">
        <input value="Create Account" type="submit" class="save">
    </div>

</form>
    
