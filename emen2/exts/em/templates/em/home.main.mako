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


<div class="home-main">

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

</div>
