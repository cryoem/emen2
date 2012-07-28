<%! import jsonrpc.jsonutil %>
<%inherit file="/pages/paramdef" />
<%namespace name="buttons" file="/buttons"  /> 
<%namespace name="forms" file="/forms"  /> 

<form method="post" action="${ctxt.reverse('ParamDef/edit', name=paramdef.name)}">

<h1>
    ${title}
    <ul class="e2l-actions">
        <li><input type="submit" value="Save" /></li>
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

</form>