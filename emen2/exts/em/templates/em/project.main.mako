<%! 
import jsonrpc.jsonutil
import emen2.util.listops
%>
<%inherit file="/pages/record" />
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


	$('.e2-button').button();
	
	## New record controls
	$('.e2-record-new').RecordControl({
	});
	$('.e2-record-edit').RecordControl({
	});	
	
</%block>

<%
recorddefs_d = emen2.util.listops.dictbykey(recorddefs, 'name')
%>

<h1>
	Project overview
	<ul class="e2l-actions">
		<li><a class="e2-button e2-record-edit" data-name="${name}" href="${EMEN2WEBROOT}/record/${name}/#edit" target="_blank">${buttons.image('edit.png')} Edit</a></li>
		<li><a class="e2-button" href="${EMEN2WEBROOT}/query/children.is.${name}*/" target="_blank">View all ${len(children)} records</a></li>
		<li><a class="e2-button" href="${EMEN2WEBROOT}/sitemap/${name}/" target="_blank">Sitemap</a></li>
		## <li><a class="e2-button" href="${EMEN2WEBROOT}/record/${name}/" target="_blank"></a></li>
	</ul>
</h1>

<div id="recent_activity">
	<div class="e2-plot"></div>
</div>



${rec_rendered}


<h1>
	Sub-projects (${len(subprojects)})
	<ul class="e2l-actions">
		<li><a href="" class="e2-button e2-record-new" data-rectype="subproject" data-parent="${name}">${buttons.image('edit.png')} New</a></li>
	</ul>
</h1>

<ul>
% for subproject in subprojects:
	<li><a href="${EMEN2WEBROOT}/em/project/${subproject}/">${recnames.get(subproject, subproject)}</a></li>
% endfor
</ul>




<h1>In this project...</h1>

<table class="e2l-shaded" cellpadding="0" cellspacing="0">
	
	% for rectype,items in children_grouped.items():
		<tbody>

			<tr class="e2l-shaded-header">
				<td colspan="2">
					${recorddefs_d.get(rectype, dict()).get('desc_short')} (${len(items)})

					<ul class="e2l-actions">
						<li><span class="e2-button e2-record-new" data-rectype="${rectype}" data-parent="${name}">${buttons.image('edit.png')} New</span></li>
						<li><a class="e2-button" href="${EMEN2WEBROOT}/query/children.is.${name}*/rectype.is.${rectype}/">View all</a></li>
					</ul>

				</td>
			</tr>

			% for item in items & recent:
				<tr class="e2l-shaded-indent">
					<td>
						<a href="${EMEN2WEBROOT}/record/${item}/">${recnames.get(item, item)}</a>
					</td>
					<td>
						<a href="${EMEN2WEBROOT}/record/${item}/">${rendered_thumb.get(item,'')}</a>
					</td>
				</tr>
			% endfor
			
			% if len(items) > 10:
				<tr class="e2l-shaded-indent">
					<td colspan="2">
						<a href="${EMEN2WEBROOT}/query/children.is.${name}*/rectype.is.${rectype}/">... more</a>
					</td>
				</tr>
			% endif

		</tbody>
	% endfor

</table>
