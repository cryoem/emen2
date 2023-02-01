<%! import operator %>
<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 
<%namespace name="pages_user_util" file="/pages/user"  /> 

<h1>
    ${USER.displayname}
    <span class="e2l-label"><a href="${ROOT}/user/${USER.name}/edit/"><img src="${ROOT}/static/images/edit.png" alt="Edit" /> Edit Profile</a></span>
</h1>

<div class="e2l-cf">
    <div class="e2l-float-left">
        ${pages_user_util.page_userrec(USER, False)}
    </div>    
    <div class="e2l-float-right">
        ${pages_user_util.page_photo(USER, False)}
    </div>
</div>

% if banner:
    <h1>
        Welcome to ${TITLE}
        % if banner.writable():
            <span class="e2l-label">
                <a href="${ROOT}/record/${banner.name}/edit/"><img src="${ROOT}/static/images/edit.png" alt="Edit" /> Edit</a>
            </span>
        % endif
    </h1>

    <div>
    ${render_banner}
    </div>
% endif
