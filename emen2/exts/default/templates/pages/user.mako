<%! import jsonrpc.jsonutil %>
<%namespace name="buttons" file="/buttons"  />
<%namespace name="forms" file="/forms"  /> 

## JavaScript for client-side initial validation and error
## reporting for New User form

<%def name="newuser_js_ready(minimum=6)">
    $('input[name=password]').change(function(){
        if ($(this).val().length < 6) {
            this.setCustomValidity('Minimum password length is 6');
        } else {
            this.setCustomValidity('');
        }
    });
    
    $('input[name=user\\.password]').change(function() {
        var op1 = $(this).val();
        var op2 = $('input[name=password]').val();
        var msg = '';
        if (op1 != op2) {
            msg = 'Passwords did not match';
        } else if (op1.length < 8 || op2.length < 8) {
            msg = 'Minimum password length is 8';
        }
        $('#e2-newuser-passwordmatch').html(msg || 'Ok');
        this.setCustomValidity(msg);
    });    
</%def>

<%def name="profile(user=None, userrec=None, edit=False, prefix='userrec.')">
    % if edit:
        <table class="e2l-kv">    
            <tbody>                    
                <tr>
                    <td>First Name:</td>
                    <td><input name="name_first" type="text" value="${userrec.get('name_first','')}" required /></td>
                </tr>
                <tr>
                    <td>Middle Name:</td>
                    <td><input name="name_middle" type="text" value="${userrec.get('name_middle','')}" /></td>
                </tr>
                <tr>
                    <td>Last Name:</td>
                    <td><input name="name_last" type="text" value="${userrec.get('name_last','')}" required /></td>
                </tr>
                
                ## <tr>
                ##    <td>Phone:</td>
                ##    <td><input name="${prefix}phone" type="text" value="${userrec.get('phone','')}"></td>
                ## </tr>
                ## <tr>
                ##    <td>Web page:</td>
                ##    <td><input name="${prefix}website" type="text" value="${userrec.get('website','')}"></td>
                ## </tr>
                ## <tr>
                ##    <td>Fax:</td>
                ##    <td><input name="${prefix}phone_fax" type="text" value="${userrec.get('phone_fax','')}"></td>
                ## </tr>
                ## <tr>
                ##     <td>Institution:</td>
                ##     <td><input name="${prefix}institution" type="text" value="${userrec.get('institution','')}" required /></td>
                ## </tr>
                ## <tr>
                ##     <td>Department:</td>
                ##     <td><input name="${prefix}department" type="text" value="${userrec.get('department','')}" required /></td>
                ## </tr>
                ## <tr>
                ##     <td>Street Address:</td>
                ##     <td><input name="${prefix}address_street" type="text" value="${userrec.get('address_street','')}" required /></td>
                ## </tr>
                ## <tr>
                ##     <td>City:</td>
                ##     <td><input name="${prefix}address_city" type="text" value="${userrec.get('address_city','')}" required /></td>
                ## </tr>
                ## <tr>
                ##     <td>State:</td>
                ##     <td><input name="${prefix}address_state" type="text" value="${userrec.get('address_state','')}" required /></td>
                ## </tr>
                ## <tr>
                ##     <td>Zipcode:</td>
                ##     <td><input name="${prefix}address_zipcode" type="text" value="${userrec.get('address_zipcode','')}" required /></td>
                ## </tr>
                ## <tr>
                ##     <td>Country:</td>
                ##     <td>            
                ##         <select name="${prefix}country" required />
                ##             ${forms.countries()}
                ##         </select>
                ##         <script type="text/javascript">
                ##             var country = ${userrec.get('country','United States') | n,jsonencode};
                ##             $('select[name=userrec\\.country]').val(country);
                ##         </script>
                ##     </td>
                ## </tr>            
            </tbody>
        </table>

    % else:
    
        % if user.userrec.get('person_photo'):
            <% pf_url = ctxt.root + "/download/" + user.userrec.get('person_photo') + "/user.jpg" %>
            <a class="e2l-float-right" href="${pf_url}"><img src="${pf_url}?size=small" class="e2l-thumbnail-mainprofile" alt="profile photo" /></a>
        % endif
    
        <table style="width:auto;">
            <tbody>
                <tr>
                    <td>Department:</td>
                    <td>${userrec.get('department', '')}</td>
                </tr>
                <tr>
                    <td>Institution:</td>
                    <td>${userrec.get('institution', '')}</td>
                </tr>
                <tr>
                    <td>Address:</td>
                    <td>
                        ${userrec.get('address_street', '')}<br />
                        ${userrec.get('address_street2', '')}<br />
                        ${userrec.get('address_city', '')},    ${userrec.get('address_state', '')} ${userrec.get('address_zipcode', '')}<br />
                        ${userrec.get('country', '')}
                    </td>
                </tr>
                <tr>
                    <td>Email:</td>
                    <td><a href="mailto:${user.email}">${user.email}</a></td>
                </tr>
                <tr>
                    <td>Phone:</td>
                    <td>${userrec.get('phone', '')}</td>
                </tr>
                <tr>
                    <td>Web:</td>
                    <td>${userrec.get('website', '')}</td>
                </tr>
            </tbody>
        </table>

            
    % endif

</%def>

