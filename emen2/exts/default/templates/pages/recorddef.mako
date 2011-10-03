<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 
<%
import markdown
%>

<%block name="js_ready">
	${parent.js_ready()}
	$('.e2-tab').TabControl({});
	$('.e2-map').MapControl({'attach':true});	
</%block>

<h1>
	${title}
	
	<span class="e2l-label"><a href="${EMEN2WEBROOT}/query/rectype==${recdef.name}/"><img src="${EMEN2WEBROOT}/static/images/query.png" alt="Query" /> Query</a></span>	
	
	% if editable:
		<span class="e2l-label"><a href="${EMEN2WEBROOT}/recorddef/${recdef.name}/edit/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> Edit</a></span>
	% endif

	% if create:
		<span class="e2l-label"><a href="${EMEN2WEBROOT}/recorddef/${recdef.name}/new/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="New" /> New</a></span>
	% endif
</h1>


## Protocol details

<table class="e2l-kv">
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
			<ul id="typicalchld">
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


## Views

<div class="e2-tab e2-tab-switcher">
	<ul class="e2l-cf">
		<li data-tab="mainview" class="e2-tab-active"><span class="e2l-a">Protocol</span></li>
		<li data-tab="tabularview"><span class="e2l-a">Table</span></li>
		<li data-tab="recname"><span class="e2l-a">Record Name</span></li>	
	</ul>
	<div data-tab="mainview" class="e2-tab-active">mainview</div>
	<div data-tab="tabularview">tabularview</div>
	<div data-tab="recname">recname</div>
</ul>
