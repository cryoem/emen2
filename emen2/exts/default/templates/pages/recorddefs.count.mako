<%inherit file="/page" />
<%namespace name="buttons"  file="/buttons"  /> 

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

groupings = [-1, 0, 10, 100, 1000, 10000]
labels = {
	-1: "No Records",
	0: "1 - 10 Records",
	10: "10 - 100 Records",
	100: "100 - 1,000 Records",
	1000: "1,000 - 10,000 Records",
	10000: "More than 10,000 Records"
}


d = collections.defaultdict(list)
for recorddef in recorddefs:
	group = groupings[[count.get(recorddef.name, 0)<=i for i in groupings].count(False)-1]
	d[group].append(recorddef)

for k,v in d.items():
	d[k] = sorted(v, key=lambda x:x.get('name', '').lower())

%>


<div class="clearfix"><div class="infobuttons">Protocol Name Index</div></div>
<div class="info">

	% for k in sorted(d.keys(), reverse=True):
		<a href="#${k}">${k}</a>  
	% endfor

</div>


% for k in sorted(d.keys(), reverse=True):

<a name="${k}"></a>
<h1 class="clearfix">${labels.get(k)}</h1>

	% for recorddef in d[k]:
		<%
		c = count[recorddef.name]
		body = '%s records'%c
		if c == 1:
			body = '1 record'
		if not c:
			body = 'No records'
		%>

		${buttons.infobox(recorddef, body=body, autolink=True)}
	% endfor

% endfor