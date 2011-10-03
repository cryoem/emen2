<%! import jsonrpc.jsonutil  %>
<%inherit file="/pages/record" />
<%namespace name="buttons" file="/buttons"  /> 


<%block name="js_ready">
	${parent.js_ready()}

	// Record, ptest
	var rec = caches['record'][${jsonrpc.jsonutil.encode(rec.name)}];
	var ptest = ${jsonrpc.jsonutil.encode(rec.ptest())}
	
	// Change View
	$('#e2-editbar-record [data-viewtype]').click(function(){
		var target = $("#rendered");
		var viewtype = $(this).attr('data-viewtype') || 'recname';
		target.attr("data-viewtype", viewtype);
		$.rebuild_views("#rendered");
	});

	// Bookmarks control
	$('#e2l-editbar-record-setbookmark').BookmarksControl({'mode':'toggle'});

	// Tile browser
	$('.e2-tile').TileControl({'mode':'cached'});
		
	// Intialize the Tab controller
	var tab = $("#e2-editbar-record");		
	tab.TabControl({
		##absolute: true
	});

	// Editor
	tab.TabControl('setcb', 'edit', function(page) {
		$('#e2-edit').MultiEditControl({
			name: rec.name,
			controls: page
		});
		$('#e2-edit').MultiEditControl('show');
	});
	
	tab.TabControl('sethidecb', 'edit', function(page) {
		$('#e2-edit').MultiEditControl('hide');	
	});

	// Permissions editor
	tab.TabControl('setcb','permissions', function(page) {
		$('#e2-permissions', page).PermissionsControl({
			name: rec.name,
			edit: ptest[3],
			show: true,
			controls: page
		});
	});
	
	// Attachments editor
	tab.TabControl('setcb', 'attachments', function(page) {
		page.AttachmentControl({
			name: rec.name,
			edit: ptest[2] || ptest[3],
			show: true,
			controls: page
		});
	});
	
	// New record editor
	tab.TabControl('setcb', 'new', function(page) {
		page.NewRecordControl({
			parent: rec.name,
			controls: page
		});
	});		

	// Relationship editor
	tab.TabControl('setcb', 'relationships', function(page) {
		$('#e2-relationships', page).RelationshipControl({
			name: rec.name,
			edit: true,
			embed: true,
			show: true,
			summary: true,
			controls: page
		});
	});

	// Comments editor
	tab.TabControl('setcb', 'comments', function(page) {
		page.CommentsControl({
			name: rec.name,
			edit: ptest[1] || ptest[2] || ptest[3],
			controls: page,
			historycount: "#e2l-editbar-commentcount",
			commentcount: '#e2l-editbar-historycount'
		});
	});

	// Simple handler for browsing siblings...
	tab.TabControl('setcb', 'siblings', function(page) {
		page.SiblingsControl({
			name: rec.name
		})
	});	
	
	// Now that we have all the callbacks added...
	tab.TabControl('checkhash');
	
</%block>




<div class="e2-tab e2-editbar" id="e2-editbar-record" data-group="editbar">

	<ul class="e2l-cf">

		## Bookmarks
		% if USER:
			<li id="e2l-editbar-bookmark">
				<span class="e2l-a" data-parent="${USER.record}" data-name="${rec.name}">
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
			<li data-tab="edit">
				<a href="#edit"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> Edit</a>
			</li>
		% endif

		## New Record
		% if create:
			<li data-tab="new">
				<a href="#new">New ${buttons.caret()}</a>
			</li>
		% endif

		## Relationship Editor
		<li data-tab="relationships">
			<a href="#relationships">Relationships ${buttons.caret()}</a>
		</li>

		## Permissions Editor
		<li data-tab="permissions">
			<a href="#permissions">Permissions ${buttons.caret()}</a>
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
		<li data-tab="attachments">
			<a href="#attachments">
				<span id="attachment_count">
				% if attachments:
					${len(attachments)}
				% endif
				</span>
				<img id="e2l-editbar-comments-img" src="${EMEN2WEBROOT}/static/images/attachments.png" alt="Attachments" />
				${buttons.caret()}
			</a>
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
		<li data-tab="tools">
			<a href="#tools"> ${rec.rectype} ${buttons.caret()}</a>
		</li>

		## Table View
		<li>
			<span class="e2l-a" data-viewtype="dicttable"><img src="${EMEN2WEBROOT}/static/images/table.png" alt="Param/Value Table" /></span>
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
			<li data-tab="siblings" class="e2l-float-right" data-sibling="${sibling}" data-prev="${pos_prev}" data-next="${pos_next}">
				<a href="#siblings">${pos+1} of ${len(siblings)}</a>
			</li>
		% endif
	
		## Comments!
		<%
		comments = filter(lambda x:not x[2].startswith('LOG'), rec.get('comments', []))
		%>
		<li data-tab="comments" class="e2l-float-right">
			<a href="#comments">
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
			
				${buttons.caret()}
			</a>
		</li>
	</ul>
	
	
	<div data-tab="edit"></div>
	
	<div data-tab="new"></div>
	
	<div data-tab="relationships">
		<form id="e2-relationships" method="post" action="${EMEN2WEBROOT}/record/${rec.name}/edit/relationships/"></form>
	</div>	 
	
	<div data-tab="permissions">
		<form id="e2-permissions" method="post" action="${EMEN2WEBROOT}/record/${rec.name}/edit/permissions/"></form>
	</div>
	
	<div data-tab="attachments"></div>
	
	<div data-tab="comments"></div>
	
	<div data-tab="siblings"></div>
	
	<div data-tab="tools">
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
			<li><a href="${EMEN2WEBROOT}/query/name==${rec.name}/attachments/">View / Download all attachments</a></li>
			<li><a href="${EMEN2WEBROOT}/query/children.name.${rec.name}*/attachments/">View / Download all attachments in children</a></li>
			<li><a href="${EMEN2WEBROOT}/sitemap/${rec.name}/">Child tree</a></li>
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
	
	
</div>


## Tile viewer

% if rec.get('file_binary_image'):
	<div class="e2-tile-outer">
		<div class="e2-tile" style="height:512px;overflow:hidden" data-bdo="${rec.get('file_binary_image')}" data-mode="cached"></div>
	</div>
% endif


## Main rendered record
<form id="e2-edit" method="post" data-name="${rec.name}" action="${EMEN2WEBROOT}/record/${rec.name}/edit/">
	<div id="rendered" class="e2-view" data-viewtype="${viewtype}" data-name="${rec.name}" ${['', 'data-edit="true"'][rec.writable()]}>
		${rendered}
	</div>
</form>


