<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 
<%namespace name="forms" file="/forms"  /> 


<%block name="js_ready">
	${parent.js_ready()}
	${buttons.tocache(paramdef)}
	$('#e2-relationships').RelationshipControl({
		edit: ${jsonrpc.jsonutil.encode(edit)}
	});
	
	// Add choices
	$('.e2-paramdef-addchoices').click(function(){
		var elem = $(this);
		elem.parent().before('<li><input type="text" name="choices" value="" /></li>');
		elem.parent().before('<li><input type="text" name="choices" value="" /></li>');
		elem.parent().before('<li><input type="text" name="choices" value="" /></li>');
	})
	
	$('.e2-tree').TreeControl({'attach':true});
</%block>


<%block name="precontent">
	${parent.precontent()}
	<div class="e2-tree-main" style="overflow:hidden">${parentmap}</div>
</%block>


<%def name="paramdef_edit(paramdef, edit=False, new=False)">
	<table class="e2l-kv">

		<tr>	
			<td>Name:</td>
			<td>
				% if new:
					<input name="name" value="" />
				% else:
					${paramdef.name or ''}
				% endif
			</td>
		</tr>

		<tr>
			<td>Short description:</td>
			<td>
				% if edit:
					<input name="desc_short" value="${paramdef.desc_short or ''}" required />
				% else:
					${paramdef.desc_short or ''}
				% endif
			</td>
		</tr>

		<tr>
			<td>Detailed description:</td>
			<td>
				% if edit:
					<textarea class="e2l-fw" name="desc_long" required>${paramdef.desc_long or ''}</textarea>
				% else:
					${paramdef.desc_long or ''}
				% endif
			</td>
		</tr>

		<tr>
			<td>
			% if paramdef.vartype == 'choice':
				Permitted values:
			% else:
				Suggested values:
			% endif
			</td>
			<td>
				<ul class="e2l-nonlist">
				% if edit:
					% for i in paramdef.choices or []:					
						<li><input type="text" name="choices" value="${i}" /></li>
					% endfor
						<li><input type="text" name="choices" /></li>
						<li><input type="text" name="choices" /> <input class="e2-paramdef-addchoices" type="button" value="+" /></li>
				% else:
					% for i in paramdef.choices or []:
						<li>${i}</li>
					% endfor
				% endif
				</ul>
			</td>
		</tr>

		<tr>
			<td>Control hint:</td>
			<td>
				% if edit:
					<input name="controlhint" value="${paramdef.get('controlhint') or ''}" />
				% else:
					${paramdef.get('controlhint') or ''}
				% endif
			</td>
		</tr>
	
		% if edit:
		<tr>
			<td colspan="2">
				The following attributes cannot be easily changed after the parameter is created because
				they change the parameter's meaning, validation method, or index format. If you must change these
				attributes, the database must be taken offline and modified using the migration scripts.
			</td>
		</tr>
		% endif
		
		<table class="e2l-kv">
			<tr>
				<td>Data type:</td>
				<td>
					% if new:
						<select name="vartype" required>
							<option></option>
							% for vt in vartypes:
								<option>${vt}</option>
							% endfor
						</select>
					% else:
						${paramdef.vartype or ''}
					% endif
				</td>
			</tr>

			<tr>
				<td>Iterable:</td>
				<td>
					% if new:
						<input type="checkbox" name="iter" ${forms.ifchecked(paramdef.iter)} />
					% else:
						${paramdef.iter}
					% endif
				</td>
			</tr>

			<tr>
				<td>Physical property:</td>
				<td>
					% if new:
						<select name="property" disabled>
							<option value="">Select a data type that permits physical properties</option>
							% for property in properties:
								<option>${property}</option>
							% endfor
						</select>
					% else:
						${paramdef.property or ''}
					% endif
				</td>
			</tr>

			<tr>
				<td>Default units:</td>
				<td>
					% if new:
						<select name="defaultunits" disabled>
							<option value="">Select a property</option>
						</select>
					% else:
						${paramdef.defaultunits or ''}
					% endif
				</td>
			</tr>

			<tr>
				<td>Indexed:</td>
				<td>
					% if new:
						<input type="checkbox" name="indexed" ${forms.ifchecked(paramdef.indexed)} />
					% else:
						${paramdef.indexed}
					% endif
				</td>
			</tr>
		
			<tr>
				<td>Immutable:</td>
				<td>
					% if new:
						<input type="checkbox" name="immutable" ${forms.ifchecked(paramdef.get('immutable'))} />
					% else:
						${bool(paramdef.get('immutable'))}
					% endif
				</td>
			</tr>		

			% if not new:
				<tr>
					<td>Created:</td>
					<td><a href="${EMEN2WEBROOT}/user/${paramdef.creator}">${paramdef.creator}</a> @ <time class="e2-localize" datetime="${paramdef.creationtime}">${paramdef.creationtime}</time></td>
				</tr>

				<tr>
					<td>Modified:</td>
					<td><a href="${EMEN2WEBROOT}/user/${paramdef.modifyuser}">${paramdef.modifyuser}</a> @ <time class="e2-localize" datetime="${paramdef.modifytime}">${paramdef.modifytime}</time></td>
				</tr>
			% endif
		</table>
</%def>


${next.body()}
