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



<%block name="css_inline">
	${parent.css_inline()}

	.home-sidebar {
		position: absolute;
		left: 20px;
		width: 300px;
		height: 100%;
		padding-bottom:50px;
	}

	.home-main {
		border-left:solid 1px #ccc;
		margin-left:290px;
		padding-left:20px;
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

	$('.e2-record-new').RecordControl({
		redirect:window.location.pathname
	});

	$('.e2-record-edit').RecordControl({
		redirect:window.location.pathname
	});
		
	$('#activity time').timeago();	
</%block>



<div class="home-sidebar">

	<div class="e2-infobox" style="width:100%">
		% if USER.userrec.get('person_photo'):
			<img class="e2l-thumbnail" src="${EMEN2WEBROOT}/download/${USER.userrec.get('person_photo')}/user.jpg?size=small" />
		% endif	
		<div>
			<h4>${USER.displayname}</h4>
			<div class="e2l-small">
				${USER.email}
				<span style="float:right;padding-right:5px;">
					<a href="">Profile</a>
				</span>
			</div>
		</div>
	</div>
	
	## <h2 class="e2l-cf">
	##	<a href="">Groups</a>
	##	<a href="${EMEN2WEBROOT}/record/0/new/project/" class="e2-record-new" data-parent="0" data-rectype="group">New group</a>
	## </h2>
	## <ul class="home-projectlist">
	## 	<li><a href="${EMEN2WEBROOT}/record/${group}/">${recnames.get(group)}</a></li>
	##			 ${len(projects)} projects
	## </ul>

	% for group, projects in groups_children.items():
		<h2 class="e2l-cf">
			<a href="${EMEN2WEBROOT}/record/${group}/">${recnames.get(group, group)}</a>
			<a href="${EMEN2WEBROOT}/record/${group}/new/project/" class="e2-record-new" data-parent="${group}" data-rectype="project">New project</a>
		 </h2>
		<ul class="home-projectlist">
			% for project in sorted(projects, key=lambda x:recnames.get(x, '').lower()):
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
	% endfor

	

	
</div>

<div class="home-main">
	${next.body()}
</div>