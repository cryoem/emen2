<%inherit file="/pages/record" />
<%namespace name="buttons" file="/buttons"  /> 
<% import jsonrpc.jsonutil  %>

## Init script

<script type="text/javascript">
//<![CDATA[
	$(document).ready(function() {
		record_init(${jsonrpc.jsonutil.encode(rec)}, ${jsonrpc.jsonutil.encode(rec.ptest())}, ${jsonrpc.jsonutil.encode(edit)});
	});	
//]]>
</script>


<ul class="menu editbar floatlist clearfix">

	% if USER:
		<li id="e2-editbar-record-setbookmark">
			<span class="clickable label" data-parent="${USER.record}" data-name="${rec.name}">
			% if rec.name in bookmarks:
				<img src="${EMEN2WEBROOT}/static/images/star-closed.png" alt="Bookmarked" />
			% else:
				<img src="${EMEN2WEBROOT}/static/images/star-open.png" alt="Add Bookmark" />
			% endif
			</span>		
		</li>
	% endif
	
	% if rec.writable():
		<li id="e2-editbar-record-edit">
			<span class="clickable label" data-name="${rec.name}">
				<img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> Edit
			</span>
		</li>
	% endif

	% if create:
		<li id="e2-editbar-record-newrecord">
			<span class="clickable label">
				New
				<img src="${EMEN2WEBROOT}/static/images/caret_small.png" alt="^" />
			</span>
		</li>
	% endif

	<li id="e2-editbar-record-relationships">
		<span class="clickable label">
			Relationships
			<img src="${EMEN2WEBROOT}/static/images/caret_small.png" alt="^" />
		</span>
	</li>


	<li id="e2-editbar-record-permissions">
		<span class="clickable label">
			Permissions
			<img src="${EMEN2WEBROOT}/static/images/caret_small.png" alt="^" />
		</span>
	</li>

	<%
	attachments = []
	# cheap filtering....
	for k in rec.getparamkeys():
		v = rec[k]
		if hasattr(v, "__iter__"):
			attachments.extend(x for x in v if 'bdo:' in str(x))
		elif "bdo:" in unicode(v):
			attachments.extend([v])
	%>


	<li id="e2-editbar-record-attachments">
		<span class="clickable label">
			<span id="attachment_count">${len(attachments)}</span>
			Attachments
			<img src="${EMEN2WEBROOT}/static/images/caret_small.png" alt="^" />
		</span>
	</li>



	<%
	nicenames = {
		"tabularview": "Table View (tabularview)",
		"mainview": "Main Protocol Definition (mainview)",
		"recname": "Short description (recname)",
		"dicttable": "Key/value table (dicttable)",
		"defaultview": "Default view"
	}
	
	historycount = len(rec.get('history',[]))
	historycount += len(filter(lambda x:x[2].startswith("LOG:"), rec.get('comments',[])))
	
	%>


	<li id="e2-editbar-tools">
		<span class="clickable label">
			${rec.rectype}
			<img src="${EMEN2WEBROOT}/static/images/caret_small.png" alt="^" />
		</span>
		<div class="hidden" style="width:400px;">

			<p><a href="${ctxt.reverse('RecordDef',name=rec.rectype)}">${rec.rectype} protocol page</a></p>

			<h4>Views</h4>
			<ul>
			% for i in sorted(set(recdef.views.keys()+['mainview', 'dicttable'])):
				<li class="clickable" data-viewtype="${i}">${nicenames.get(i, i)}</li>	
			% endfor
			</ul>


			<h4>Tools</h4>
			<ul>
				<li><a href="${EMEN2WEBROOT}/record/${rec.name}/email/">Email Users</a></li>
				<li><a href="${EMEN2WEBROOT}/query/name==${rec.name}/files/">View / Download all files</a></li>
				<li><a href="${EMEN2WEBROOT}/query/children.name.${rec.name}*/files/">View / Download all files in children</a></li>
				<li><a href="${EMEN2WEBROOT}/sitemap/${rec.name}/">Child tree</a></li>
				<li><a href="${EMEN2WEBROOT}/sitemap/${rec.name}/?recurse=3">Child tree (Semi-expanded)</a></li>
				<li><a href="${EMEN2WEBROOT}/sitemap/${rec.name}/?recurse=-1">Child tree (Expanded)</a></li>
				% if rec.isowner():
					<li><a href="${EMEN2WEBROOT}/record/${rec.name}/delete/">Delete this record</a></li>
				% endif
			</ul>
		
			<h4>Common Queries:</h4>
			<ul>
				<li><a href="${EMEN2WEBROOT}/query/children.name.${rec.name}*/">Child records, sorted by creation time</a></li>
				<li><a href="${EMEN2WEBROOT}/query/children.name.${rec.name}*/?sortkey=modifytime">Child records, sorted by last modification</a></li>
				<li><a href="${EMEN2WEBROOT}/query/children.name.${rec.name}*/rectype.is.image_capture*/">Child images (ccd, scan, tomogram)</a></li>
				<li><a href="${EMEN2WEBROOT}/query/children.name.${rec.name}*/rectype.is.grid_imaging/">Child grid imaging sessions</a></li>
				<li><a href="${EMEN2WEBROOT}/query/rectype.is.${rec.rectype}/">${rec.rectype} records</a></li>
				<li><a href="${EMEN2WEBROOT}/query/rectype.is.${rec.rectype}/creator.is.${rec.get('creator')}/">${rec.rectype} records, created by ${rec.get('creator')}</a></li>
			</ul>				
		</div>
	</li>

	<li>
		<span class="clickable label" data-viewtype="dicttable"><img src="${EMEN2WEBROOT}/static/images/table.png" alt="^" /></span>
	</li>


	% if len(siblings)>1 and rec.name in siblings:

		<%
			pos = siblings.index(rec.name)
		%>
	
		<li id="e2-editbar-record-siblings" class="floatright" data-sibling="${sibling}">
				## % if pos > 0:
				##	<a class="chevron" href="${EMEN2WEBROOT}/record/${siblings[pos-1]}/?sibling=${sibling}">&lsaquo;</a> 
				## % endif

				<span class="clickable label">
					${pos+1} of ${len(siblings)}
				</span>

				## % if pos+1 < len(siblings):
				##	<a class="chevron" href="${EMEN2WEBROOT}/record/${siblings[pos+1]}/?sibling=${sibling}">&rsaquo;</a> 
				## % endif
		</li>

	% endif

	<li id="e2-editbar-helper" class="floatright">
		<span class="clickable label">
			% if rec.get('modifytime'):	
				${displaynames.get(rec.get('modifyuser'), '(%s)'%rec.get('modifyuser'))} @ ${rec.get('modifytime', '')[:10]}
			% else:
				${displaynames.get(rec.get('creator'), '(%s)'%rec.get('creator'))} @ ${rec.get('creationtime', '')[:10]}
			% endif
			
			<span id="e2-record-historycount">
			% if historycount:
			 	(${historycount} changes)
			% endif
			</span>
			
			<img src="${EMEN2WEBROOT}/static/images/caret_small.png" alt="^" />
		</span>
		<div class="hidden" style="width:800px"></div>			
	</li>
</ul>


## Tile viewer

% if rec.get('file_binary_image'):
	<div style="position:relative">
		<div class="e2-tile" style="height:512px;overflow:hidden" data-bdo="${rec.get('file_binary_image')}"></div>
	</div>

	<h1></h1>
% endif


## Main rendered record
<div id="rendered" class="e2-view" data-viewtype="${viewtype}" data-name="${rec.name}" ${['', 'data-edit="true"'][rec.writable()]}>
	${rendered}
</div>

