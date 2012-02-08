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
	$('#content .e2-map').MapControl({'attach':true});

	## Recent activity viewer
	var q = ${jsonrpc.jsonutil.encode(recent_activity)}; 
	$('#recent_activity').PlotHistogram({
		q:q,
		pan: false,
		height:200,
	});
	
	$('.e2-button').button();

	## New record controls
	$('.e2-record-new').RecordControl({
		redirect:'/'
	});
	

</%block>

<h1>
	${USER.displayname}
	<ul class="e2l-actions">
		<a class="e2-button" href="${EMEN2WEBROOT}/user/${USER.name}/edit/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> Edit Profile</a></li>
	</ul>
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

<h1>Activity</h1>

<div id="recent_activity">
	<div class="e2-plot"></div>
</div>



<%
bymonth = collections.defaultdict(set)
for rec in recent_activity['recs']:
	t = rec.get('creationtime')
	n = rec.get('name')
	year, month = t[0:4], t[5:7]
	bymonth[(year,month)].add(n)
	
months = sorted(bymonth.keys())[-6:]

def asdf(x):
	c = projects_children.get(x) or [None]
	lastitem = sorted(c)[-1]
	return rendered_recs.get(lastitem, dict()).get('creationtime')


if sortkey == 'children':
	lsortkey = lambda x:len(projects_children.get(x, []))
elif sortkey == 'activity':
	lsortkey = asdf
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
	Groups
		
	<ul class="e2l-actions">
		<a target="_blank" class="e2-button" href="${EMEN2WEBROOT}/sitemap/">Sitemap</a></li>

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


<table class="e2l-shaded" cellpadding="0" cellspacing="0">
	<thead>
		<tr>
			<th>
				${sortlink('name', 'Name')}
			</th>

			<th>
				${sortlink('children', 'Children')}
			</th>

			<th style="width:80px">
				Activity
			</th>
			
			<th style="width:150px">
				${sortlink('activity', 'Last activity')}
			</th>

			<th></th>

		</tr>
	</thead>
	
	% for group, projects in groups_children.items():
	<tbody>

		<tr>
			<td style="background:#ccc" colspan="5">
				<a href="${EMEN2WEBROOT}/em/group/${group}/">${recnames.get(group,group)}</a>

				<ul class="e2l-actions">
				% if ADMIN:
					<li><span class="e2-button e2-record-new" data-parent="${group}" data-rectype="project">${buttons.image('edit.png','')} New project</span></li>
				% endif
			</td>
		</tr>
		
		% for project in sorted(projects, key=lsortkey, reverse=reverse):

			<%
				c = projects_children.get(project) or [None]
				lastitem = sorted(c)[-1]

				# Make a simple little inline chart showing distribution of record creation
				chart = {}
				for month in months:
					y = bymonth.get(month, set()) & projects_children.get(project, set())
					chart[month] = (float(len(y)) / float(len(c) or 1)) * 20
			%>

			% if hideinactive and lastitem is None:
			
			% else:
				<tr>
					<td style="padding-left:20px"><a href="${EMEN2WEBROOT}/record/${project}/">${recnames.get(project,project)}</a></td>

					<td>${len(projects_children.get(project, []))}</td>

					<td>
						% for month in months:
							<div class="e2-plot-sparkbox" style="height:${chart[month]}px;margin-top:${20-chart[month]}px">&nbsp;</div>
						% endfor
					</td>

					% if rendered_recs.get(lastitem):
						<td>
							<time class="e2-timeago" datetime="${rendered_recs.get(lastitem)['creationtime']}">${rendered_recs.get(lastitem)['creationtime']}</time>
						</td>
						<td>
							<a href="${EMEN2WEBROOT}/record/${lastitem}/">${recnames.get(lastitem, lastitem)}</a>
						</td>
					% else:
						<td colspan="2"></td>
					% endif
				</tr>
			% endif
		% endfor
	</tbody>
	% endfor

</table>





