<%inherit file="/page" />


<form method="post" action="${EMEN2WEBROOT}/paramdefs/name/">
<h1>

	Parameters by Physical Property

	<span class="label search">
		<input value="${q or ''}" name="q" type="text" size="8" />
		<input type="submit" value="Search" />
	</span>

	% if create:
		<span class="label"><a href="${EMEN2WEBROOT}/paramdef/root/new/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> New</a></span>
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


<div class="clearfix"><div class="infobuttons">Parameter Property Index</div></div>
<div class="info">

	% for k in sorted(d.keys()):

		<a href="#${k}">${k}</a>

	% endfor

</div>


% for k in sorted(d.keys()):

<a name="${k}"></a>
<h1 class="clearfix">${str(k).capitalize()}</h1>

	% for paramdef in d[k]:
	
		<div class="userbox">
			<a href="${EMEN2WEBROOT}/paramdef/${paramdef.name}/">
				<img src="${EMEN2WEBROOT}/static/images/gears.png" alt="Parameter" />			
			</a>
			
			<div>
				<a href="${EMEN2WEBROOT}/paramdef/${paramdef.name}/">
				${paramdef.desc_short}<br />
				${paramdef.name}
				</a>
			</div>
			
		</div>
	
	% endfor

% endfor