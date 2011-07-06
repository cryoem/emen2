<%inherit file="/page" />


<%
import operator
import collections
import re

d = collections.defaultdict(list)
for group in groups:
	lastname = group.get('displayname', group.name)
	if lastname: lastname = lastname.upper()[0]
	else: lastname = "other"
	d[lastname].append(group)

for k,v in d.items():
	d[k] = sorted(v, key=lambda x:x.get('displayname', group.name).lower())

%>

<form method="post" action="${EMEN2WEBROOT}/groups/">
<h1>

	${title}

	<span class="label search">
		<input value="${q or ''}" name="q" type="text" size="8" />
		<input type="submit" value="Search" />
	</span>	
	
	% if admin:
		<span class="label"><a href="${EMEN2WEBROOT}/groups/new/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> New</a></span>
	% endif

</h1>
</form>

<ul class="buttons clearfix floatlist">
	<li>Last Name Index</li>
</ul>
<div class="page page_active">
	% for k in sorted(d.keys()):
		<a href="#${k}">${k}</a>
	% endfor
</div>



% for k in sorted(d.keys()):

<a name="${k}"></a>
<h1 class="clearfix">${k.capitalize()}</h1>

	% for group in d[k]:
	
		<div class="userbox">
			<a href="${EMEN2WEBROOT}/group/${group.name}/">
			<img src="${EMEN2WEBROOT}/static/images/group.png" alt="Group" />			
			</a>
			
			<div>
			<a href="${EMEN2WEBROOT}/group/${group.name}/">
			${group.get('displayname', group.name)}<br />
			${group.name}
			</a>
			</div>
			
		</div>
	
	% endfor

% endfor
