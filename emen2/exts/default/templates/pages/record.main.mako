<%! import jsonrpc.jsonutil  %>
<%inherit file="/pages/record" />
<%namespace name="buttons" file="/buttons"  /> 


<%block name="javascript_ready">
	${parent.javascript_ready()}

	// Record, ptest
	var rec = caches['record'][${jsonrpc.jsonutil.encode(rec.name)}];
	var ptest = ${jsonrpc.jsonutil.encode(rec.ptest())}
	
	// Permissions editor
	$('#e2l-editbar-record-permissions').EditbarControl({
		width: 700,
		cb: function(self){
			self.popup.PermissionControl({
				name: rec.name,
				edit: ptest[3],
				embed: true,
				show: true
				});
			}
	});		

	// Attachments editor
	var showattachments = (window.location.hash.search('attachments'));
	if (showattachments>-1){showattachments=true}
	$('#e2l-editbar-record-attachments').EditbarControl({
		width: 600,
		cb: function(self) {
			self.popup.AttachmentControl({
				name: rec.name,
				edit: ptest[2] || ptest[3],
				embed: true,
				show: true
				});
			},
		show: showattachments
	});
	
	// New record editor
	$('#e2l-editbar-record-newrecord').EditbarControl({
		width: 300,
		cb: function(self){
			self.popup.NewRecordControl({
				embedselector: true,
				showselector: true,
				parent: rec.name
				});
			}
	});		

	// Relationship editor
	$("#e2l-editbar-record-relationships").EditbarControl({	
		width: 600,	
		cb: function(self){
			self.popup.SimpleRelationshipControl({
				name: rec.name,
				edit: true,
				embed: true,
				show: true
				});
			}
	});	

	// Change View
	$('.e2l-editbar [data-viewtype]').click(function(){
		var target = $("#rendered");
		var viewtype = $(this).attr('data-viewtype') || 'recname';
		target.attr("data-viewtype", viewtype);
		$.rebuild_views("#rendered");
	});

	$('#e2l-editbar-tools').EditbarControl({
		width: 500
	});

	// Comments editor
	$('#e2l-editbar-comments').EditbarControl({
		width: 400,
		align: 'right',
		cb: function(self) {
			// Comments and history
			self.popup.CommentsControl({
				name: rec.name,
				edit: ptest[1] || ptest[2] || ptest[3],
				historycount: "#e2l-editbar-commentcount",
				commentcount: '#e2l-editbar-historycount'
			});
		}
	});

	// Simple handler for browsing siblings...
	var showsiblings = (window.location.hash.search('siblings'));
	if (showsiblings>-1){showsiblings=true}	
	$("#e2l-editbar-record-siblings").EditbarControl({
		width: 400,
		show: showsiblings,
		align: 'right',
		cb: function(self) {
			self.popup.SiblingsControl({
				name: rec.name
			})
		}
	});	

	// Bind editable widgets
	// $('.e2l-editable').EditControl({});
	$('#e2l-editbar-record-setbookmark').BookmarksControl({'mode':'toggle'});

	$('#e2l-editbar-record-edit .label').MultiEditControl({
		name: rec.name,
		form: '#rendered'
	});

	$('.e2-tile').TileControl({'mode':'cached'});
	
</%block>


