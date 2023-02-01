<%namespace name="buttons" file="/buttons"  />

<div id="nav" role="navigation">
    <ul class="e2l-menu e2l-cf">

        <li>
            <a style="padding:0px;padding-left:8px;" href="${ROOT}/"><img id="logo" src="${ROOT}/static/images/${LOGO}" alt="${TITLE}" /></a>
        </li>
    
        <li><a href="${ROOT}/">Home ${buttons.caret()}</a>
            <ul>
                <li><a href="${ROOT}/records/">Sitemap</a></li>
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
                <li><a href="${ROOT}/query/rectype.is.grid_imaging/">Imaging sessions</a></li>
                <li><a href="${ROOT}/query/rectype.is.image_capture*/">Images</a></li>
                <li><a href="${ROOT}/query/rectype.is.labnotebook/">Lab notebooks</a></li>
                <li><a href="${ROOT}/query/rectype.is.publication*/">Publications</a></li>
            </ul>
        </li>
            
    </ul>
</div>