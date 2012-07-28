<%! import jsonrpc.jsonutil %>
<%inherit file="/record/record" />
<%namespace name="buttons" file="/buttons"  /> 

<%block name="js_ready">
    ${parent.js_ready()}
    $('#publishmap').TreeSelectControl({
        attach: true,
        active: ${jsonrpc.jsonutil.encode(published)},
        display_count: '#publish_count'
    });
</%block>


<form method="post" action="">
<h1>
    Manage public data &mdash; <span id="publish_count">${len(published)}</span> records selected
    <ul class="e2l-actions">
        <li><button type="submit" id="publish_save">${buttons.spinner(False)} Save</button></li>
    </ul>
</h1>

<div class="e2l-shaded-drop">
    <p>
        Records marked in "orange" will be marked as public data when this form is saved. The number of selected records is shown above.
    </p>
    <p>
        Click on a record to select or deselect it. 
        You can also hold down "shift" while clicking to select or deselect all the children of that record.
    </p>
</div>

<br /><br />

<div id="publishmap">
    ${childmap}
</div>

</form>