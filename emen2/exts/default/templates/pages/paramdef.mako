<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 
<% import jsonrpc.jsonutil %>

<h1>
	${title}

	<span class="label"><a href="${EMEN2WEBROOT}/query/${paramdef.name}.!None./"><img src="${EMEN2WEBROOT}/static/images/query.png" alt="Query" /> Query</a></span>	

	% if editable:
		<span class="label"><a href="${EMEN2WEBROOT}/paramdef/${paramdef.name}/edit/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> Edit</a></span>
	% endif

	% if create:
		<span class="label"><a href="${EMEN2WEBROOT}/paramdef/${paramdef.name}/new/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="New" /> New</a></span>
	% endif
</h1>



<%buttons:singlepage label='Parameter Details'>
	<table>
		<tr>
			<td>Description:</td>
			<td>${paramdef.desc_long}</td>
		</tr>

		<tr>
			<td>Short Description:</td>
			<td>${paramdef.desc_short}</td>
		</tr>

		<tr>
			<td>Created:</td>
			<td>${displaynames.get(paramdef.creator,"(%s)"%(paramdef.creator))} (<a href="${EMEN2WEBROOT}/user/${paramdef.creator}">${paramdef.creator}</a>) @ ${paramdef.creationtime}</td>
		</tr>

		<tr>
			<td>Data Type:</td>
			<td>${paramdef.vartype}</td>
		</tr>

		<tr>
			<td>Physical Property:</td>
			<td>${paramdef.property or ""}</td>
		</tr>

		<tr>
			<td>Default Units:</td>
			<td>${paramdef.defaultunits or ""}</td>
		</tr>

		<tr>
			<td>Indexed:</td>
			<td>${paramdef.indexed}</td>
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
	</table>
</%buttons:singlepage>
