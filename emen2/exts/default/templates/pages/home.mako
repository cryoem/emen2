<%inherit file="/page" />

<%namespace name="buttons" file="/buttons"  /> 
<%namespace name="pages_user_util" file="/pages/user.util"  /> 
<%namespace name="table" file="/pages/table"  /> 


<%
import operator
from emen2.web.markuputils import HTMLTab
%>


<h1>
	${pages_user_util.page_title(user, False)} 
	<span class="e2l-label"><a href="${EMEN2WEBROOT}/user/${user.name}/edit/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> Edit Profile</a></span>
</h1>

<div class="e2l-clearfix">

	<div class="e2l-float-left">
		${pages_user_util.page_userrec(user, False)}
	</div>
	
	<div class="e2l-float-right">
		${pages_user_util.page_photo(user, False)}
	</div>


</div>


<br /><br />



<%
ctsearch = [[None, ctroot]]
rn = {}

while ctsearch:
	parent, child = ctsearch.pop()
	if parent == None:
		rn[child] = recnames.get(child,'child')		
	else:
		rn[child] = rn.get(parent,parent) + " / " + recnames.get(child,child)

	n = [(child,j) for j in childtree.get(child, [])]
	ctsearch.extend(n)
%>


% if banner:

<h1>
	Welcome to ${EMEN2DBNAME}
	% if banner.writable():
		<span class="e2l-label"><a href="${EMEN2WEBROOT}/record/${banner.name}/edit/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> Edit</a></span>
	% endif
</h1>

<div>
${render_banner}
</div>

% endif


<h1>Projects</h1>

% for name, recname in sorted(rn.items(), key=operator.itemgetter(1)):
	<a href="${EMEN2WEBROOT}/record/${name}/">${recname|x}</a><br />
% endfor

