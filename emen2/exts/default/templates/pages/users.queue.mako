<%inherit file="/page" />
<%namespace name="forms" file="/forms"  /> 

<%block name="js_ready">
	${parent.js_ready()}
	
	$('input[name=all]').click(function(){
		$('input[value='+$(this).val()+']').attr('checked', true);
	});
</%block>

<h1>${title} (${len(queue)})</h1>

<form method="post" action="${ctxt.reverse('Users/queue')}">

<table class="e2l-shaded">
	<thead>
		<tr>

			<th style="width:16px">
				<input type="radio" name="all" value="approve" />
			</th>
			<th style="width:16px">
				<input type="radio" name="all" value="reject" />
			</th>
			
			<th>Email</th>
			<th>Name</th>
			<th>Comments</th>
			<th>Additional details</th>
		</tr>
	</thead>
	
	<tbody>
		% for user in queue:
			<tr>
				<td><input type="radio" name="actions.${user.name}" value="approve" ${forms.ifchecked(actions.get(user.name)=='approve')} /></td>
				<td><input type="radio" name="actions.${user.name}" value="reject" ${forms.ifchecked(actions.get(user.name)=='reject')} /></td>

				<td>${user.email}</td>
				<td>${user.signupinfo.get('name_last', '')}, ${user.signupinfo.get('name_first', '')} ${user.signupinfo.get('name_middle', '')}</td>
				<td>${user.signupinfo.get('comments', '')}</td>
				<td>
					<%
					details = {}
					for k in set(user.signupinfo.keys())-set(['email','name_first','name_middle','name_last','comments']):
						details[k] = user.signupinfo[k]
					%>
					% for k,v in sorted(details.items()):
						${k}: ${v}, 
					% endfor				
				</td>
			</tr>
		% endfor
	</tbody>
</table>

<ul class="e2l-controls">
	<li><input type="submit" value="Accept checked users" /></li>
</u>

</form>