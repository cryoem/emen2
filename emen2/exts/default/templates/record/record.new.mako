<%!
    import jsonrpc.jsonutil
    import markdown
%>
<%inherit file="/record/record" />
<%namespace name="buttons" file="/buttons" />

<%block name="js_ready">
    ${parent.js_ready()}
    ${buttons.tocache(newrec)}
    ${buttons.tocache(recdef)}
    
    // Save Record
    $('#e2-edit').MultiEditControl({
        show: true,
        permissions: $('#e2-permissions')
    });

    // var tab = $('#e2-tab-editbar');
    // tab.TabControl({});

    // Permissions editor
    // tab.TabControl('setcb','permissions', function(page){
    //    // console.log('perm');
    //    $('#e2-permissions', page).PermissionsControl({
    //        name: 'None',
    //        show: true,
    //        edit: true
    //    });
    // });
    
</%block>



<div class="e2l-help">
    <p>
        You are creating a new <a href="${ctxt.reverse('RecordDef/main', name=recdef.name)}">${recdef.desc_short}</a> record as a child of <a href="${ctxt.reverse('Record/main', name=rec.name)}">${recnames.get(rec.name, rec.name)}</a>
    </p>
    ${markdown.markdown('<strong>Protocol description:</strong>\n'+recdef.desc_long)}
</div>

<div data-tab="permissions">
    ## This form will be copied into the main form during submit
    <form id="e2-permissions"></form>
</div>


## Main rendered record

<form id="e2-edit" data-name="None" method="post" action="${EMEN2WEBROOT}/record/${rec.name}/new/${newrec.rectype}/" enctype="multipart/form-data">
    <div id="rendered" class="e2-view" data-viewname="${viewname}">
        ${rendered}
    </div>

    <div class="e2l-controls">
        <input type="submit" value="Save">
    </div>
</form>



