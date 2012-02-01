<%! 
import jsonrpc.jsonutil
import operator 
%>
<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 
<%namespace name="user_util" file="/pages/user"  /> 

## Start map browser
<%block name="js_ready">
	${parent.js_ready()}
	$('#content .e2-map').MapControl({'attach':true});
	var q = ${jsonrpc.jsonutil.encode(recent_activity)}; 
	$('#recent_activity').PlotHistogram({
		q:q,
		pan: false,
		height:200,
	});
</%block>

<h1>
	${USER.displayname}
	<span class="e2l-label"><a href="${EMEN2WEBROOT}/user/${USER.name}/edit/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> Edit Profile</a></span>
</h1>

<div class="e2l-cf">
	${user_util.profile(user=USER, userrec=USER.userrec, edit=False)}
</div>


## % if banner:
##	<h1>
##		Welcome to ${EMEN2DBNAME}
##		% if banner.writable():
##			<span class="e2l-label">
##				<a href="${EMEN2WEBROOT}/record/${banner.name}/edit/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> Edit</a>
##			</span>
##		% endif
##	</h1>
##
##	<div>
##	${render_banner}
##	</div>
## % endif

<h1>Recent activity</h1>

<div id="recent_activity">
	<div class="e2-plot"></div>
</div>

<br /><br />


<%
modifytimes = {}
for rec in recent_activity['recs']:
	modifytimes[rec.get('name')] = rec.get('modifytime')

counted = {}
for k,v in projects_children.items():
	v.add(k)
	counted[k] = sorted(v & recent_activity['names'], key=modifytimes.get)

%>

<h1>
	Projects
</h1>

<table>
	<thead>
		<tr>
			<th>Project</th>
			<th>Total</th>
			<th>Last 90 days</th>
			<th>Last activity</th>
		</tr>
	</thead>
	
	% for group, projects in groups_projects.items():
	<tbody>
		<tr>
			<td colspan="0">- ${group} -</td>
		</tr>
		% for project in projects:
			<tr>
				<td>${projects_render.get(project,project)}</td>
				<td>${len(projects_children.get(project, []))}</td>
				<td>${len(counted.get(project, []))}</td>
				<td>
					% if counted.get(project, []):
						<%
							lastcounted = counted.get(project, [])[0]
							lasttime = modifytimes.get(lastcounted)
						%>
						<time datetime="${lasttime}">${lasttime}</time>
					% else:
						<em></em>
						## <em>&gt; 6mo. ago</em>
					% endif
				</td>
			</tr>
		% endfor
	</tbody>
	% endfor

</table>
