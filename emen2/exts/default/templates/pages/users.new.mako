<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 
<%namespace name="forms" file="/forms"  /> 

<%block name="js_ready">
	${parent.js_ready()}
	var invalid = ${jsonrpc.jsonutil.encode(invalid)};
	var country = ${jsonrpc.jsonutil.encode(kwargs.get('country','United States'))};
	$('select[name=country]').val(country);
	$.each(invalid, function() {
		$('input[name='+this+']').addClass("e2l-error");
	})
</%block>


<%block name="css_inline">
	.signup td:first-child {
		text-align:right;
	}
</block>


<h1>Welcome to ${EMEN2DBNAME}</h1>

<p>Please complete this form to create an ${EMEN2DBNAME} account. We request detailed contact information because this is included in our grant reports.</p>

<p>If you are requesting access to a particular project, please let us know in the comments.</p>	

<p>New accounts must be approved by an administrator before you may login. You will receive an email acknowledging your request, and a second email when your account is approved.</p>


% if error:
<div class="notify error">${error}</div>
% endif

% if invalid-set(['password','password2']):
<div class="notify error">Please complete the following items marked in red:</div>
% endif


<form id="form_newuser" action="${EMEN2WEBROOT}/users/new/save/" method="post" enctype="charset=utf-8">

<%buttons:singlepage label='Account Details (required)'>

	<table class="e2l-kv">	
		<tbody>					
			<tr>
				<td>Account Name:</td>
				<td>
					<input name="name" type="text" value="${kwargs.get('name','')}">
					<span class="e2l-small">Please use 'firstnamelastname' format</span>
				</td>
			</tr>
		
			<tr>
				<td>Email:</td>
				<td><input name="email" type="text" value="${kwargs.get('email','')}"></td>
			</tr>

			<tr>
				<td>Password:</td>
				<td>
					<input name="password" type="password">
					<span class="e2l-small">Minimum 6 characters</span>
				</td>
			</tr>

			<tr>
				<td>Re-enter Password:</td>
				<td>
					<input name="password2" type="password">
				</td>
			</tr>
		</tbody>
	</table>
</%buttons:singlepage>

<br />

<%buttons:singlepage label='Contact Information (required)'>
	<table  class="e2l-kv">	
		<tbody>					

			<tr>
				<td>First Name:</td>
				<td><input name="name_first" type="text" value="${kwargs.get('name_first','')}"></td>
			</tr>

			<tr>
				<td>Middle Name:</td>
				<td><input name="name_middle" type="text" value="${kwargs.get('name_middle','')}"> <span class="e2l-small">Optional</span></td>
			</tr>

			<tr>
				<td>Last Name:</td>
				<td><input name="name_last" type="text" value="${kwargs.get('name_last','')}"></td>
			</tr>

			<tr>
				<td>Institution:</td>
				<td><input name="institution" type="text" value="${kwargs.get('institution','')}"></td>
			</tr>
			<tr>
				<td>Department:</td>
				<td><input name="department" type="text" value="${kwargs.get('department','')}"></td>
			</tr>

			<tr>
				<td>Street Address:</td>
				<td><input name="address_street" type="text" value="${kwargs.get('address_street','')}"></td>
			</tr>
			<tr>
				<td>City:</td>
				<td><input name="address_city" type="text" value="${kwargs.get('address_city','')}"></td>
			</tr>
			<tr>
				<td>State:</td>
				<td><input name="address_state" type="text" value="${kwargs.get('address_state','')}"></td>
			</tr>
			<tr>
				<td>Zipcode:</td>
				<td><input name="address_zipcode" type="text" value="${kwargs.get('address_zipcode','')}"></td>
			</tr>
			<tr>
				<td>Country:</td>
				<td>
			
				## <input name="country" type="text" value="${kwargs.get('country','')}">
				## ISO 3166-1
				<select name="country">
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
		<textarea id="form_newuser_comments" name="comments">${kwargs.get('comments','')}</textarea>
	</p>
</%buttons:singlepage>



<div class="e2l-controls">
	<input value="Create Account" type="submit" class="save">
</div>

</form>
	
