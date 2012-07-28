<%inherit file="/page" />

<%block name="js_ready">
    ${parent.js_ready()}
    $('#sitemap').TreeControl({
        'attach':true,
        'keytype':'paramdef'
    });
</%block>


<form method="post" action="${EMEN2WEBROOT}/paramdefs/name/">
<h1>
    ${title}
    <ul class="e2l-actions">
        <li>
            <input value="${q or ''}" name="q" type="text" size="8" />
            <input type="submit" value="Search" />
        </li>
        % if create:
            <li><a class="e2-button" href="${EMEN2WEBROOT}/paramdef/root/new/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> New</a></li>
        % endif
    </ul>

    <span class="e2l-label">
    </span>
</h1>
</form>


${childmap}
