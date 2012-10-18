<%inherit file="/page" />
<%namespace name="user_util" file="/pages/user"  /> 

<h1>
    ${user.displayname}
    <ul class="e2l-actions">
        % if ADMIN:
            <li><a class="e2-button" href="${ROOT}/user/${user.name}/edit/"><img src="${ROOT}/static/images/edit.png" alt="Edit" /> Edit Profile</a></li>
        % endif
    </li>
</h1>


<div class="e2l-cf">

    ${user_util.profile(user=user, userrec=user.userrec, edit=False)}

</div>


