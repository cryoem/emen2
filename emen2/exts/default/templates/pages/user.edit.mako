<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 
<%namespace name="user_util" file="/pages/user" /> 

<h1>${user.displayname}</h1>

% if user.name != 'root' and user.userrec:

    <%buttons:singlepage label='Profile'>

        <form method="post" enctype="multipart/form-data" action="${ROOT}/record/${user.record}/edit/">

            <input type="hidden" name="_redirect" value="${ctxt.reverse('User/edit', name=user.name, saved='profile')}" />
        
            ${user_util.profile(user=user, userrec=user.userrec, edit=True, prefix='')}

            <table class="e2l-kv">
                <tbody>
                    <tr>
                        <td>Select a new photo:</td>
                        <td>

                            % if user.userrec.get('person_photo'):
                                <% pf_url = ROOT + "/download/" + user.userrec.get('person_photo') + "/user.jpg" %>
                                <a href="${pf_url}"><img src="${pf_url}?size=small" class="e2l-thumbnail-mainprofile" alt="profile photo" /></a>
                                <input type="hidden" name="person_photo" value="${user.userrec.get('person_photo')}" />
                            % else:
                                <div>There is currently no photo.</div>
                            % endif

                            <p>
                                <input type="file" name="person_photo"/>
                            </p>


                        </td>
                    </tr>
                </tbody>
            </table>

            ${buttons.save('Save profile')}

        </form>
    </%buttons:singlepage>

% endif



<%buttons:singlepage label='Change email'>
    <form method="post" action="${ROOT}/auth/email/change/">

        ## <input type="hidden" name="_redirect" value="${ctxt.reverse('User/edit', name=user.name, saved='email')}" />
        <input type="hidden" name="name" value="${user.name or ''}" />

        <table class="e2l-kv">
            <tbody>
                <tr>
                    <td>Current password:</td>
                    <td><input type="password" name="opw" value="" /> <span class="e2l-small">(required to change email)</span></td>
                </tr>
                </tr>
                    <td>New email:</td>
                    <td><input type="text" name="email" value="${user.get('email','')}" /></td>
                </tr>
            </tbody>
        </table>

        ${buttons.save('Change email')}

    </form>
</%buttons:singlepage>



<%buttons:singlepage label='Change password'>
    <form action="${ROOT}/auth/password/change/" method="post">

        ## <input type="hidden" name="_redirect" value="${ctxt.reverse('User/edit', name=user.name, saved='password')}" />
        <input type="hidden" name="name" value="${user.name or ''}" />

        <table class="e2l-kv">
            <tbody>
                <tr>
                    <td>Current password:</td>
                    <td><input type="password" name="opw" /></td>
                </tr>
                <tr>
                    <td>New password:</td>
                    <td><input type="password" name="on1" /></td>
                </tr>
                <tr>
                    <td>Confirm new password:</td>
                    <td><input type="password" name="on2" /></td>
                </tr>
            </tbody>
        </table>

        ${buttons.save('Change password')}

    </form>
</%buttons:singlepage>



<%buttons:singlepage label='Set privacy'>
    Who may view your account information:
        
    <form method="post" action="${ctxt.reverse('User/edit', name=user.name)}">
        <input type="hidden" name="_redirect" value="${ctxt.reverse('User/edit', name=user.name, saved='privacy')}" />    
        <input type="radio" name="user.privacy" value="0" ${['checked="checked"','',''][user.privacy]}> Public <br />
        <input type="radio" name="user.privacy" value="1" ${['','checked="checked"',''][user.privacy]}> Only authenticated users<br />
        <input type="radio" name="user.privacy" value="2" ${['','','checked="checked"'][user.privacy]}> Private<br />
        ${buttons.save('Set privacy level')}
    </form>        
</%buttons:singlepage>



% if ADMIN:
    <%buttons:singlepage label='Account status'>
        <form method="post" action="${ctxt.reverse('User/edit', name=user.name)}">
            <input type="hidden" name="_redirect" value="${ctxt.reverse('User/edit', name=user.name, saved='status')}" />        
            <input type="radio" name="user.disabled" value="" ${['checked="checked"',''][user.disabled]}> Enabled <br />
            <input type="radio" name="user.disabled" value="True" ${['','checked="checked"'][user.disabled]}> Disabled
            ${buttons.save('Set account status')}
        </form>
    </%buttons:singlepage>
% endif



<%buttons:singlepage label='History'>
    <p>Created: <time class="e2-localize" datetime="${user.get("creationtime")}">${user.get("creationtime")}</time></p>
    <p>Modified: <time class="e2-localize" datetime="${user.get("modifytime")}">${user.get("modifytime")}</time></p>
</%buttons:singlepage>



## <%buttons:singlepage label='Groups'>
## </%buttons:singlepage>

