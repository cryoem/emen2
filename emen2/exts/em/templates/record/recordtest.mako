<%! 
import jsonrpc.jsonutil
import operator 
import collections
%>

<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 


<%

# Database queries.
torender = set()
def nodeleted(items):
	return filter(lambda x:not x.get('deleted'), items)

# Groups
groups = nodeleted(DB.record.get(DB.record.findbyrectype('group')))
groups = set([i.name for i in groups])
torender |= groups

# Top-level children of groups (any rectype)
groups_children = DB.rel.children(groups)
projs = set()
for v in groups_children.values():
	projs |= v
torender |= projs

# Get projects, most recent children, and progress reports
# projects_children = DB.rel.children(projs, recurse=-1)
projects_children = {}

# Get all the recent records we want to display
recnames = DB.record.render(torender)

%>

<%
print rec
%>

## Relationship tree
<%block name="precontent">
	${parent.precontent()}
	<div class="e2-tree-main" style="overflow:hidden">${parentmap}</div>
</%block>



<%block name="css_inline">
	${parent.css_inline()}

	.home-sidebar {
		position: absolute;
		left: 20px;
		width: 250px;
		height: 100%;
		padding-bottom:50px;
	}

	.home-main {
		border-left:solid 1px #ccc;
		margin-left:240px;
		padding-left:0px;
	}

	.home-tools li {
	}

	.home-sidebar h2 {
		position:relative;
		font-size:12pt;
		margin:0px;
		padding:5px;
		padding-left: 0px;
		padding-right: 5px;
		border-bottom:solid 1px #ccc;
	}
	.home-sidebar h2 a {
		display:block;
	}
	.home-label, 
	.home-sidebar h2 a.e2-record-new {
		position:absolute;
		right:5px;
		top:6px;
		font-size:10pt;
		font-weight:normal;
	}
	
	.home-sidebar ul {
		padding-left:0px;
		margin-bottom:40px;
	}
	.home-sidebar li {
		list-style:none;
		position:relative;
	}
	.home-sidebar .home-projectlist li a {
		font-size:10pt;
		display:block;
		padding:5px;
		padding-right:50px;
	}
	.home-sidebar .home-projectlist li:nth-child(2n) {
		background:#eee;
	}
	
	.home-profile img {
		max-height: 64px;
		max-width: 64px;
	}
	
	.home-count {
		position:absolute;
		right:8px;
		top:6px;
		background:#f0f0f0;
		padding:2px;
		font-size:8pt;
		border-radius: 4px;
	}

	
</%block>



<%block name="js_ready">
	${parent.js_ready()}

	${buttons.tocache(rec)}

	emen2.caches['recnames'] = ${jsonrpc.jsonutil.encode(recnames)};

	$('.e2-tree').TreeControl({'attach':true});

	// Record, ptest
	var rec = emen2.caches['record'][${jsonrpc.jsonutil.encode(rec.name)}];
	var ptest = ${jsonrpc.jsonutil.encode(rec.ptest())}

	// Tile browser
	$('.e2-tile').TileControl({'mode':'cached'});
		
	// Intialize the Tab controller
	var tab = $("#e2-tab-editbar2");		
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
			historycount: "#e2l-editbar2-commentcount",
			commentcount: '#e2l-editbar2-historycount'
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


















<div class="home-sidebar">

	<%
	c = DB.record.get(rec.get('children', []))
	byrd = collections.defaultdict(set)
	for i in c:
		byrd[i.rectype].add(i)
	rds = DB.recorddef.get(byrd.keys())
	rds_d = dict(((i.name, i) for i in rds))

	parentnames = DB.record.render(rec.get('parents', []))
	recnames.update(parentnames)

	%>
	
	
	
	
	<h2>${recnames.get(rec.name, rec.name)}</h2>

	<div id="e2-tab-editbar2" data-tabgroup="record" role="tab">

		<ul class="e2l-cf home-projectlist" role="menubar tablist" data-tabgroup="record">


			## Edit Record
			% if rec.writable():
				<li data-tab="edit"><a href="#edit"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> Edit</a></li>
			% endif


			## New Record
			% if create:
				<li data-tab="new"><a href="#new">New</a></li>
			% endif


			## Relationship Editor
			<li data-tab="relationships"><a href="#relationships">Relationships</a></li>


			## Permissions Editor
			<li data-tab="permissions"><a href="#permissions">Permissions</a></li>


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
					<img id="e2l-editbar2-comments-img" src="${EMEN2WEBROOT}/static/images/attachments.png" alt="Attachments" /> Attachments
				</a>
			</li>


			## View Selector
			<li data-tab="views"><a href="#views"><img src="${EMEN2WEBROOT}/static/images/table.png" alt="Param/Value Table" /> Views</a></li>


			## Tools
			<li data-tab="tools"><a href="#tools">Tools</a></li>


			## Comments!
			<%
			displaynames = dict([i.name, i.displayname] for i in users)
			comments = filter(lambda x:not x[2].startswith('LOG'), rec.get('comments', []))
			historycount = len(rec.get('history',[]))
			historycount += len(filter(lambda x:x[2].startswith("LOG:"), rec.get('comments',[])))
			%>
			<li data-tab="comments">
				<a href="#comments">
					## ${displaynames.get(rec.get('creator'), rec.get('creator'))}
					Last change
					@
					<time class="e2-localize" datetime="${rec.get('creationtime')[:10]}">${rec.get('creationtime', '')[:10]}</time>
		
					<span id="e2l-editbar2-historycount">
					% if historycount:
						<img id="e2l-editbar2-comments-img" src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edits" />
						${historycount}
					% endif
					</span>
		
					<span id="e2l-editbar2-commentcount">
					% if comments:
						<img id="e2l-editbar2-comments-img" src="${EMEN2WEBROOT}/static/images/comment.closed.png" alt="Comments" />
						${len(comments)}
					% endif
					</span>
				</a>
			</li>
		</ul>
	</div>

	<h2 class="e2l-cf">
		Parents
		<span class="home-label">
			Map | Table
		</span>
	</h2>
	<ul class="home-projectlist">
		% for i in rec.get('parents', []):
			<li><a href="${EMEN2WEBROOT}/record/${i}/">${recnames.get(i,i)}</a></li>
		% endfor
	</ul>
	
	
	<h2 class="e2l-cf">
		Children
		<span class="home-label" style="float:right">
			Map | Table
		</span>
	</h2>
	<ul class="home-projectlist">
		% for k,v in byrd.items():
			<li>
				<a href="${EMEN2WEBROOT}/record/${rec.name}/children/${k}/">${rds_d.get(k).desc_short}</a>
				<span class="e2l-shadow home-count">${len(v)}</span>
			</li>
		% endfor
	</ul>
</div>



<div class="e2-tab e2-tab-editbar2 home-main" data-tabgroup="record" role="tabpanel">

	<div data-tab="main" class="e2-tab-active">
		${next.body()}
	</div>
	
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
				<li><a href="${EMEN2WEBROOT}/records/?root=${rec.name}">Record tree starting at this record</a></li>
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




