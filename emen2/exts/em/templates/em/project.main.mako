<%! 
import jsonrpc.jsonutil
import emen2.util.listops
%>
<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

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
	
	## New record controls
	$('.e2-newrecord-test').NewRecordControl({
		redirect:'/'
	});
</%block>

<%
recorddefs_d = emen2.util.listops.dictbykey(recorddefs, 'name')
%>


<h1>
	${title}
	<ul class="e2l-actions">
		<li><button>${buttons.image('edit.png')} Edit</button></li>
		<li><button>Sitemap</button></li>
	</ul>	
</h1>


## ${rec_rendered}


<h1>
	Activity
	<ul class="e2l-actions">
		<li><button>View query</button></li>
	</ul>
</h1>
<div id="recent_activity">
	<div class="e2-plot"></div>
</div>




<h1>
	Subprojects
	<ul class="e2l-actions">
		<li><button>New subproject</button></li>
	</ul>
</h1>

<ul>
% for subproject in subprojects:
	<li>${rendered.get(subproject, subproject)}</li>
% endfor
</ul>




<h1>In this project...</h1>

<table class="e2l-shaded" cellpadding="0" cellspacing="0">
	<thead>
		<tr>
			<th>Test</th>
		</tr>
	</thead>
	
	% for rectype,items in children_grouped.items():
		<tbody>
			<tr class="e2l-shaded-header">
				<td colspan="0">${recorddefs_d.get(rectype, dict()).get('desc_short')} (${len(items)})</td>
			</tr>
			% for item in items & recent:
				<tr class="e2l-shaded-indent">
					<td>${rendered.get(item, item)}</td>
				</tr>
			% endfor
		</tbody>
	% endfor

</table>
