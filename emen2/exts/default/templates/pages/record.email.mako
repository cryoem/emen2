<%inherit file="/page" />

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

<h1>${title}</h1>

${emailtable(users)}


<%
allemails = ['%s &lt;%s&gt;'%(user.displayname, user.email) for user in users]
%>

<h1>Distribution list</h1>

<a href="mailto:${','.join([user.email for user in users])}">${','.join(allemails)}</a>