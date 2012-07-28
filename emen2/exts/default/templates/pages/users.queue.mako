<%inherit file="/page" />
<%namespace name="forms" file="/forms"  /> 
<%namespace name="buttons"  file="/buttons"  /> 

<%block name="js_ready">
    ${parent.js_ready()}
    
    $('input[name=all]').click(function(){
        $('input[value='+$(this).val()+']').attr('checked', true);
    });
</%block>

<h1>${title}</h1>

<%buttons:singlepage label='Account requests'>
    <p>Showing ${len(queue)} of ${len(queue)} pending accounts.</p>
</%buttons:singlepage>

<br />

<form method="post" action="${ctxt.reverse('Users/queue')}">

<table class="e2l-shaded" cellpadding="0" cellspacing="0">
    <thead>
        <tr>

            <th style="width:16px">
                Approve
                ## <input type="radio" name="all" value="approve" />
            </th>
            <th style="width:16px">
                Reject
                ## <input type="radio" name="all" value="reject" />
            </th>
            
            <th>Groups</th>
            
            <th>Email</th>
            <th>Name</th>
            <th>Additional details</th>
        </tr>
    </thead>
    
    <tbody>
        % for user in queue:
            <tr>
                <td><input type="radio" name="actions.${user.name}" value="approve" ${forms.ifchecked(actions.get(user.name)=='approve')} /></td>
                <td><input type="radio" name="actions.${user.name}" value="reject" ${forms.ifchecked(actions.get(user.name)=='reject')} /></td>

                <td>                
                    <ul class="e2l-nonlist">    
                    % for group in groups:
                        <li>
                        % if group.name in groups_default:
                            <input type="checkbox" name="groups.${user.name}" checked="checked" value="${group.name}">${group.get('displayname', group.name)} 
                        % else:
                            <input type="checkbox" name="groups.${user.name}" value="${group.name}">${group.get('displayname', group.name)}     
                        % endif
                        </li>
                    % endfor
                    </ul>
                    <input type="hidden" name="groups.${user.name}" value="" />
                    <input type="hidden" name="groups.${user.name}" value="" />
                </td>

                <td>${user.email}</td>
                <td>${user.signupinfo.get('name_first', '')} ${user.signupinfo.get('name_middle', '')} ${user.signupinfo.get('name_last', '')}</td>
                <td>
                    <%
                    details = {}
                    for k in set(user.signupinfo.keys())-set(['email','name_first','name_middle','name_last','comments']):
                        details[k] = user.signupinfo[k]
                    %>
                    <ul class="e2l-nonlist">
                    % for k,v in sorted(details.items()):
                        <li>${k}: ${v}</li>
                    % endfor
                        <li>
                            Comments: ${user.signupinfo.get('comments', '')}
                        </li>
                    </ul>
                </td>
            </tr>
        % endfor
    </tbody>
</table>

<ul class="e2l-controls">
    <li><input type="submit" value="Save" /></li>
</u>

</form>