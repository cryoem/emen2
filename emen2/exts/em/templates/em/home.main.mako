<%! 
import jsonrpc.jsonutil
%>

<%inherit file="/em/home" />
<%namespace name="buttons" file="/buttons"  /> 


<%block name="js_ready">
	${parent.js_ready()}

	## Recent activity viewer
	var q = ${jsonrpc.jsonutil.encode(recent_activity)}; 
	$('#recent_activity').PlotHistogram({
		q:q,
		pan: false,
		height:200,
	});
</%block>


% if banner:
	<h1>
		Welcome to ${EMEN2DBNAME}
		% if banner.writable():
			<ul class="e2l-actions">
				<li><a class="e2-button e2-record-edit" data-name="${banner.name}" href="${EMEN2WEBROOT}/record/${banner.name}#edit">${buttons.image('edit.png')} Edit banner</a>
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
		<li><a class="e2-button" href="${EMEN2WEBROOT}/records/">Record tree</a></li>
		<li><a class="e2-button" href="${EMEN2WEBROOT}/query/">All records</a></li>
	</ul>
</h1>

<div id="recent_activity">
	<div class="e2-plot"></div>
</div>

${recent_activity_table}



<br /><br />

% for group in groups:
	<h1>
		<a name="groups-${group.name}"></a>
		${recnames.get(group.name, group.name)}
		<ul class="e2l-actions">
			<li><a class="e2-button e2-record-new" href="${EMEN2WEBROOT}/record/${group.name}/new/project/" class="e2-record-new" data-parent="${group.name}" data-rectype="project">${buttons.image('new.png')} New project</a>
			<li><a class="e2-button" href="${EMEN2WEBROOT}/record/${group.name}/children/project/">View projects in table</a></li>
		</ul>
	</h1>
	
	<ul class="home-projectlist">
		% for project in sorted(groups_children.get(group.name, []), key=lambda x:recnames.get(x, '').lower()):
			<li>
				<a href="${EMEN2WEBROOT}/record/${project}/">
					${recnames.get(project, project)}
				</a>
				<span class="e2l-shadow home-count">
					${len(projects_children.get(project, [])) or ''}						
				</span>
				</li>
		% endfor
	</ul>
	
	<br /><br /><br /><br />
% endfor