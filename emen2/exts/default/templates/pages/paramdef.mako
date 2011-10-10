<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

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


<%def name="paramdef_edit(paramdef, edit=True, new=True)">
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
			<td>Data Type:</td>
			<td>
				% if new:
					<input name="vartype" value="${paramdef.vartype or ''}" />
				% else:
					${paramdef.vartype}
				% endif
			</td>
		</tr>

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

		<tr>
			<td>Iterable:</td>
			<td>
				% if new:
					<input name="iter" value="${paramdef.iter or ''}" />
				% else:
					${paramdef.iter}
				% endif
			</td>
		</tr>

		<tr>
			<td>Physical Property:</td>
			<td>
				% if new:
					<input name="property" value="${paramdef.property or ''}" />
				% else:
					${paramdef.property}
				% endif
			</td>
		</tr>

		<tr>
			<td>Default Units:</td>
			<td>
				% if new:
					<input name="defaultunits" value="${paramdef.defaultunits or ''}" />
				% else:
					${paramdef.defaultunits}
				% endif
			</td>
		</tr>

		<tr>
			<td>Indexed:</td>
			<td>
				% if new:
					<input name="indexed" value="${paramdef.indexed or ''}" />
				% else:
					${paramdef.indexed}
				% endif
			</td>
		</tr>
		
		<tr>
			<td>Immutable:</td>
			<td>
				% if new:
					<input name="immutable" value="${paramdef.immutable or ''}" />
				% else:
					${paramdef.immutable}
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


${paramdef_edit(paramdef, True)}

<br />

<%buttons:singlepage label='Relationships'>
	<div id="e2-relationships" data-name="${paramdef.name}" data-keytype="${paramdef.keytype}"></div>
</%buttons:singlepage>

