<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 
<% import jsonrpc.jsonutil %>


<script type="text/javascript">
//<![CDATA[

	$(document).ready(function() {
		$('#recdef_edit').RecordDefEditControl({
			newdef: ${jsonrpc.jsonutil.encode(new)},
			parents:['${recdef.name}'],
			ext_save: "#ext_save"
		});
		
##		$("#reledit").RelationshipControl({
##			name: '${recdef.name}',
##			keytype: 'recorddef',
##			edit: true,
##			embed: true,
##			show: true
##			});
		
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

<form action="" method="get" id="recdef_edit">


<%buttons:singlepage label='Protocol Details'>
	<table>
	

		% if new:
			<tr><td>Name:</td><td><input type="text" name="name" value="" /></td></tr>
		% else:
			<tr><td>Name:</td><td>${recdef.name}</td></tr>
			<tr><td>Created:</td><td><a href="${EMEN2WEBROOT}/users/${recdef.creator}/">${displaynames.get(recdef.creator, recdef.creator)}</a> @ ${recdef.creationtime}</td></tr>
			<tr><td>Owner:</td><td>${recdef.owner}</td></tr>
			<input type="hidden" name="name" value="${recdef.name}" />
		% endif
	

		<tr>
			<td>Private:</td>
			<td>
				<input type="checkbox" ${['','checked="checked"'][recdef.private]} name="private" />
			</td>
		</tr>

		<tr>
			<td>Suggested Child Types</td>
			<td>
				<ul id="typicalchld" class="e2l-nonlist">
				% for k,i in enumerate(recdef.typicalchld):
					<li><input type="text" value="${i}" name="typicalchld"></li>
				% endfor

				<li><input type="text" name="typicalchld"></li>			
				<li><input type="text" name="typicalchld"></li>			
				<li><input type="text" name="typicalchld"></li>			
				<li><input type="text" name="typicalchld"></li>			
				<li><input type="text" name="typicalchld"></li>			

				</ul>
			</td>
	
		</tr>

		<tr>
			
			<td>Short Description</td>
			<td>
				<input type="text" name="desc_short" value="${recdef.get("desc_short","")}" />
			</td>
	
		</tr>

		<tr>
			<td colspan="2">
				<p>Detailed Description</p>
				<p>
					<textarea cols="80" rows="10" name="desc_long">${recdef.get("desc_long") or ""}</textarea>
				</p>
			</td>
		</tr>


	</table>
</%buttons:singlepage>




<%buttons:singlepage label='Protocol'>
		<input type="hidden" value="mainview" name="viewkey_mainview" data-t="mainview" />
		<textarea cols="80" rows="30" name="view_mainview" data-t"mainview">${recdef.mainview}</textarea>
</%buttons:singlepage>



${buttons.buttons(pages_recdefviews)}
<%call expr="buttons.pageswrap(pages_recdefviews)">
	% for k,v in pages_recdefviews.content.items():
		<%call expr="buttons.pagewrap(pages_recdefviews,k)">

				<ul class="recdef_edit_actions e2l-clearfix">
					<li>Name: <input type="text" value="${k}" data-t="${k}" name="viewkey_${k}" /></li>
					<li>Copy: <select name="viewcopy_${k}" data-t="${k}" /></li>
					<li class="recdef_edit_action_remove" data-t="${k}"><img src="${EMEN2WEBROOT}/static/images/remove_small.png" alt="Remove" /> Remove</li>
				</ul>
					
				<textarea cols="80" rows="30" data-t="${k}" name="view_${k}">${v}</textarea>
		
		</%call>

	% endfor
	
	
	<%call expr="buttons.pagewrap(pages_recdefviews,'new')">
		No additional views defined; why not add some?				
	</%call>
	
</%call>


</form>


## <h1>Relationships<h1>
## <div id="reledit">
## </div>





