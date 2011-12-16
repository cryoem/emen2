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

<h1>
	Equipment
	% if ADMIN:
		% for rd in equipment_rds:
			<span class="e2l-label"><a class="e2l-capsule" href="${EMEN2WEBROOT}/em/equipment/new/${rd.name}/">${rd.desc_short}</a></span>
		% endfor
		<span class="e2l-label">
			${buttons.image('edit.png')} New
		</span>
	% endif
 </h1>

% if not equipment:
	<p>There is no equipment defined.</p>
% else:
	<table class="e2l-shaded" cellpadding="0" cellspacing="0">
		<thead>
			<tr>
				<th>Type</th>
				<th>Name</th>
				<th>Calibration</th>
				<th>Maintenance</th>
				<th>Activity</th>
			</tr>
		</thead>
		<tbody>
			% for e in equipment:
				<tr>
					<td>${e.name}</td>
					<td> -- </td>
					<td> -- </td>
					<td> -- </td>
					<td> -- </td>
				</tr>
			% endfor
		</tbody>
	</table>
% endif

<br /><br />

<h1>
	Projects
	% for rd in project_rds:
		<span class="e2l-label"><a class="e2l-capsule" href="${EMEN2WEBROOT}/em/project/new/${rd.name}/">${rd.desc_short}</a></span>
	% endfor
	<span class="e2l-label">
		${buttons.image('edit.png')} New
	</span>
</h1>

<div class="e2-map e2-map-projects">${projects_map}</div>

