## -*- coding: utf-8 -*-
<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 
<% import jsonrpc.jsonutil %>


<script type="text/javascript">
//<![CDATA[

	$(document).ready(function() {
		$('#paramdef_edit').ParamDefEditControl({
			newdef: ${jsonrpc.jsonutil.encode(new)},
			parents:['${paramdef.name}'],
			ext_save: "#ext_save",
		});
	});

//]]>	
</script>


<h1>
	${title}

	<div class="controls save" id="ext_save">
		<img class="e2l-spinner hide" src="${EMEN2WEBROOT}/static/images/spinner.gif" alt="Loading" />
		<input type="button" value="Save" name="save">
	</div>	

</h1>

<form action="" method="get" id="paramdef_edit">


<table>

	<tr>
		<td>Name</td>
		<td>
		% if action=="new":
			<input type="text" name="name" value="" />
		% else:
			${paramdef.name}
			<input type="hidden" name="name" value="${paramdef.name}" />
		% endif
		</td>
	</tr>
	
	<tr>
		<td>Short Description</td>
		<td><input type="text" name="desc_short" value="${paramdef.desc_short or ""}"/></td>
	</tr>
	
	<tr>
		<td>Long Description</td>
		<td>
			<textarea name="desc_long" cols="80" rows="5" />${paramdef.desc_long or ""}</textarea>
		</td>
	</tr>	
	
	<tr>
		<td>Default Choices</td>
		<td>
			<ul class="e2l-nonlist">
				% for i,j in enumerate(list(paramdef.choices or [])+[""]*6):
					<li><input type="text" name="choices" value="${j}"></li>
				% endfor
			</ul>
		</td>
	</tr>
	
	<tr>
		<td>UI Control</td>
		<td><input type="text" name="controlhint" value="${paramdef.get('controlhint') or ""}"/></td>
	</tr>
	
	<tr>
		<td>Immutable</td>
		<td>
			% if new:
				% if paramdef.get('immutable'):
					<input type="checkbox" name="immutable" checked="checked">
				% else:
					<input type="checkbox" name="immutable">
				% endif
			% else:
				${paramdef.get('immutable', False)}
			% endif
		</td>
	</tr>	

	<tr>
		<td>Indexed</td>
		<td>
			% if new:			
				% if paramdef.get('indexed', False):
					<input type="checkbox" name="indexed" checked="checked" />
				% else:
					<input type="checkbox" name="indexed" />
				% endif
			% else:
				${paramdef.get('indexed', False)}
			% endif
		</td>
	</tr>	
	
	<tr>
		<td>Data Type</td>
		<td>
			% if new:
				<select name="vartype">
					% for i in sorted(vartypes):
						<option value="${i}" ${['','selected="selected"'][i==paramdef.vartype]}>${i}</option>
					% endfor
				</select>
			% else:
				${paramdef.vartype}
			% endif
		</td>
	</tr>
	
	<tr>
		<td>Property</td>
		<td>
			% if new:
				<select name="property">
					<option value=""></option>
					% for i in sorted(properties):
						<option value="${i}" ${['','selected="selected"'][i==paramdef.property]}>${i}</option>
					% endfor
				</select>
			% else:
				${paramdef.property}
			% endif
		</td>
	</tr>

	<tr>
		<td>Default Units</td>
		<td>
			% if new:
				<select name="defaultunits">
					% if paramdef.property:
						% for i in units:
							<option value="${i}"  ${['','selected="selected"'][i==paramdef.defaultunits]}>${unicode(i)}</option>
						% endfor
					% else:
						<option value="">(select property)</option>
					% endif
				</select>
			% else:
				${paramdef.defaultunits}
			% endif
		</td>
	</tr>
		
</table>							



</form>


## <h1>Relationships<h1>
## <div id="reledit">
## </div>


