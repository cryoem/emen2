<%inherit file="/page" />
<%namespace name="buttons"  file="/buttons"  /> 


<form method="post" action="${EMEN2WEBROOT}/paramdefs/name/">
<h1>

	Parameters by Physical Property

	<span class="e2l-label">
		<input value="${q or ''}" name="q" type="text" size="8" />
		<input type="submit" value="Search" />
	</span>

	% if create:
		<span class="e2l-label"><a href="${EMEN2WEBROOT}/paramdef/root/new/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> New</a></span>
	% endif
</h1>
</form>


<%
import operator
import collections
import re

d = collections.defaultdict(list)
for paramdef in paramdefs:
	d[paramdef.property].append(paramdef)

for k,v in d.items():
	d[k] = sorted(v, key=lambda x:x.get('name', '').lower())

%>


<%buttons:singlepage label='Index'>
	<ul>
	% for k in sorted(d.keys()):
		<li><a href="#${k}">${str(k).capitalize()}</a></li>
	% endfor
	</ul>
</%buttons:singlepage>


% for k in sorted(d.keys()):

<a name="${k}"></a>
<h1 class="e2l-cf">${str(k).capitalize()}</h1>

	% for paramdef in d[k]:
		${buttons.infobox(paramdef, autolink=True)}
	% endfor

% endfor