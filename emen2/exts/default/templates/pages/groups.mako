<%inherit file="/page" />
<%namespace name="buttons"  file="/buttons"  /> 


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
	<ul class="e2l-actions">
		<li>
			<input value="${q or ''}" name="q" type="text" size="8" />
			<input type="submit" value="Search" />
		</li>
		% if admin:
			<li><a class="e2-button" href="${EMEN2WEBROOT}/groups/new/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> New</a></li>
		% endif
	</ul>
</h1>
</form>

<%buttons:singlepage label='Index'>
	% for k in sorted(d.keys()):
		<a href="#${k}">${k}</a>
	% endfor
	<p>Showing ${len(groups)} of ${len(groupnames)} user groups.</p>	
</%buttons:singlepage>



% for k in sorted(d.keys()):

<a name="${k}"></a>
<h1 class="e2l-cf">${k.capitalize()}</h1>

	% for group in d[k]:
		<%buttons:infobox item="${group}" autolink="True" />
	% endfor

% endfor
