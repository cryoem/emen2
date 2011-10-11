<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 
<%namespace name="forms" file="/forms"  /> 

<%block name="js_inline">
	${parent.js_inline()}
	${buttons.tocache(paramdef)}
</%block>

<%block name="js_ready">
	${parent.js_ready()}
	$('#e2-relationships').RelationshipControl({
		edit:true
	});
	$('.e2-map').MapControl({'attach':true});
</%block>

<%block name="precontent">
	${parent.precontent()}
	${parentmap}
</%block>


<%def name="paramdef_edit(paramdef, edit=False, new=False)">
	<table class="e2l-kv">

		<tr>
			<td>Short Description:</td>
			<td>
				% if edit:
					<input name="desc_short" value="${paramdef.desc_short or ''}" />
				% else:
					${paramdef.desc_short}
				% endif
			</td>
		</tr>

		<tr>
			<td>Detailed Description:</td>
			<td>
				% if edit:
					<textarea class="e2l-fw" name="desc_long">${paramdef.desc_long or ''}</textarea>
				% else:
					${paramdef.desc_long}
				% endif
			</td>
		</tr>

		% if paramdef.vartype=="choice":
			<tr>
				<td>Possible Values:</td>
				<td>
					<ul>
					% for i in paramdef.choices:
						<li>${i}</li>
					% endfor
					</ul>
				</td>
			</tr>

		% elif edit:

			<tr>
				<td>Suggested Values:</td>
				<td>
					<ul class="e2l-nonlist">
					% for i in paramdef.choices or []:					
						<li><input type="text" name="choices" value="${i}" /></li>
					% endfor
					% for i in range(2):
						<li><input type="text" name="choices" /></li>
					% endfor
						<li><input type="button" value="+" /></li>
					</ul>
				</td>
			</tr>

		% elif paramdef.choices:

			<tr>
				<td>Suggested Values:</td>
				<td>
					<ul>
					% for i in paramdef.choices:
						<li>${i}</li>
					% endfor
					</ul>
				</td>
			</tr>

		% endif

		<tr>
			<td>Control hint:</td>
			<td>
				% if edit:
					<input name="controlhint" value="${paramdef.get('controlhint') or ''}" />
				% else:
					${paramdef.get('controlhint')}
				% endif
			</td>
		</tr>
	</table>
	
	<%buttons:singlepage label='Immutable Options'>
	
		<p>These attributes cannot be easily changed after the parameter is created because
		they change the parameter's meaning, validation method, or index format. If you must change these
		attributes, the database must be taken offline and modified using the migration scripts.</p>
		
		<table class="e2l-kv">
			<tr>
				<td>Data Type:</td>
				<td>
					% if new:
						<select name="vartype" required>
							<option></option>
							% for vt in vartypes:
								<option>${vt}</option>
							% endfor
						</select>
					% else:
						${paramdef.vartype}
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
				<td>Physical Property:</td>
				<td>
					% if new:
						<select name="property">
							<option></option>
						</select>
					% else:
						${paramdef.property}
					% endif
				</td>
			</tr>

			<tr>
				<td>Default Units:</td>
				<td>
					% if new:
						<select name="defaultunits">
							<option></option>
						</select>
					% else:
						${paramdef.defaultunits}
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
						${paramdef.get('immutable')}
					% endif
				</td>
			</tr>		

			% if not new:
				<tr>
					<td>Created:</td>
					<td><a href="${EMEN2WEBROOT}/user/${paramdef.creator}">${paramdef.creator}</a> @ ${paramdef.creationtime}</td>
				</tr>

				<tr>
					<td>Modified:</td>
					<td><a href="${EMEN2WEBROOT}/user/${paramdef.modifyuser}">${paramdef.modifyuser}</a> @ ${paramdef.modifytime}</td>
				</tr>
			% endif
		</table>
	</%buttons:singlepage>
	
</%def>


<h1>
	${title}

	<span class="e2l-label"><a href="${EMEN2WEBROOT}/query/${paramdef.name}.!None./"><img src="${EMEN2WEBROOT}/static/images/query.png" alt="Query" /> Query</a></span>	

	% if editable:
		<span class="e2l-label"><a href="${EMEN2WEBROOT}/paramdef/${paramdef.name}/edit/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> Edit</a></span>
	% endif

	% if create:
		<span class="e2l-label"><a href="${EMEN2WEBROOT}/paramdef/${paramdef.name}/new/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="New" /> New</a></span>
	% endif
</h1>

<form action="${EMEN2WEBROOT}/paramdef/${paramdef.name}/edit/" method="post">
	${paramdef_edit(paramdef, edit=edit, new=new)}
	
	% if edit:
		<ul class="e2l-controls">
			<li><input type="submit" value="Save" /></li>
		</ul>
	% endif
</form>


<br />

##<%buttons:singlepage label='Relationships'>
##	<div id="e2-relationships" data-name="${paramdef.name}" data-keytype="${paramdef.keytype}"></div>
##</%buttons:singlepage>
