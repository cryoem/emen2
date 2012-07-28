<%inherit file="/record/record" />

<%def name="emailtable(emailusers)">
    <table class="e2l-kv e2l-shaded" cellpadding="0" cellspacing="0">
        <thead>
            <tr>
                <th>Name</th>
                <th>Email</th>
            </tr>    
        </thead>
        <tbody>
        % for user in sorted(emailusers, key=lambda x:x.displayname):
            <tr>
                <td><a href="${EMEN2WEBROOT}/user/${user.name}/">${user.displayname}</a></td>
                <td><a href="mailto:${user.email}">${user.email}</a></td>
            </tr>
        % endfor
        </tbody>
    </table>
</%def>

<h1>
    Email users 
    ## referenced by ${recnames.get(rec.name, rec.name)}
</h1>

## <div class="e2l-help">This asdf.</div>

<p>This page lists all users who are referenced by the record. This includes users users referenced by a parameter (e.g. project investigators), as well as those listed in the permissions.</p>


${emailtable(emailusers)}

<br />

<%
allemails = ['%s &lt;%s&gt;'%(user.displayname, user.email) for user in emailusers]
%>

<h1>Distribution list</h1>

<p>Click to compose an email to all users:</p>

<div class="e2l-help"><a href="mailto:${', '.join([user.email for user in emailusers])}">${','.join(allemails)}</a></div>

<p>Or copy and paste just the addresses:</p>

<div class="e2l-help">${', '.join([user.email for user in emailusers])}</div>