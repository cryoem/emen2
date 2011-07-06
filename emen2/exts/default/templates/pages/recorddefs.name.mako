<%inherit file="/page" />

<form method="post" action="${EMEN2WEBROOT}/recorddefs/name/">
<h1>
	${title}

	<span class="label search">
		<input value="${q or ''}" name="q" type="text" size="8" />
		<input type="submit" value="Search" />
	</span>

	% if create:
		<span class="label"><a href="${EMEN2WEBROOT}/recorddef/root/new/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> New</a></span>
	% endif

</h1>
</form>


<%
import operator
import collections
import re

d = collections.defaultdict(list)
for recorddef in recorddefs:
	d[recorddef.name[0].upper()].append(recorddef)

for k,v in d.items():
	d[k] = sorted(v, key=lambda x:x.get('name', '').lower())

%>


<div class="clearfix"><div class="infobuttons">Protocol Name Index</div></div>
<div class="info">

	% for k in sorted(d.keys()):

		<a href="#${k}">${k}</a>

	% endfor

</div>


% for k in sorted(d.keys()):

<a name="${k}"></a>
<h1 class="clearfix">${str(k).capitalize()}</h1>

	% for recorddef in d[k]:
	
		<div class="userbox">
			<a href="${EMEN2WEBROOT}/recorddef/${recorddef.name}/">
				<img src="${EMEN2WEBROOT}/static/images/gears.png" alt="Protocol" />
			</a>
			
			<div>
				<a href="${EMEN2WEBROOT}/recorddef/${recorddef.name}/">
				${recorddef.desc_short}

				% if count.get(recorddef.name) > 0:
					(${count[recorddef.name]} records)				
				% endif

				<br />
				${recorddef.name}
				</a>
			</div>
			
		</div>
	
	% endfor

% endfor