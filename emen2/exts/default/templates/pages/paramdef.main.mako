<%! import jsonrpc.jsonutil %>
<%inherit file="/pages/paramdef" />
<%namespace name="buttons" file="/buttons"  /> 
<%namespace name="forms" file="/forms"  /> 

<h1>
    ${ctxt.title}

    <ul class="e2l-actions">
        <li><a class="e2-button" href="${ROOT}/query/${paramdef.name}.!None./">${buttons.image('query.png', 'Query')} Query</a></li>

        % if editable:
            <li><a class="e2-button" href="${ROOT}/paramdef/${paramdef.name}/edit/">${buttons.image('edit.png', 'Edit')} Edit</a></li>
        % endif

        % if create:
            <li><a class="e2-button" href="${ROOT}/paramdef/${paramdef.name}/new/"><img src="${ROOT}/static/images/edit.png" alt="New" /> New</a></li>
        % endif
    </ul>
</h1>

<%buttons:singlepage label='Details'>
    ${self.paramdef_edit(paramdef, edit=edit, new=new)}
</%buttons:singlepage>

<%buttons:singlepage label='Data type and validation'>
    ${self.paramdef_edit_fixed(paramdef, edit=edit, new=new)}
</%buttons:singlepage>

<%buttons:singlepage label='History'>
    ${self.paramdef_edit_history(paramdef, edit=edit, new=new)}
</%buttons:singlepage>

<%buttons:singlepage label='Relationships'>
    <div id="e2-relationships" data-name="${paramdef.name}" data-keytype="${paramdef.keytype}"></div>
</%buttons:singlepage>
