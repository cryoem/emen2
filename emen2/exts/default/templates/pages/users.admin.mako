<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />
<%namespace name="pages_user_util" file="/pages/user"  /> 


<p>
	<form method="post" action="${EMEN2WEBROOT}/users/admin/">
		% if q:
			<input type="text" name="q" length="30" value="${q}" />
		% else:
			<input type="text" name="q" length="30" />
		% endif
		<input type="submit" value="Search" />
	</form>	
</p>

<br /><br />


<%
for user in users:
	user.getdisplayname(lnf=True)

if sortby == "name":
	sortkey = lambda x:x.get('name','').lower()
elif sortby == "email":
	sortkey = lambda x:x.get('email','').lower()
elif sortby == "domain":
	sortkey = lambda x:x.get('email','').partition("@")[2]
elif sortby == "displayname":
	sortkey = lambda x:x.get('displayname','').lower()
elif sortby == 'disabled':
	sortkey = lambda x:x.disabled	
else:
	sortkey = lambda x:x.userrec.get(sortby,'').lower()

users_sorted = sorted(users, key=sortkey, reverse=reverse)
%>

<form name="form_admin_userlist">
	<table cellpadding="0" cellspacing="0" class="e2l-shaded" width="100%" >
		<thead>
			<tr>
				<th><a href="${EMEN2WEBROOT}/users/admin/?sortby=disabled">Active</a></th>
				<th><a href="${EMEN2WEBROOT}/users/admin/?sortby=disabled">Disabled</a></th>
				<th><a href="${EMEN2WEBROOT}/users/admin/?sortby=name">Account Name</a></th>
				<th><a href="${EMEN2WEBROOT}/users/admin/?sortby=displayname">Name</a></th>
				<th><a href="${EMEN2WEBROOT}/users/admin/?sortby=email">Email</a> (<a href="${EMEN2WEBROOT}/users/admin/?sortby=domain">sort by domain</a>)</th>
			</tr>
		</thead>
		<tbody>
			% for sh, user in enumerate(users_sorted):
				<tr ${['','class="s"'][sh%2]}>
					% if not user.disabled:
						<td><input type="radio" name="${user.name}" checked="1" value="0" /></td>
						<td><input type="radio" name="${user.name}" value="1" /></td>			
					% else:
						<td><input type="radio" name="${user.name}" value="0" /></td>
						<td><input type="radio" name="${user.name}" checked="1" value="1" /></td>			
					% endif
					<td><a href="${EMEN2WEBROOT}/user/${user.name}/edit/">${user.name}</a></td>
					<td>${user.displayname}</td>
					<td>${user.get('email','')}</td>
				</tr>
			% endfor
		</tbody>
	</table>

	<ul class="e2l-controls">
		<li><input type="submit" value="Save" /></li>
	</ul>
	
</form>

