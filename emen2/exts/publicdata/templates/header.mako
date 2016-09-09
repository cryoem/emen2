<%namespace name="buttons" file="/buttons"  />

<div id="nav" role="navigation">
    <ul class="e2l-menu e2l-cf">

        <li>
            <a style="padding:0px;padding-left:8px;" href="${ctxt.root}/"><img id="logo" src="${ctxt.root}/static/images/${LOGO}" alt="${TITLE}" /></a>
        </li>
    
        <li><a href="${ctxt.root}/">Home ${buttons.caret()}</a>
            <ul>
                <li><a href="${ctxt.root}/records/">Sitemap</a></li>
                <li class="e2l-menu-divider"><a href="${ctxt.root}/paramdefs/">Params</a></li>
                <li><a href="${ctxt.root}/recorddefs/">Protocols</a></li>
                <li class="e2l-menu-divider"><a href="${ctxt.root}/users/">Users</a></li>
                <li><a href="${ctxt.root}/groups/">User groups</a></li>
                <li class="e2l-menu-divider"><a href="${ctxt.root}/help/">Help</a></li>                
            </ul>
        </li>

        <li>
            <a href="${ctxt.root}/query/">Query ${buttons.caret()}</a>
            <ul>
                <li><a href="${ctxt.root}/query">All records</a></li>
                <li><a href="${ctxt.root}/query/rectype.is.grid_imaging/">Imaging sessions</a></li>
                <li><a href="${ctxt.root}/query/rectype.is.image_capture*/">Images</a></li>
                <li><a href="${ctxt.root}/query/rectype.is.labnotebook/">Lab notebooks</a></li>
                <li><a href="${ctxt.root}/query/rectype.is.publication*/">Publications</a></li>
            </ul>
        </li>
            
    </ul>
</div>