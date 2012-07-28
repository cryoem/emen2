<%inherit file="/page" />
<%namespace name="buttons"  file="/buttons"  /> 


<form method="post" action="${EMEN2WEBROOT}/users/">
<h1>
    ${title}
    <ul class="e2l-actions">
        <li>
            <a class="e2-button" href="${EMEN2WEBROOT}/users/new/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> New</a>
        </li>
        <li>
            <input value="${q or ''}" name="q" type="text" size="8" />
            <input type="submit" value="Search" />
        </li>
    </ul>
</h1>
</form>



<%
import operator
import collections
import re

d = collections.defaultdict(list)
for user in users:
    lastname = user.userrec.get("name_last")
    if lastname: lastname = lastname.upper()[0]
    else: lastname = "other"
    d[lastname].append(user)

for k,v in d.items():
    d[k] = sorted(v, key=lambda x:x.userrec.get('name_last', '').lower())

%>


<%buttons:singlepage label='Last Name Index'>
    % for k in sorted(d.keys()):
        <a href="#${k}">${k}</a>
    % endfor
    <p>Showing ${len(users)} of ${len(usernames)} users.</p>
</%buttons:singlepage>



% for k in sorted(d.keys()):

<a name="${k}"></a>
<h1 class="e2l-cf">${k.capitalize()}</h1>
    % for user in d[k]:
        ${buttons.infobox(user, autolink=True)}
    % endfor

% endfor