<%! import jsonrpc.jsonutil  %>
<%inherit file="/record/record" />
<%namespace name="buttons" file="/buttons"  /> 

<%block name="css_inline">
	${parent.css_inline()}
	#content {
		width: auto;
		padding: 0px;
	}
	#content_inner {
		padding: 0px;
		padding-top: 10px;
		padding-left: 30px;
		padding-right: 30px;
	}
</%block>

<%block name="js_ready">
	${parent.js_ready()}

	// Record, ptest
	var rec = emen2.caches['record'][${jsonrpc.jsonutil.encode(rec.name)}];
	var ptest = ${jsonrpc.jsonutil.encode(rec.ptest())}
	
	// Bookmarks control
	// $('#e2l-editbar-record-setbookmark').BookmarksControl({'mode':'toggle'});

	// Tile browser
	$('.e2-tile').TileControl({'mode':'cached'});
		
	// Intialize the Tab controller
	var tab = $("#e2-tab-editbar");		
	tab.TabControl({});

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
			controls: page,
			summary: true,
			help: true
		});
	});
	
	// Attachments editor
	tab.TabControl('setcb', 'attachments', function(page) {
		$('#e2-attachments', page).AttachmentControl({
			name: rec.name,
			edit: ptest[2] || ptest[3],
			show: true,
			summary: true,
			help: true,
			controls: $('#e2-attachments', page)
		});
	});
	
	// New record editor
	tab.TabControl('setcb', 'new', function(page) {
		page.NewRecordChooserControl({
			parent: rec.name,
			controls: page,
			help: true,
			summary: true
		});
	});		

	// Relationship editor
	tab.TabControl('setcb', 'relationships', function(page) {
		$('#e2-relationships', page).RelationshipControl({
			name: rec.name,
			edit: ptest[2] || ptest[3],
			embed: true,
			show: true,
			summary: true,
			help: true,
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
	
	$('.e2-record-new').RecordControl({});
	
	
</%block>


## The only way I can have the nice gradient is if I
## put the tab ul and the page divs in separate containers...
<div id="e2-tab-editbar" class="e2-tab e2-tab-editbar" data-tabgroup="record" role="tab">
	<ul class="e2l-cf" role="menubar tablist" data-tabgroup="record">

		## Bookmarks
		% if USER:
			<li id="e2l-editbar-bookmark">
				<span class="e2l-a" data-parent="${USER.record}" data-name="${rec.name}">
					% if rec.name in bookmarks:
						<img src="${EMEN2WEBROOT}/static/images/star.closed.png" alt="Bookmarked" />
					% else:
						<img src="${EMEN2WEBROOT}/static/images/star.open.png" alt="Add Bookmark" />
					% endif
				</span>		
			</li>
		% endif

		## Edit Record
		% if rec.writable():
			<li data-tab="edit">
				<a href="#edit"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> Edit ${buttons.caret()}</a>
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
		for k in rec.paramkeys():
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
		historycount = len(rec.get('history',[]))
		historycount += len(filter(lambda x:x[2].startswith("LOG:"), rec.get('comments',[])))
		lastitem = 'comments'
		
		pos_prev = ''
		pos_next = ''
		%>
		
		## Table View
		<li data-tab="views">
			<a href="#views"><img src="${EMEN2WEBROOT}/static/images/table.png" alt="Param/Value Table" /></a>
		</li>

		## Tools
		<li data-tab="tools">
			<a href="#tools">Tools ${buttons.caret()}</a>
		</li>

		## Siblings
		% if len(siblings)>1 and rec.name in siblings:
			<%
				lastitem = 'siblings'
				pos = siblings.index(rec.name)
				pos_prev = None
				if pos > 0:
					pos_prev = siblings[pos-1]
				pos_next = None
				if pos+1 < len(siblings):
					pos_next = siblings[pos+1]
			%>

			<li class="e2l-float-right" style="border:none">
				% if pos_next is not None:
					<a href="${EMEN2WEBROOT}/record/${pos_next}/">&raquo;</a>
				% endif
			</li>
			
			<li data-tab="siblings" class="e2l-float-right"  style="border:none">
				<a href="#siblings">${pos+1} of ${len(siblings)}</a>
			</li>
			
			<li class="e2l-float-right" style="border:none">
				% if pos_prev is not None:
					<a href="${EMEN2WEBROOT}/record/${pos_prev}/">&laquo;</a>
				% endif
			</li>
			
			<li class="e2l-float-right"><span>&nbsp;</span></li>		
		% endif

		## Comments!
		<%
		displaynames = dict([i.name, i.displayname] for i in users)
		comments = filter(lambda x:not x[2].startswith('LOG'), rec.get('comments', []))
		%>
		<li data-tab="comments" class="e2l-float-right">
			<a href="#comments">

				## Ian: show date_occurred, modifytime, or creationtime...?
				${displaynames.get(rec.get('creator'), rec.get('creator'))}
				@
				<time class="e2-localize" datetime="${rec.get('creationtime')}">${rec.get('creationtime', '')[:10]}</time>
		
				<span id="e2l-editbar-historycount">
				% if historycount:
					<img id="e2l-editbar-comments-img" src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edits" />
					${historycount}
				% endif
				</span>
		
				<span id="e2l-editbar-commentcount">
				% if comments:
					<img id="e2l-editbar-comments-img" src="${EMEN2WEBROOT}/static/images/comment.closed.png" alt="Comments" />
					${len(comments)}
				% endif
				</span>
		
				${buttons.caret()}
			</a>
		</li>
	</ul>
</div>

<div class="e2-tab e2-tab-editbar" data-tabgroup="record" role="tabpanel">
	<div data-tab="edit"></div>
	
	<div data-tab="new"></div>
	
	<div data-tab="relationships">
		<form id="e2-relationships" method="post" action="${EMEN2WEBROOT}/record/${rec.name}/edit/relationships/"></form>
	</div>	 
	
	<div data-tab="permissions">
		<form id="e2-permissions" method="post" action="${EMEN2WEBROOT}/record/${rec.name}/edit/permissions/"></form>
	</div>
	
	<div data-tab="attachments">
		<form id="e2-attachments" method="post" enctype="multipart/form-data" action="${EMEN2WEBROOT}/record/${rec.name}/edit/attachments/"></form>
	</div>
	
	<div data-tab="comments"></div>
	
	<div data-tab="siblings" data-sibling="${sibling}" data-prev="${pos_prev}" data-next="${pos_next}"></div>
	
	<div data-tab="views">
		<%
		prettynames = {'defaultview': 'default', 'mainview': 'protocol', 'recname': 'record name', 'tabularview':'table columns', 'dicttable':'parameter-value table'}
		recdef.views['defaultview'] = recdef.views.get('defaultview') or recdef.mainview
		
		%>

		<h4>Record views</h4>
		
		<p>You are viewing the ${prettynames.get(viewname, viewname)} view for this record.</p>

		<p>This record uses the <a href="${EMEN2WEBROOT}/recorddef/${recdef.name}">${recdef.desc_short} protocol</a>, which provides ${len(recdef.views)+2} views:
			<ul>
				<li><a href="?viewname=mainview#views">Protocol</a></li>
				<li><a href="?viewname=dicttable#views">Parameter-Value table</a></li>				
				% for v in recdef.views:
					<li><a href="?viewname=${v}#views">${prettynames.get(v, v).capitalize()}</a></li>
				% endfor
			</ul>
		</p>		
	</div>
	
	<div data-tab="tools">
		<%block name="tools">

			<h4>Tools</h4>
			<ul>
				<li><a href="${EMEN2WEBROOT}/query/children.is.${rec.name}*/attachments/">Download all attachments in children</a></li>
				<li><a href="${EMEN2WEBROOT}/record/${rec.name}/publish/">Manage published data</a></li>
				<li><a href="${EMEN2WEBROOT}/record/${rec.name}/email/">Email Users</a></li>
				<li><a href="${EMEN2WEBROOT}/sitemap/${rec.name}/">Sitemap</a></li>
			</ul>

			<h4>Common Queries:</h4>
			<ul>
				<li><a href="${EMEN2WEBROOT}/query/children.is.${rec.name}*/">Child records, sorted by creation time</a></li>
				<li><a href="${EMEN2WEBROOT}/query/children.is.${rec.name}*/?sortkey=modifytime">Child records, sorted by last modification</a></li>
				<li><a href="${EMEN2WEBROOT}/query/children.is.${rec.name}*/rectype.is.image_capture*/">Child images (ccd, scan, tomogram)</a></li>
				<li><a href="${EMEN2WEBROOT}/query/children.is.${rec.name}*/rectype.is.grid_imaging/">Child grid imaging sessions</a></li>
				<li><a href="${EMEN2WEBROOT}/query/rectype.is.${rec.rectype}/">${rec.rectype} records</a></li>
				<li><a href="${EMEN2WEBROOT}/query/rectype.is.${rec.rectype}/creator.is.${rec.get('creator')}/">${rec.rectype} records, created by ${rec.get('creator')}</a></li>
			</ul>				

		</%block>
	</div>
		
</div>

## Tile viewer
% if rec.get('file_binary_image'):
	<div class="e2-tile-outer">
		<div class="e2-tile" style="height:512px;overflow:hidden" data-bdo="${rec.get('file_binary_image')}" data-mode="cached"></div>
	</div>
% endif

<div id="content_inner">
	${next.body()}
</div>

