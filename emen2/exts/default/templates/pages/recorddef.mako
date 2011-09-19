<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 
<%
import markdown
%>

<h1>
	${title}
	
	<span class="label"><a href="${EMEN2WEBROOT}/query/rectype==${recdef.name}/"><img src="${EMEN2WEBROOT}/static/images/query.png" alt="Query" /> Query</a></span>	
	
	% if editable:
		<span class="label"><a href="${EMEN2WEBROOT}/recorddef/${recdef.name}/edit/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> Edit</a></span>
	% endif

	% if create:
		<span class="label"><a href="${EMEN2WEBROOT}/recorddef/${recdef.name}/new/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="New" /> New</a></span>
	% endif
</h1>


<%buttons:singlepage label='Protocol Details'>
	<table>
		<tr><td>Name:</td><td>${recdef.name}</td></tr>		
		<tr><td>Created:</td><td><a href="${EMEN2WEBROOT}/user/${recdef.creator}/">${displaynames.get(recdef.creator, recdef.creator)}</a> @ ${recdef.creationtime}</td></tr>
		<tr><td>Owner:</td><td>${recdef.owner}</td></tr>

		<tr>
			<td>Private:</td>
			<td>
				${["No","Yes"][recdef.private]}		
			</td>
		</tr>

		<tr>
			<td>Suggested Child Types</td>
			<td>
			% if len(recdef.typicalchld) == 0:
				None Defined
			% else:
				<ul id="typicalchld" class="nonlist">
				% for k,i in enumerate(recdef.typicalchld):
					<li><a href="${EMEN2WEBROOT}/recorddef/${i}/">${i}</a></li>
				% endfor

				</ul>
			% endif
			</td>
	
		</tr>

		<tr>
			
			<td>Short Description</td>
			<td>
				${recdef.get("desc_short")}
			</td>
	
		</tr>

		<tr>
			<td colspan="2">
				<p>Detailed Description</p>
				<p>
						${recdef.get("desc_long")}
				</p>
			</td>
		</tr>
	</table>
</%buttons:singlepage>


<%buttons:singlepage label='Protocol'>
	${markdown.markdown(recdef.mainview)}
</%buttons:singlepage>




${buttons.buttons(pages_recdefviews)}
<%call expr="buttons.pageswrap(pages_recdefviews)">
	% for k,v in pages_recdefviews.content.items():
		<%call expr="buttons.pagewrap(pages_recdefviews,k)">
			${markdown.markdown(v)}			
		</%call>

	% endfor
			
</%call>



</form>
