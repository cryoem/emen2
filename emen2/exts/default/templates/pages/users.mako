<%inherit file="/page" />


<form method="post" action="${EMEN2WEBROOT}/users/">
<h1>
	${title}

	<span class="label search">
		<input value="${q or ''}" name="q" type="text" size="8" />
		<input type="submit" value="Search" />
	</span>

	<span class="label"><a href="${EMEN2WEBROOT}/users/new/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> New</a></span>

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


<div class="clearfix"><div class="infobuttons">Last Name Index</div></div>
<div class="info">

	% for k in sorted(d.keys()):

		<a href="#${k}">${k}</a>

	% endfor

</div>




% for k in sorted(d.keys()):

<a name="${k}"></a>
<h1 class="clearfix">${k.capitalize()}</h1>

	% for user in d[k]:
	
		<div class="userbox">
			<a href="${EMEN2WEBROOT}/user/${user.name}/">
			% if user.userrec.get('person_photo'):
				<img src="${EMEN2WEBROOT}/download/${user.userrec.get('person_photo')}/${user.name}.jpg?size=thumb" alt="Photo" />
			% else:
				<img src="${EMEN2WEBROOT}/static/images/nophoto.png" alt="Photo" />			
			% endif
			</a>
			
			<div>
			<a href="${EMEN2WEBROOT}/user/${user.name}/">
			${user.displayname}
			% if user.email and user.email != 'None':
				<br />
				${user.email}
			% endif
			</a>
			</div>
			
		</div>
	
	% endfor

% endfor