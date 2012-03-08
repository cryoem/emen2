<%! import jsonrpc.jsonutil %>
<%namespace name="buttons" file="/buttons"  />
<%namespace name="forms" file="/forms"  /> 

## JavaScript for client-side initial validation and error
## reporting for New User form

<%def name="newuser_js_ready(minimum=6)">
	$('input[name=password]').change(function(){
		if ($(this).val().length < 6) {
			this.setCustomValidity('Minimum password length is 6');
		} else {
			this.setCustomValidity('');
		}
	});
	
	$('input[name=user\\.password]').change(function() {
		var op1 = $(this).val();
		var op2 = $('input[name=password]').val();
		var msg = '';
		if (op1 != op2) {
			msg = 'Passwords did not match';
		} else if (op1.length < 6 || op2.length < 6) {
			msg = 'Minimum password length is 6';
		}
		$('#e2-newuser-passwordmatch').html(msg || 'Ok');
		this.setCustomValidity(msg);
	});	
</%def>


<%def name="newuser(user)">
	<table class="e2l-kv">	
		<tbody>		
			<tr>
				<td>Email:</td>
				<td><input name="user.email" type="email" value="${user.get('email','')}" required autocomplete="off" /></td>
			</tr>

			<tr>
				<td>Password:</td>
				<td>
					<input name="password" type="password" required />
					<span class="e2l-small">Minimum 6 characters</span>
				</td>
			</tr>

			<tr>
				<td>Confirm Password:</td>
				<td>
					<input name="user.password" type="password" required />
					<span id="e2-newuser-passwordmatch" class="e2l-small"></span>					
				</td>
			</tr>
		</tbody>
	</table>
</%def>




<%def name="profile(user=None, userrec=None, edit=False, prefix='userrec.')">
	% if edit:
	
		<table  class="e2l-kv">	
			<tbody>					
				<tr>
					<td>First Name:</td>
					<td><input name="${prefix}name_first" type="text" value="${userrec.get('name_first','')}" required /></td>
				</tr>
				<tr>
					<td>Middle Name:</td>
					<td><input name="${prefix}name_middle" type="text" value="${userrec.get('name_middle','')}" /></td>
				</tr>
				<tr>
					<td>Last Name:</td>
					<td><input name="${prefix}name_last" type="text" value="${userrec.get('name_last','')}" required /></td>
				</tr>
				<tr>
					<td>Institution:</td>
					<td><input name="${prefix}institution" type="text" value="${userrec.get('institution','')}" required /></td>
				</tr>
				<tr>
					<td>Department:</td>
					<td><input name="${prefix}department" type="text" value="${userrec.get('department','')}" required /></td>
				</tr>
				<tr>
					<td>Street Address:</td>
					<td><input name="${prefix}address_street" type="text" value="${userrec.get('address_street','')}" required /></td>
				</tr>
				<tr>
					<td>City:</td>
					<td><input name="${prefix}address_city" type="text" value="${userrec.get('address_city','')}" required /></td>
				</tr>
				<tr>
					<td>State:</td>
					<td><input name="${prefix}address_state" type="text" value="${userrec.get('address_state','')}" required /></td>
				</tr>
				<tr>
					<td>Zipcode:</td>
					<td><input name="${prefix}address_zipcode" type="text" value="${userrec.get('address_zipcode','')}" required /></td>
				</tr>
				<tr>
					<td>Country:</td>
					<td>			
						<select name="${prefix}country" required />
							${forms.countries()}
						</select>
						<script type="text/javascript">
							var country = ${jsonrpc.jsonutil.encode(userrec.get('country','United States'))};
							$('select[name=userrec\\.country]').val(country);
						</script>

					</td>
				</tr>
				<tr>
					<td>Phone:</td>
					<td><input name="${prefix}phone_voice" type="text" value="${userrec.get('phone_voice','')}"></td>
				</tr>
				<tr>
					<td>Fax:</td>
					<td><input name="${prefix}phone_fax" type="text" value="${userrec.get('phone_fax','')}"></td>
				</tr>
				<tr>
					<td>Web page:</td>
					<td><input name="${prefix}website" type="text" value="${userrec.get('website','')}"></td>
				</tr>
			</tbody>
		</table>

	% else:
	
		% if user.userrec.get('person_photo'):
			<% pf_url = EMEN2WEBROOT + "/download/" + user.userrec.get('person_photo') + "/" + user.name %>
			<a class="e2l-float-right" href="${pf_url}"><img src="${pf_url}?size=small" class="e2l-thumbnail-mainprofile" alt="profile photo" /></a>
		% endif
	
		<table>
			<tbody>
				<tr>
					<td>Department:</td>
					<td>${userrec.get('department', '')}</td>
				</tr>
				<tr>
					<td>Institution:</td>
					<td>${userrec.get('institution', '')}</td>
				</tr>
				<tr>
					<td>Address:</td>
					<td>
						${userrec.get('address_street', '')}<br />
						${userrec.get('address_street2', '')}<br />
						${userrec.get('address_city', '')},	${userrec.get('address_state', '')} ${userrec.get('address_zipcode', '')}<br />
						${userrec.get('country', '')}
					</td>
				</tr>
				<tr>
					<td>Email:</td>
					<td><a href="mailto:${user.email}">${user.email}</a></td>
				</tr>
				<tr>
					<td>Phone:</td>
					<td>${user.get('phone_voice', '')}</td>
				</tr>
				<tr>
					<td>Web:</td>
					<td>${userrec.get('website', '')}</td>
				</tr>
			</tbody>
		</table>

			
	% endif

</%def>


