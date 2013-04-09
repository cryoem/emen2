<%inherit file="/page" />

<%block name="js_ready">
    ${parent.js_ready()}
    $('#sitemap').TreeControl({
        'attach':true,
        'keytype':'paramdef'
    });
</%block>


<form method="post" action="${ctxt.root}/paramdefs/name/">
<h1>
    ${ctxt.title}
    <ul class="e2l-actions">
        <li>
            <input value="${q or ''}" name="q" type="text" size="8" />
            <input type="submit" value="Search" />
        </li>
        % if create:
            <li><a class="e2-button" href="${ctxt.root}/paramdef/root/new/"><img src="${ctxt.root}/static/images/edit.png" alt="Edit" /> New</a></li>
        % endif
    </ul>

    <span class="e2l-label">
    </span>
</h1>
</form>


${unicode(childmap) | n}
