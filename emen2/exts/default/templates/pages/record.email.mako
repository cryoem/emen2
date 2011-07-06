<%inherit file="/page" />


<div>

<% 
# sort by displayname...
import operator

s = []
for k in users_ref:
	u = users.get(k, {})
	s.append((u.get('displayname'), u.get('name'), u.get('email')))
s = sorted(s, key=operator.itemgetter(0))

%>

<h1>Users referenced in values</h1>

<table width="600">
	<tr>
		<th align="left">Name</th>
		<th align="left">Email</th>
	</tr>
	
	% for user, name, email in s:
		<tr>
			<td><a href="${EMEN2WEBROOT}/user/${name}/">${user}</a></td>
			<td><a href="mailto:${email}">${email}</a></td>
		</tr>
	% endfor

</table>



<%
s = []
for k in users_permissions:
	u = users.get(k, {})
	s.append((u.get('displayname'), u.get('name'), u.get('email')))
s = sorted(s, key=operator.itemgetter(0))
%>

<h1>Permissions</h1>

<table width="600">
	<tr>
		<th align="left">Name</th>
		<th align="left">Email</th>
	</tr>
	
	% for user, name, email in s:
		<tr>
			<td><a href="${EMEN2WEBROOT}/user/${name}/">${user}</a></td>
			<td><a href="mailto:${email}">${email}</a></td>
		</tr>
	% endfor

</table>



</div>

