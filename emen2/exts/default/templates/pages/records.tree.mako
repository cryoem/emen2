<%inherit file="/page" />

<%block name="js_ready">
    ${parent.js_ready()}
    $('#sitemap').TreeControl({
        'attach':true,
        'keytype':'record'
    });
</%block>


<h1>
    ${title}
    <ul class="e2l-actions">
        <li><a href="${EMEN2WEBROOT}/records/edit/relationships/?root=${root}" class="e2-button">Edit relationships</a></li>
    </ul>
</h1>

${childmap}
