<%namespace name="buttons" file="/buttons"  />

<div id="nav" role="nav">
	<ul class="e2l-menu e2l-cf">

		<li>
			<a style="padding:0px;padding-left:8px;" href="${EMEN2WEBROOT}/"><img id="logo" src="${EMEN2WEBROOT}/static/images/${EMEN2LOGO}" alt="${EMEN2DBNAME}" /></a>
		</li>
	
		% if USER:

			<li><a href="${EMEN2WEBROOT}/">Home ${buttons.caret()}</a>
				<ul>
					<li><a href="${EMEN2WEBROOT}/sitemap/">Sitemap</a></li>
					<li class="e2l-menu-divider"><a href="${EMEN2WEBROOT}/paramdefs/">Params</a></li>
					<li><a href="${EMEN2WEBROOT}/recorddefs/">Protocols</a></li>
					<li class="e2l-menu-divider"><a href="${EMEN2WEBROOT}/users/">Users</a></li>
					<li><a href="${EMEN2WEBROOT}/groups/">User groups</a></li>
					<li class="e2l-menu-divider"><a href="${EMEN2WEBROOT}/help/">Help</a></li>				
				</ul>
			</li>

			<li>
				<a href="${EMEN2WEBROOT}/query/">Query ${buttons.caret()}</a>
				<ul>
					<li><a href="${EMEN2WEBROOT}/query">All records</a></li>
					<li class="e2l-menu-divider"</li>
					<li><a href="${EMEN2WEBROOT}/query/rectype.is.project/">Projects</a></li>
					<li><a href="${EMEN2WEBROOT}/query/rectype.is.grid_imaging/">Imaging sessions</a></li>
					<li><a href="${EMEN2WEBROOT}/query/rectype.is.image_capture*/">Images</a></li>
					<li><a href="${EMEN2WEBROOT}/query/rectype.is.labnotebook/">Lab notebooks</a></li>
					<li><a href="${EMEN2WEBROOT}/query/rectype.is.publication*/">Publications</a></li>
				</ul>
			</li>
			
			<li id="bookmarks" data-parent="${USER.record}">
				<a href="">Bookmarks ${buttons.caret()}</a>
				<ul id="bookmarks_system">
					% for i,j in BOOKMARKS:
						<li><a href="${j}">${i}</a></li>
					% endfor
					## <li class="e2l-menu-divider"></li>
					## <li><a href="">${buttons.image('spinner.gif')} Loading personal bookmarks</a></li>
				</ul>
			</li>
	
		% endif

		% if ADMIN:
			<li><a href="${EMEN2WEBROOT}/">Admin ${buttons.caret()}</a>
				<ul>
					<li><a href="${ctxt.reverse('Users/queue')}">Account requests</a></li>
					## <li><a href="${ctxt.reverse('Users/admin')}">User administration</a></li>
					## <li><a href="">Configuration</a></li>
					## <li><a href="">Backup</a></li>
				</ul>
			</li>
		% endif

		## <li class="e2l-float-right nohover" role="search">
		##	<form method="get" action="${EMEN2WEBROOT}/query/">
		##		## type="search"
		##		<input type="text" name="keywords" size="8" placeholder="Search" id="e2-header-search" />
		##	</form>
		## </li>

		% if USER:
			<li class="e2l-float-right">
					<a href="${EMEN2WEBROOT}/user/${USER.name}/">${USER.displayname} ${buttons.caret()}</a>
					<ul>				
						<li><a href="${EMEN2WEBROOT}/user/${USER.name}/edit/">Edit profile</a></li>
						<li><a href="${EMEN2WEBROOT}/auth/logout/">Logout</a></li>
					</ul>
			</li>
		% else:
			<li class="e2l-float-right">
				<a href="${EMEN2WEBROOT}/auth/login/">Login</a>
			</li>
			<li class="e2l-float-right">
				<a href="${EMEN2WEBROOT}/users/new/">Register</a>
			</li>
		% endif

	</ul>
</div>