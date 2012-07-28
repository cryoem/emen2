<%inherit file="/page" />

<%block name="js_ready">
    ${parent.js_ready()}
    $('#sitemaptest').TreeMoveControl({
        'attach':true,
        'keytype':'record',
        'shiftselect': false
    });
</%block>


<h1>
    ${title}
    <ul class="e2l-actions">
        <li><a href="${EMEN2WEBROOT}/records/?root=${root}" class="e2-button">Done editing</a></li>
    </ul>    
</h1>

<div class="e2l-shaded-drop">
    <p>
        Click to select a record; it will become highlighted in orange. Each selected record represents a single parent-child relationship.
    </p>
    <p>
        Drag a selected record to a different parent to move all the currently selected records. In each case, the parent in each selected parent-child relationship will be replaced with the new parent.
    </p>
    <p>
        <strong>Important Note:</strong>
        Generally, DO NOT move a record to one of its children. This is highly likely to create an orphan tree, as well as a circular relationship.
    </p>
</div>

<br /><br />

<form id="sitemaptest" method="post" action="">
    <input type="hidden" name="root" value="${root}" />
    ${childmap}
</form>