<ul class="e2l-menu e2l-editbar e2l-float-list e2l-clearfix">

	## Bookmarks
	% if USER:
		<li id="e2l-editbar-record-setbookmark">
			<span class="e2l-a e2l-label" data-parent="${USER.record}" data-name="${rec.name}">
			% if rec.name in bookmarks:
				<img src="${EMEN2WEBROOT}/static/images/star-closed.png" alt="Bookmarked" />
			% else:
				<img src="${EMEN2WEBROOT}/static/images/star-open.png" alt="Add Bookmark" />
			% endif
			</span>		
		</li>
	% endif
	
	## Edit Record
	% if rec.writable():
		<li id="e2l-editbar-record-edit">
			<span class="e2l-a e2l-label" data-name="${rec.name}">
				<img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> Edit
			</span>
		</li>
	% endif

	## New Record
	% if create:
		<li id="e2l-editbar-record-newrecord">
			<span class="e2l-a e2l-label">
				New
				<img src="${EMEN2WEBROOT}/static/images/caret_small.png" alt="^" />
			</span>
		</li>
	% endif

	## Relationship Editor
	<li id="e2l-editbar-record-relationships">
		<span class="e2l-a e2l-label">
			Relationships
			<img src="${EMEN2WEBROOT}/static/images/caret_small.png" alt="^" />
		</span>
	</li>

	## Permissions Editor
	<li id="e2l-editbar-record-permissions">
		<span class="e2l-a e2l-label">
			Permissions
			<img src="${EMEN2WEBROOT}/static/images/caret_small.png" alt="^" />
		</span>
	</li>

	## Attachments Editor
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
	<li id="e2l-editbar-record-attachments">
		<span class="e2l-a e2l-label">
			<span id="attachment_count">
			% if attachments:
				${len(attachments)}
			% endif
			</span>
			<img id="e2l-editbar-comments-img" src="${EMEN2WEBROOT}/static/images/attachments.png" alt="Attachments" />
			<img src="${EMEN2WEBROOT}/static/images/caret_small.png" alt="^" />
		</span>
	</li>

	## View Selector
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
	lastitem = 'comments'
	%>
	<li id="e2l-editbar-tools">
		<span class="e2l-a e2l-label">
			${rec.rectype}
			<img src="${EMEN2WEBROOT}/static/images/caret_small.png" alt="^" />
		</span>
		<div class="e2l-menu-hidden">
			<p><a href="${ctxt.reverse('RecordDef',action=None,name=rec.rectype)}">${rec.rectype} protocol page</a></p>

			<h4>Views</h4>
			<ul>
			% for i in sorted(set(recdef.views.keys()+['mainview', 'dicttable'])):
				<li class="e2l-a" data-viewtype="${i}">${nicenames.get(i, i)}</li>	
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

	## Table View
	<li>
		<span class="e2l-a e2l-label" data-viewtype="dicttable"><img src="${EMEN2WEBROOT}/static/images/table.png" alt="Param/Value Table" /></span>
	</li>

	## Siblings
	% if len(siblings)>1 and rec.name in siblings:
		<%
			lastitem = 'siblings'
			pos = siblings.index(rec.name)
			pos_prev = ''
			if pos > 0:
				pos_prev = siblings[pos-1]
			pos_next = ''
			if pos+1 < len(siblings):
				pos_next = siblings[pos+1]
		%>
		<li id="e2l-editbar-record-siblings" class="e2l-float-right e2l-editbar-lastitem" data-sibling="${sibling}" data-prev="${pos_prev}" data-next="${pos_next}">
			<span class="e2l-a e2l-label">
			${pos+1} of ${len(siblings)}
			</span>
		</li>
	% endif
	
	## Comments!
	<%
	comments = filter(lambda x:not x[2].startswith('LOG'), rec.get('comments', []))
	%>
	% if lastitem == 'comments':	
		<li id="e2l-editbar-comments" class="e2l-float-right e2l-editbar-lastitem">
	% else:
		<li id="e2l-editbar-comments" class="e2l-float-right">
	%endif
	
		<span class="e2l-a e2l-label">
			% if rec.get('modifytime'):	
				${displaynames.get(rec.get('modifyuser'), '(%s)'%rec.get('modifyuser'))} @ ${rec.get('modifytime', '')[:10]}
			% else:
				${displaynames.get(rec.get('creator'), '(%s)'%rec.get('creator'))} @ ${rec.get('creationtime', '')[:10]}
			% endif
			
			<span id="e2l-editbar-historycount">
			% if historycount:
				<img id="e2l-editbar-comments-img" src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edits" />
				${historycount}
			% endif
			</span>
			
			<span id="e2l-editbar-commentcount">
			% if comments:
				<img id="e2l-editbar-comments-img" src="${EMEN2WEBROOT}/static/images/comment-open.png" alt="Comments" />
				${len(comments)}
			% endif
			</span>
			
			<img src="${EMEN2WEBROOT}/static/images/caret_small.png" alt="^" />
		</span>
		<div class="e2l-menu-hidden"></div>			
	</li>
</ul>


## Tile viewer

% if rec.get('file_binary_image'):
	<div class="e2-tile-outer">
		<div class="e2-tile" style="height:512px;overflow:hidden" data-bdo="${rec.get('file_binary_image')}" data-mode="cached"></div>
	</div>
% endif


## Main rendered record
<form id="rendered" name="rendered" method="post" action="${EMEN2WEBROOT}/record/${rec.name}/edit/" class="e2-view" data-viewtype="${viewtype}" data-name="${rec.name}" ${['', 'data-edit="true"'][rec.writable()]}>
	${rendered}
</form>

