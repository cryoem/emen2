<%! 
import jsonrpc.jsonutil
import operator 
import collections
%>

<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

<%block name="css_inline">
	${parent.css_inline()}

	.home-profile {
		float: left;
		width: 350px;
		border-right:solid 1px #ccc;
		padding-bottom:50px;
	}
	.home-profile h2 {
		position:relative;
		font-size:12pt;
		margin:0px;
		padding:5px;
		border-bottom:solid 1px #ccc;
	}
	.home-profile h2 a {
		display:block;
	}
	.home-profile h2 a.e2-record-new {
		position:absolute;
		right:8px;
		top:6px;
		font-size:10pt;
		font-weight:normal;
	}
	
	.home-profile ul {
		padding-left:0px;
		margin-bottom:40px;
	}
	.home-profile li {
		list-style:none;
		position:relative;
	}
	.home-profile .home-projectlist li a {
		font-size:10pt;
		display:block;
		padding:5px;
		padding-right:50px;
	}
	.home-profile .home-projectlist li:nth-child(2n) {
		background:#eee;
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
	.home-main {
		margin-left:380px;
	}

	
</%block>


<%block name="js_ready">
	${parent.js_ready()}

	$('.e2-record-new').RecordControl({
		redirect:'/'
	});
	
	$('#activity time').timeago();	
</%block>


<div class="home-profile">

	<h1 style="text-align:center;border-bottom:none">
		% if USER.userrec.get('person_photo'):
			<img src="${EMEN2WEBROOT}/download/${USER.userrec.get('person_photo')}/user.jpg?size=small" class="e2l-thumbnail-mainprofile" alt="profile photo" />
			<br />
		% endif	
		${USER.displayname}
		<br />
		<a href="${EMEN2WEBROOT}/user/${USER.name}/edit/" class="e2-button">${buttons.image('edit.png','')} Edit profile</a> <a href="${EMEN2WEBROOT}/auth/logout/" class="e2-button">Logout</a>				
		<br />
		<a href="${EMEN2WEBROOT}/query/rectype.is.group/" class="e2-button">All groups</a> <a href="${EMEN2WEBROOT}/query/rectype.is.project/" class="e2-button">All projects</a>				
	</h1>
	
	<br />
	
	
	% for group, projects in groups_children.items():

		<h2 class="e2l-cf">
			<a href="${EMEN2WEBROOT}/em/home/group/${group}/">${recnames.get(group, group)}</a>
			
			
			## % if ADMIN:
			<a href="${EMEN2WEBROOT}/record/${group}/new/project/" class="e2-record-new" data-parent="${group}" data-rectype="project">New project</a>
			## % endif
			
		</h2>


		<ul class="home-projectlist">
			% for project in sorted(projects, key=lambda x:recnames.get(x, '').lower()):
				<li>
					<a href="${EMEN2WEBROOT}/em/home/project/${project}/">
						${recnames.get(project, project)}
					</a>
					<span class="e2l-shadow home-count">
						${len(projects_children.get(project, []))}						
					</span>
					</li>
			% endfor
		</ul>
	% endfor
	
	% if ADMIN:
		<span class="e2-button e2-button e2-record-new" data-parent="0" data-rectype="group">${buttons.image('edit.png','')} New group</span>
	% endif
	
</div>




${next.body()}