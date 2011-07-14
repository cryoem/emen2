<%inherit file="/page" />

<%def name="emailtable(users)">
	<table>
		<thead>
			<tr>
				<th>Name</th>
				<th>Email</th>
			</tr>	
		</thead>
		<tbody>
		% for user in users:
			<tr>
				<td><a href="${EMEN2WEBROOT}/user/${user.name}/">${user.displayname}</a></td>
				<td><a href="mailto:${user.email}">${user.email}</a></td>
			</tr>
		% endfor
		</tbody>
	</table>
</%def>

<h1>All Users</h1>

${emailtable(users)}
