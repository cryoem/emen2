<%! 
import jsonrpc.jsonutil
import operator 
import collections
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
	
	$('.e2-newrecord-test').NewRecordControl({
		redirect:'/'
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
bymonth = collections.defaultdict(set)
for rec in recent_activity['recs']:
	t = rec.get('modifytime')
	n = rec.get('name')
	modifytimes[n] = t
	year, month = t[0:4], t[5:7]
	bymonth[(year,month)].add(n)

months = sorted(bymonth.keys())[-6:]

counted = {}
for k,v in projects_children.items():
	v.add(k)
	counted[k] = sorted(v & recent_activity['names'], key=modifytimes.get)
%>


<h1>
	Instrument schedule
</h1>


<%buttons:singlepage label='Drag to calendar'>
	<div style="background:#ccc;float:left">Ian Rees</div>
</%buttons:singlepage>

<table class="e2l-shaded" cellpadding="0" cellspacing="0">
	<thead>
		<tr>
			<th>Instrument</th>
			<th>Monday</th>
			<th>Tuesday</th>
			<th>Wednesday</th>
			<th>Thursday</th>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td>JEOL 1400</td>
			<td></td>
			<td></td>
			<td>Ian</td>
			<td></td>
		</tr>
		<tr>
			<td>JEOL 2100</td>
			<td></td>
			<td>Ian</td>
			<td>Angel</td>
			<td></td>
		</tr>
</table>







<h1>
	Groups and projects
	% if ADMIN:
		<span class="e2l-label"><a class="e2-newrecord-test" data-rectype="group" data-parent="0" href="${EMEN2WEBROOT}/record/0/new/group/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> New Group</a></span>
	% endif
</h1>

<table class="e2l-shaded" cellpadding="0" cellspacing="0">
	<thead>
		<tr>
			<th>Project</th>
			<th>Activity</th>
			<th>Total records</th>
			<th>Last activity</th>
			<th>Progress report</th>			
		</tr>
	</thead>
	
	% for group, projects in groups_projects.items():
	<tbody>
		<tr>
			<td style="background:#ccc" colspan="0">
				<a href="${EMEN2WEBROOT}/record/${group}/">${groups_render.get(group,group)}</a>
				% if ADMIN:
					<span class="e2l-label e2l-float-right"><a class="e2-newrecord-test" data-parent="${group}" data-rectype="project" href="${EMEN2WEBROOT}/record/${group}/new/project/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> New Project</a></span>
				% endif
			</td>
		</tr>
		% for project in sorted(projects, reverse=True):
			<tr>
				<td style="padding-left:20px"><a href="${EMEN2WEBROOT}/record/${project}/">${projects_render.get(project,project)}</a></td>
				<%
					c = counted.get(project, set())
					chart = {}
					for month in months:
						y = bymonth.get(month, set()) & projects_children.get(project, set())
						chart[month] = (float(len(y)) / float(len(c) or 1)) * 30
						# chart[month] = (float(len(y)) / len(projects_children.get(project, []))) * 20
				%>
				<td style="width:80px">
					% for month in months:
						<div class="e2-plot-sparkbox" style="height:${chart[month]}px;margin-top:${30-chart[month]}px">&nbsp;</div>
					% endfor
				</td>
				<td>${len(projects_children.get(project, []))}</td>
				<td>
					...
					## ${len(bymonth.get(months[-1], set()) & projects_children.get(project, set()))}
				</td>
				<td>
					<a class="e2-newrecord-test" href="${EMEN2WEBROOT}/record/${project}/new/progress_report/" data-rectype="progress_report" data-parent="${project}">New progress report</a>
				</td>
			</tr>
		% endfor
	</tbody>
	% endfor

</table>
