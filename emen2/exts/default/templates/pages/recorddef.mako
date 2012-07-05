<%! import markdown %>
<%inherit file="/page" />
<%namespace name="buttons" file="/buttons" /> 

<%block name="js_ready">
	${parent.js_ready()}
	$('.e2-tab').TabControl({});
	$('.e2-tree').TreeControl({'attach':true});	
</%block>

<%block name="precontent">
	${parent.precontent()}
	<div class="e2-tree-main" style="overflow:hidden">${parentmap}</div>
</%block>


<h1>
	${title}
</h1>


<form action="${ctxt.reverse('RecordDef/edit', name=recorddef.name)}" method="post">

	<table class="e2l-kv">
		<tbody>
			<tr>
				<td>Name:</td>
				<td>${recorddef.name}</td>
			</tr>		

			<tr>
				<td>Created:</td>
				<td><a href="${EMEN2WEBROOT}/user/${recorddef.creator}/">${recorddef.creator}</a> @ <time class="e2-localize" datetime="${recorddef.creationtime}">${recorddef.creationtime}</time></td>
			</tr>

			<tr>
				<td>Private:</td>
				<td>
					${["No","Yes"][recorddef.private]}		
				</td>
			</tr>

			<tr>
				<td>Suggested child protocols</td>
				<td>
				% if len(recorddef.typicalchld) == 0:
					None Defined
				% else:
					<ul id="typicalchld">
					% for k,i in enumerate(recorddef.typicalchld):
						<li><a href="${EMEN2WEBROOT}/recorddef/${i}/">${i}</a></li>
					% endfor

					</ul>
				% endif
				</td>

			</tr>

			<tr>
	
				<td>Short Description</td>
				<td>
					${recorddef.get("desc_short")}
				</td>

			</tr>

			<tr>
				<td colspan="2">
					<p>Detailed Description</p>
					<p>
						${recorddef.get("desc_long")}
					</p>
				</td>
			</tr>
		</tbody>
	</table>
	
	<%buttons:singlepage label='Protocol'>
		${markdown.markdown(recorddef.mainview)}
	</%buttons:singlepage>

	<%buttons:singlepage label='Relationships'>
		<div id="e2-relationships" data-name="${recorddef.name}" data-keytype="${recorddef.keytype}"></div>
	</%buttons:singlepage>


	<ul>
		
		
	</ul>

	% if edit:
		<ul class="e2l-controls">
			<li><input type="submit" value="Save" /></li>
		</ul>
	% endif

</form>