<%! import jsonrpc.jsonutil  %>
<%inherit file="/pages/record" />
<%namespace name="buttons" file="/buttons"  /> 

<%block name="css_inline">
	${parent.css_inline()}
	#content {
		width: auto;
		padding: 0px;
	}
	#content_inner
	{
		padding: 10px;
	}
</%block>

<%block name="js_ready">
	${parent.js_ready()}

	// Record, ptest
	var rec = emen2.caches['record'][${jsonrpc.jsonutil.encode(rec.name)}];
	var ptest = ${jsonrpc.jsonutil.encode(rec.ptest())}
	
	// Change View
	$('span[data-viewname]').click(function(){
		var target = $("#content_inner");
		var viewname = $(this).attr('data-viewname') || 'recname';
		target.attr("data-viewname", viewname);
		$.rebuild_views("#content_inner");
	});

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
		%>

		## Table View
		<li>
			<span data-viewname="dicttable"><img src="${EMEN2WEBROOT}/static/images/table.png" alt="Param/Value Table" /></span>
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
		displaynames = dict([i.name, i.displayname] for i in users)
		comments = filter(lambda x:not x[2].startswith('LOG'), rec.get('comments', []))
		%>
		<li data-tab="comments" class="e2l-float-right">
			<a href="#comments">

				## Ian: show date_occurred, modifytime, or creationtime...?
				${displaynames.get(rec.get('creator'), rec.get('creator'))}
				@
				<time datetime="${rec.get('creationtime')}">${rec.get('creationtime', '')[:10]}</time>
		
				<span id="e2l-editbar-historycount">
				% if historycount:
					<img id="e2l-editbar-comments-img" src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edits" />
					${historycount}
				% endif
				</span>
		
				<span id="e2l-editbar-commentcount">
				% if comments:
					<img id="e2l-editbar-comments-img" src="${EMEN2WEBROOT}/static/images/comment.png" alt="Comments" />
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
	
	<div data-tab="siblings"></div>
		
</div>

## Main rendered record
<form enctype="multipart/form-data" id="e2-edit" method="post" data-name="${rec.name}" action="${EMEN2WEBROOT}/record/${rec.name}/edit/">
	<div id="content_inner" class="e2-view" data-viewname="${viewname}" data-name="${rec.name}" ${['', 'data-edit="true"'][rec.writable()]}>
		${rendered}
	</div>
</form>


## Subview
<div id="content_subview">
${subview}
</div>

