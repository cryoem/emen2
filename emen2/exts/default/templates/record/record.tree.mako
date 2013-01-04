<%inherit file="/record/record" />

<%block name="js_ready">
    ${parent.js_ready()}
    $('#sitemap').TreeControl({
        'attach':true,
        'keytype':'record'
    });
</%block>


<h1>
    Record tree 
    ## starting at ${recnames.get(rec.name)} (${rec.name})
    <ul class="e2l-actions">
        <li><a href="${ctxt.root}/records/edit/relationships/?root=${rec.name}" class="e2-button">"Drag &amp; drop" relationship editor</a></li>
    </ul>
</h1>

## Disable filtering -- this comes from a template.
${childmap | n,unicode}
