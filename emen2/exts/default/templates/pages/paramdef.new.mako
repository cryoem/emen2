<%! import jsonrpc.jsonutil %>
<%inherit file="/pages/paramdef" />
<%namespace name="buttons" file="/buttons"  /> 
<%namespace name="forms" file="/forms"  /> 

<form method="post" action="${ctxt.reverse('ParamDef/new', name=paramdef.name)}">

<h1>
	${title}

	<span class="e2l-label">
		<input type="submit" value="Save" />
	<span>
</h1>


${self.paramdef_edit(paramdef, edit=edit, new=new)}

<%buttons:singlepage label='Relationships'>
	<div id="e2-relationships" data-name="${paramdef.name}" data-keytype="${paramdef.keytype}"></div>
</%buttons:singlepage>

</form>