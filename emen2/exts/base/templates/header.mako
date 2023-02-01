<%namespace name="buttons" file="/buttons"  />

<div id="navigation" role="navigation">
    <ul class="e2l-menu e2l-cf">

        <li>
            <a style="padding:0px;padding-left:8px;" href="${ROOT}/"><img id="logo" src="${ROOT}/static/images/${LOGO}" alt="${TITLE}" /></a>
        </li>
    
        % if USER:

            <li><a href="${ROOT}/">Home ${buttons.caret()}</a>
                <ul>
                    <li><a href="${ROOT}/records/">Records</a></li>
                    <li class="e2l-menu-divider"><a href="${ROOT}/paramdefs/">Params</a></li>
                    <li><a href="${ROOT}/recorddefs/">Protocols</a></li>
                    <li class="e2l-menu-divider"><a href="${ROOT}/users/">Users</a></li>
                    <li><a href="${ROOT}/groups/">User groups</a></li>
                    <li class="e2l-menu-divider"><a href="${ROOT}/help/">Help</a></li>                
                </ul>
            </li>

            <li>
                <a href="${ROOT}/query/">Query ${buttons.caret()}</a>
                <ul>
                    <li><a href="${ROOT}/query">All records</a></li>
                    <li class="e2l-menu-divider"></li>
                    <li><a href="${ROOT}/query/rectype.is.project/">Projects</a></li>
                    <li><a href="${ROOT}/query/rectype.is.grid_imaging/">Imaging sessions</a></li>
                    <li><a href="${ROOT}/query/rectype.is.image_capture*/">Images</a></li>
                    <li><a href="${ROOT}/query/rectype.is.labnotebook/">Lab notebooks</a></li>
                    <li><a href="${ROOT}/query/rectype.is.publication*/">Publications</a></li>
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
            <li><a href="${ROOT}/">Admin ${buttons.caret()}</a>
                <ul>
                    <li><a href="${ctxt.reverse('Users/queue')}">Account requests</a></li>
                    ## <li><a href="${ctxt.reverse('Users/admin')}">User administration</a></li>
                    ## <li><a href="">Configuration</a></li>
                    ## <li><a href="">Backup</a></li>
                </ul>
            </li>
        % endif

        ## <li class="e2l-float-right nohover" role="search">
        ##    <form method="get" action="${ROOT}/query/">
        ##        ## type="search"
        ##        <input type="text" name="keywords" size="8" placeholder="Search" id="e2-header-search" />
        ##    </form>
        ## </li>

        % if USER:
            <li class="e2l-float-right">
                    <a href="${ROOT}/user/${USER.name}/">${USER.displayname} ${buttons.caret()}</a>
                    <ul>                
                        <li><a href="${ROOT}/user/${USER.name}/edit/">Edit profile</a></li>
                        <li><a href="${ROOT}/auth/logout/">Logout</a></li>
                    </ul>
            </li>
        % else:
            <li class="e2l-float-right">
                <a href="${ROOT}/auth/login/">Login</a>
            </li>
            <li class="e2l-float-right">
                <a href="${ROOT}/users/new/">Register</a>
            </li>
        % endif

    </ul>
</div>