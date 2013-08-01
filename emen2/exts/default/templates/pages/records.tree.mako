<%inherit file="/page" />

<%block name="js_ready">
    ${parent.js_ready()}
    $('#sitemap').TreeControl({
        'attach':true,
        'keytype':'record'
    });
</%block>

<h1>
    ${ctxt.title}
    <ul class="e2l-actions">
        <li><a href="${ctxt.root}/records/edit/relationships/?root=${root}" class="e2-button">Edit relationships</a></li>
    </ul>
</h1>

## Disable filtering -- this comes from another template.
${childmap | n,unicode}
