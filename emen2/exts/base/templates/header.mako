<%namespace name="buttons" file="/buttons"  />

<ul id="nav" class="e2l-menu e2l-cf">

	<li>
		<a style="padding:0px;padding-left:8px;" href="${EMEN2WEBROOT}/"><img src="${EMEN2WEBROOT}/static/images/${EMEN2LOGO}" alt="${EMEN2DBNAME}" /></a>
	</li>
	
	% if USER:

		<li><a href="${EMEN2WEBROOT}/">Home ${buttons.caret()}</a>
			<ul>
				<li><a href="${EMEN2WEBROOT}/sitemap/">Sitemap</a></li>
				##<li><a href="${ctxt.reverse('Record/children', BOOKMARKS.get('PROJECTS',1), 'project')}">Projects</a></li>
				##<li><a href="${EMEN2WEBROOT}/record/${BOOKMARKS.get('EQUIPMENT',1)}/children/folder/">Equipment</a></li>
				<li class="e2l-menu-divider"><a href="${EMEN2WEBROOT}/paramdefs/">Params</a></li>
				<li><a href="${EMEN2WEBROOT}/recorddefs/">Protocols</a></li>
				<li class="e2l-menu-divider"><a href="${EMEN2WEBROOT}/users/">Users</a></li>
				<li><a href="${EMEN2WEBROOT}/groups/">Groups</a></li>
				<li class="e2l-menu-divider"><a href="${EMEN2WEBROOT}/help/">Help</a></li>				
			</ul>
		</li>

		<li>
			<a href="${EMEN2WEBROOT}/query/">Query ${buttons.caret()}</a>
			<ul>
				<li><a href="${EMEN2WEBROOT}/query">All Records</a></li>
				<li><a href="${EMEN2WEBROOT}/query/rectype.is.grid_imaging/">Imaging Sessions</a></li>
				<li><a href="${EMEN2WEBROOT}/query/rectype.is.image_capture*/">Images</a></li>
				<li><a href="${EMEN2WEBROOT}/query/rectype.is.labnotebook/">Lab Notebooks</a></li>
				<li><a href="${EMEN2WEBROOT}/query/rectype.is.publication*/">Publications</a></li>
			</ul>
		</li>
	
		<li id="bookmarks" data-parent="${USER.record}"><a href="">Bookmarks ${buttons.caret()}</a>
			<ul id="bookmarks">
				<li><a href="">${buttons.spinner()}</a></li>
			</ul>
		</li>
	
	% endif

	% if ADMIN:
		<li><a href="${EMEN2WEBROOT}/">Admin ${buttons.caret()}</a>
			<ul>
				<li><a href="">Account Requests</a></li>
				<li><a href="">User Administration</a></li>
				<li><a href="">Configuration</a></li>
				<li><a href="">Backup</a></li>
			</ul>
		</li>
	% endif

	<li class="e2l-float-right nohover">
		<form method="get" action="${EMEN2WEBROOT}/query/">
			<input type="search" name="q" size="8" placeholder="Search" id="e2-header-search" />
		</form>
	</li>

	<li class="e2l-float-right">
		% if USER:
			<a href="${EMEN2WEBROOT}/user/${USER.name}/">${USER.displayname} ${buttons.caret()}</a>
			<ul>				
				<li><a href="${EMEN2WEBROOT}/user/${USER.name}/edit/">Edit Profile</a></li>
				<li><a href="${EMEN2WEBROOT}/auth/logout/">Logout</a></li>
			</ul>
		% else:
			<a href="${EMEN2WEBROOT}/auth/login/">Login</a>
		% endif
	</li>

</ul>
