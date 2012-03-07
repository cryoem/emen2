<%! 
import jsonrpc.jsonutil
import operator 
import collections
%>

<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 
<%namespace name="user_util" file="/pages/user"  /> 

<%block name="js_ready">
	${parent.js_ready()}

	## Start map browser
	$('#content .e2-tree').TreeControl({'attach':true});

	## Recent activity viewer
	var q = ${jsonrpc.jsonutil.encode(recent_activity)}; 
	$('#recent_activity').PlotHistogram({
		q:q,
		pan: false,
		height:200,
	});
	
	## New record controls
	$('.e2-record-new').RecordControl({
		redirect:'/'
	});
	
	$('#activity time').timeago();
	
</%block>

<%
# bymonth = collections.defaultdict(set)
# for rec in recent_activity['recs']:
#	t = rec.get('creationtime')
#	n = rec.get('name')
#	year, month = t[0:4], t[5:7]
#	bymonth[(year,month)].add(n)	
# months = sorted(bymonth.keys())[-6:]

def sort_by_creationtime(x):
	c = projects_children.get(x) or [None]
	lastitem = sorted(c)[-1]
	return most_recent_recs.get(lastitem, dict()).get('creationtime')


if sortkey == 'children':
	lsortkey = lambda x:len(projects_children.get(x, []))
elif sortkey == 'activity':
	lsortkey = sort_by_creationtime
else:
	lsortkey = lambda x:recnames.get(x, '').lower()
	
%>

<%def name="sortlink(key, label)">
	% if key == sortkey:
		${buttons.image('sort_%s.png'%(int(not reverse)))}
		<a href="?sortkey=${key}&amp;reverse=${int(not reverse)}">${label}</a>
	% else:
		<a href="?sortkey=${key}">${label}</a>	
	% endif
</%def>





<h1>
	${USER.displayname}
	<ul class="e2l-actions">
		<li><a class="e2-button" href="${EMEN2WEBROOT}/user/${USER.name}/edit/">${buttons.image('edit.png')}  Edit Profile</a></li>
	</ul>
</h1>

<div class="e2l-cf">
	${user_util.profile(user=USER, userrec=USER.userrec, edit=False)}
</div>











<br /><br />

% if banner:
	<h1>
		Welcome to ${EMEN2DBNAME}
		% if banner.writable():
			<ul class="e2l-actions">
				<li><a class="e2-button" href="${EMEN2WEBROOT}/record/${banner.name}#edit">${buttons.image('edit.png')} Edit banner</a>
			</span>
		% endif
	</h1>
	<div>
	${render_banner}
	</div>
% endif









<br /><br />

<h1>
	Activity and recent records
	<ul class="e2l-actions">
		<li><a class="e2-button" href="${EMEN2WEBROOT}/query/">View all records</a></li>
	</ul>
</h1>

<div id="recent_activity">
	<div class="e2-plot"></div>
</div>

${recent_activity_table}










<br /><br />


<h1>
	Groups and projects	
	<ul class="e2l-actions">
		<a class="e2-button" href="${EMEN2WEBROOT}/sitemap/">Sitemap</a></li>

		% if hideinactive:
			<a class="e2-button" href="${EMEN2WEBROOT}/?hideinactive=0">Show inactive</a></li>
		% else:
			<a class="e2-button" href="${EMEN2WEBROOT}/?hideinactive=1">Hide inactive</a></li>		
		% endif
		
		% if ADMIN:
			<span class="e2-button e2-button e2-record-new" data-parent="0" data-rectype="group"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> New group</span>
		% endif
	</ul>
</h1>

<table id="activity" class="e2l-shaded" cellpadding="0" cellspacing="0">
	<thead>
		<tr>
			<th>
				${sortlink('name', 'Name')}
			</th>

			<th>
				${sortlink('children', 'Records')}
			</th>

			## <th style="width:80px">
			##	Activity
			## </th>
			
			<th colspan="2" style="width:150px">
				${sortlink('activity', 'Last activity')}
			</th>

		</tr>
	</thead>
	
	% for group, projects in groups_children.items():
	<tbody>

		<tr>
			<td style="background:#BBDAEE;" colspan="5">
				<a href="${EMEN2WEBROOT}/record/${group}/">
					<strong>Group: ${recnames.get(group,group)}</strong>
				</a>
				<ul class="e2l-actions">
				% if ADMIN:
					<li><span class="e2-button e2-record-new" data-parent="${group}" data-rectype="project">${buttons.image('edit.png','')} New project</span></li>
				% endif
				</ul>
			</td>
		</tr>
		
		<%
			skipped = 0
		%>
		
		% for project in sorted(projects, key=lsortkey, reverse=reverse):

			<%
				c = projects_children.get(project)
				lastitem = None
				if c:
					lastitem = most_recent_recs.get(sorted(c)[-1], dict())

				# Make a simple little inline chart showing distribution of record creation
				# chart = {}
				# for month in months:
				#	y = bymonth.get(month, set()) & projects_children.get(project, set())
				#	chart[month] = (float(len(y)) / float(len(c) or 1)) * 20
			%>

			% if hideinactive and lastitem is None:

			% else:
				<tr class="e2l-shaded-indent">
					<td><a href="${EMEN2WEBROOT}/record/${project}/">${recnames.get(project,project)}</a></td>

					<td>${len(projects_children.get(project, []))}</td>

					## <td>
					##	% for month in months:
					##		<div class="e2-plot-sparkbox" style="height:${chart[month]}px;margin-top:${20-chart[month]}px">&nbsp;</div>
					##	% endfor
					## </td>

					% if lastitem and most_recent_recs.get(lastitem.name):
						<td>
							<a href="${EMEN2WEBROOT}/record/${lastitem.name}">
								<time class="e2-timeago" datetime="${lastitem.get('creationtime')}">${lastitem.get('creationtime')}</time>
								by ${users.get(lastitem.get('creator'), dict()).get('displayname', lastitem.get('creator'))}
							</a>
						</td>
						
						<td></td>
					% else:
						<td colspan="2"></td>
					% endif

				</tr>
			% endif
		% endfor


		% if skipped:
			<tr class="e2l-shaded-indent">
				<td colspan="5">${skipped} inactive projects not shown.</td>
			</tr>
		% endif
		
		% if not projects:
			<tr class="e2l-shaded-indent">
				<td colspan="5">No children</td>
			</tr>
		% endif
		
	</tbody>
	% endfor

</table>





