<%inherit file="/record/record" />

<%def name="emailtable(users)">
	<table class="e2l-kv e2l-shaded" cellpadding="0" cellspacing="0">
		<thead>
			<tr>
				<th>Name</th>
				<th>Email</th>
			</tr>	
		</thead>
		<tbody>
		% for user in sorted(users, key=lambda x:x.displayname):
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

${emailtable(users)}


<%
allemails = ['%s &lt;%s&gt;'%(user.displayname, user.email) for user in users]
%>

<h1>Distribution list</h1>

<p>Click to compose an email to all users:</p>

<div class="e2l-help"><a href="mailto:${', '.join([user.email for user in users])}">${','.join(allemails)}</a></div>

<p>Or copy and paste just the addresses:</p>

<div class="e2l-help">${', '.join([user.email for user in users])}</div>