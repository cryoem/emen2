<%namespace name="buttons" file="/buttons"  /> 
<%namespace name="forms" file="/forms"  /> 

## This is a separate template so it can be easily overridden 
## without reimplementing the entire new User template.

<%buttons:singlepage label='Contact Information'>
	<table  class="e2l-kv">	
		<tbody>					

			<tr>
				<td>First Name:</td>
				<td><input name="name_first" type="text" value="${kwargs.get('name_first','')}" required /></td>
			</tr>

			<tr>
				<td>Middle Name:</td>
				<td><input name="name_middle" type="text" value="${kwargs.get('name_middle','')}" /></td>
			</tr>

			<tr>
				<td>Last Name:</td>
				<td><input name="name_last" type="text" value="${kwargs.get('name_last','')}" required /></td>
			</tr>

			<tr>
				<td>Institution:</td>
				<td><input name="institution" type="text" value="${kwargs.get('institution','')}" required /></td>
			</tr>
			<tr>
				<td>Department:</td>
				<td><input name="department" type="text" value="${kwargs.get('department','')}" required /></td>
			</tr>

			<tr>
				<td>Street Address:</td>
				<td><input name="address_street" type="text" value="${kwargs.get('address_street','')}" required /></td>
			</tr>
			<tr>
				<td>City:</td>
				<td><input name="address_city" type="text" value="${kwargs.get('address_city','')}" required /></td>
			</tr>
			<tr>
				<td>State:</td>
				<td><input name="address_state" type="text" value="${kwargs.get('address_state','')}" required /></td>
			</tr>
			<tr>
				<td>Zipcode:</td>
				<td><input name="address_zipcode" type="text" value="${kwargs.get('address_zipcode','')}" required /></td>
			</tr>
			<tr>
				<td>Country:</td>
				<td>			
					<select name="country" required />
						${forms.countries()}
					</select>
				</td>
			</tr>

		</tbody>
	</table>
</%buttons:singlepage>

<br />

<%buttons:singlepage label='Additional Information (optional)'>
	<table class="e2l-kv">	
		<tbody>					
			<tr>
				<td>Phone:</td>
				<td><input name="phone_voice" type="text" value="${kwargs.get('phone_voice','')}"></td>
			</tr>

			<tr>
				<td>Fax:</td>
				<td><input name="phone_fax" type="text" value="${kwargs.get('phone_fax','')}"></td>
			</tr>

			<tr>
				<td>Web page:</td>
				<td><input name="uri" type="text" value="${kwargs.get('uri','')}"></td>
			</tr>
		</tbody>
	</table>
</%buttons:singlepage>

<br />

<%buttons:singlepage label='Comments'>
	<p>Please let us know why you are requesting an account:</p>
	<p>
		<textarea class="e2l-fw" name="comments">${kwargs.get('comments','')}</textarea>
	</p>
</%buttons:singlepage>
