<%namespace name="buttons" file="/buttons"  />

<%
import emen2.db.config
logo = emen2.db.config.get('customization.logo')
bookmarks = emen2.db.config.get('bookmarks.bookmarks')
%>

<div id="navigation" role="navigation">
    <ul class="e2l-menu e2l-cf">

        <li>
            <a style="padding:0px;padding-left:8px;" href="${ctxt.root}/"><img id="logo" src="${ctxt.root}/static/images/${logo}" alt="${TITLE}" /></a>
        </li>
    
        % if USER:

            <li>
                <a href="${ctxt.root}/">Home ${buttons.caret()}</a>
            </li>

            ## <li>
            ##    <a href="${ctxt.root}/query/">Query ${buttons.caret()}</a>
            ## </li>
            
            <li id="bookmarks" data-parent="${USER.record}">
                <a href="">Bookmarks ${buttons.caret()}</a>
                <ul id="bookmarks_system">
                    % for i,j in bookmarks:
                        % if i == '-':
                            <li class="e2l-menu-divider"></li>
                        % else:
                            <li><a href="${ctxt.root}${j}">${i}</a></li>
                        % endif
                    % endfor
                </ul>
            </li>
    
        % endif

        % if ADMIN:
            <li><a href="${ctxt.root}/">Admin ${buttons.caret()}</a>
                <ul>
                    <li><a href="${ctxt.root}/paramdefs/">Params</a></li>
                    <li><a href="${ctxt.root}/recorddefs/">Protocols</a></li>
                    <li class="e2l-menu-divider"><a href="${ctxt.root}/users/">Users</a></li>
                    <li><a href="${ctxt.root}/groups/">User groups</a></li>
                    <li class="e2l-menu-divider"><a href="${ctxt.reverse('Users/queue')}">Account requests</a></li>
                </ul>
            </li>
        % endif

        <li class="e2l-float-right nohover" role="search">
            <form method="get" action="${ctxt.root}/query/">
                <input type="text" name="keywords" size="8" placeholder="Search" id="e2-header-search" />
            </form>
        </li>

        % if USER:
            <li class="e2l-float-right">
                    <a href="${ctxt.root}/user/${USER.name}/">${USER.displayname} ${buttons.caret()}</a>
                    <ul>                
                        <li><a href="${ctxt.root}/user/${USER.name}/edit/">Edit profile</a></li>
                        <li><a href="${ctxt.root}/auth/logout/">Logout</a></li>
                    </ul>
            </li>
        % else:
            <li class="e2l-float-right">
                <a href="${ctxt.root}/auth/login/">Login</a>
            </li>
            <li class="e2l-float-right">
                <a href="${ctxt.root}/users/new/">Register</a>
            </li>
        % endif

    </ul>
</div>