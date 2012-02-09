<%inherit file="/page" />
<%namespace name="buttons"  file="/buttons"  /> 

<form method="post" action="${EMEN2WEBROOT}/paramdefs/name/">
<h1>
	${title}
	<ul class="e2l-actions">
		<li>
			<input value="${q or ''}" name="q" type="text" size="8" />
			<input type="submit" value="Search" />
		</li>
		% if create:
			<li><a class="e2-button" href="${EMEN2WEBROOT}/paramdef/root/new/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> New</a></li>
		% endif
	</ul>

	<span class="e2l-label">
	</span>
</h1>
</form>

<%
import operator
import collections
import re

d = collections.defaultdict(list)
for paramdef in paramdefs:
	d[paramdef.name[0].upper()].append(paramdef)

for k,v in d.items():
	d[k] = sorted(v, key=lambda x:x.get('name', '').lower())

%>


<%buttons:singlepage label='Index'>
	% for k in sorted(d.keys()):
		<a href="#${k}">${k}</a>
	% endfor
	<p>Showing ${len(paramdefs)} of ${len(paramdefnames)} parameters.</p>	
</%buttons:singlepage>



% for k in sorted(d.keys()):
	<a name="${k}"></a>
	<h1 class="e2l-cf">${str(k).capitalize()}</h1>
	% for paramdef in d[k]:
		${buttons.infobox(paramdef, autolink=True)}
	% endfor
% endfor