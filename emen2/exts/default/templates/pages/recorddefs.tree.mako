<%inherit file="/page" />

<%block name="js_ready">
    ${parent.js_ready()}
    $('#sitemap').TreeControl({
        'attach': true,
        'keytype': 'recorddef'
    });
</%block>


<form method="post" action="${ROOT}/recorddefs/name/">
<h1>
    ${ctxt.title}
    <ul class="e2l-actions">
        <li>
            <input value="${q or ''}" name="q" type="text" size="8" />
            <input type="submit" value="Search" />
        </li>
        % if create:
            <li><a class="e2-button" href="${ROOT}/recorddef/root/new/"><img src="${ROOT}/static/images/edit.png" alt="Edit" /> New</a></li>
        % endif
    </ul>
</h1>
</form>

${childmap}
