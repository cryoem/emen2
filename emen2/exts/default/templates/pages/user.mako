<%! import jsonrpc.jsonutil %>
<%namespace name="buttons" file="/buttons"  />

## JavaScript for client-side initial validation and error
## reporting for New User form

<%def name="newuser_js_ready(minimum=6)">
	var invalid = ${jsonrpc.jsonutil.encode(invalid)};
	var country = ${jsonrpc.jsonutil.encode(kwargs.get('country','United States'))};
	$('select[name=country]').val(country);
	$.each(invalid, function() {
		var inp = $('input[name='+this+']')
		inp.addClass("e2l-error");
		inp.after(' <span class="e2l-small">Required</span>');
	})

	$('input[name=op1]').change(function(){
		if ($(this).val().length < 6) {
			this.setCustomValidity('Minimum password length is 6');
		} else {
			this.setCustomValidity('');
		}
	});
	
	$('input[name=op2]').change(function() {
		var op1 = $(this).val();
		var op2 = $('input[name=op1]').val();
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


## Required fields for New User form

<%def name="newuser_required(kwargs)">
	<%buttons:singlepage label='Account Details'>
		<table class="e2l-kv">	
			<tbody>		
					
				## <tr>
				## 	<td>Account Name:</td>
				## 	<td>
				## 		<input name="name" type="text" value="${kwargs.get('name','')}">
				## 		<span class="e2l-small">Please use 'firstnamelastname' format</span>
				## 	</td>
				## </tr>
		
				<tr>
					<td>Email:</td>
					<td><input name="email" type="email" value="${kwargs.get('email','')}" required autocomplete="off" /></td>
				</tr>

				<tr>
					<td>Password:</td>
					<td>
						<input name="op1" type="password" required />
						<span class="e2l-small">Minimum 6 characters</span>
					</td>
				</tr>

				<tr>
					<td>Confirm Password:</td>
					<td>
						<input name="op2" type="password" required />
						<span id="e2-newuser-passwordmatch" class="e2l-small"></span>					
					</td>
				</tr>
			</tbody>
		</table>
	</%buttons:singlepage>
</%def>



<%def name="page_title(user, edit)">
	<%
	un = ""
	if user.userrec.get("academic_degrees"):
		un += ", " + ", ".join(user.userrec.get("academic_degrees",[]))
	%>

	${user.displayname}${un}
	## (<a href="${ctxt.reverse('User', name=user.name)}">${user.name}</a>)
	
</%def>



<%def name="page_userrec(user, edit)">

<%
if user.name == 'root':
	return """
		<p>
			The default administrator account (root) only supports basic account details, 
			and does not provide preferences or detailed profile information. You may
			want to <a href="%s">create a non-root user account</a>.
		</p>"""%ctxt.reverse('Users/new')
		
if user.name is None:
	return """<p>This account does not have an extended profile.</p>"""
%>

	<form method="post" action="${ctxt.reverse('User/save', name=user.name)}">

	<table class="e2l-kv">
		<tbody>
		% if edit:
			<tr>
				<td>First name:</td>
				<td><input type="text" name="userrec.name_first" value="${user.userrec.get('name_first','')}" /></td>
			</tr>
			<tr>
				<td>Middle name:</td>
				<td><input type="text" name="userrec.name_middle" value="${user.userrec.get('name_middle','')}" /></td>
			</tr>
			<tr>
				<td>Last name:</td>
				<td><input type="text" name="userrec.name_last" value="${user.userrec.get('name_last','')}" /></td>
			</tr>
		% endif

			<tr>
				<td>Department:</td>
				<td>
				% if edit:
					<input type="text" name="userrec.department" value="${user.userrec.get('department','')}" />
				% else:
					${user.userrec.get("department",'')} 
				% endif				
				</td>
			</tr>

			<tr>
				<td>Institution:</td>
				<td>
				% if edit:
					<input type="text" name="userrec.institution" value="${user.userrec.get('institution','')}" />
				% else:
					${user.userrec.get("institution",'')}
				% endif
				</td>
			</tr>
			
			<tr>
				<td>Address:</td>
				<td>
					% if edit:
						<input type="text" name="userrec.address_street" value="${user.userrec.get('address_street','')}" />
					% else:
						${user.userrec.get("address_street")}			
					% endif
					<br />

				% if edit:
					<input type="text" name="userrec.address_street2" value="${user.userrec.get('address_street2','')}" />
				% else:
					${user.userrec.get("address_street2")}
				% endif
				<br />

				% if edit:
					<input type="text" name="userrec.address_city" value="${user.userrec.get('address_city','')}" /> <span class="e2l-small">(City)</span><br />
					<input type="text" name="userrec.address_state" value="${user.userrec.get('address_state','')}" /> <span class="e2l-small">(State)</span><br />
					<input type="text" name="userrec.address_zipcode" value="${user.userrec.get('address_zipcode','')}" /> <span class="e2l-small">(Zip)</span><br />
					<input type="text" name="userrec.country" value="${user.userrec.get('country','')}" /> <span class="e2l-small">(Country)</span>
				% else:
					${user.userrec.get("address_city",'')} ${user.userrec.get("address_state",'')}, ${user.userrec.get("address_zipcode",'')} ${user.userrec.get("country",'')}			
				% endif
				</td>
			</tr>
	
			<tr>
				<td>Email:</td>
				<td>
				<a href="mailto:${user.email}">${user.email}</a>
				% if edit:
					&nbsp;&nbsp;&nbsp;<span class="e2l-small">(Set email below)</span>
				% endif
			</tr>

			<tr>
				<td>Phone:</td>
				<td>
				% if edit:
					<input type="text" name="userrec.phone_voice" value="${user.userrec.get('phone_voice','')}" />			
				% else:
					${user.userrec.get("phone_voice",'')}
				% endif
				</td>
			</tr>
			
			<tr>
				<td>Web:</td>
				<td>
				% if edit:
					<input type="text" name="userrec.uri" value="${user.userrec.get('uri','')}" />
				% else:
					${user.userrec.get('uri','')}		
				% endif
				</td>
			</tr>

		</tbody>
	</table>

	% if edit:
		${buttons.save('Save profile')}
	% endif	

	</form>

</%def>




<%def name="page_email(user, edit)">
	<form method="post" action="${EMEN2WEBROOT}/auth/email/change/">
	
	<input type="hidden" name="name" value="${user.name or ''}" />

	<table class="e2l-kv">
		<tbody>
			<tr>
				<td>Current password:</td>
				<td><input type="password" name="opw" value="" /> <span class="e2l-small">(required to change email)</span></td>
			</tr>
			</tr>
				<td>New email:</td>
				<td><input type="text" name="email" value="${user.get('email','')}" /></td>
			</tr>
		</tbody>
	</table>

	${buttons.save('Change email')}

	</form>
</%def>



<%def name="page_password(user, edit)">
	<form action="${EMEN2WEBROOT}/auth/password/change/" method="post">

		<input type="hidden" name="location" value="${ctxt.reverse('User/save', name=user.name)}" />
		<input type="hidden" name="name" value="${user.name or ''}" />

		<table class="e2l-kv">
			<tbody>
				<tr>
					<td>Current password:</td>
					<td><input type="password" name="opw" /></td>
				</tr>
				<tr>
					<td>New password:</td>
					<td><input type="password" name="on1" /></td>
				</tr>
				<tr>
					<td>Confirm new password:</td>
					<td><input type="password" name="on2" /></td>
				</tr>
			</tbody>
		</table>

		${buttons.save('Change password')}

	</form>
</%def>



<%def name="page_photo(user, edit)">

<%
if user.name == 'root' or user.name is None:
	return ""
%>


	% if edit:
	
		% if user.userrec.get('person_photo'):
			<% pf_url = EMEN2WEBROOT + "/download/" + user.userrec.get('person_photo') + "/" + user.name %>
			<a href="${pf_url}"><img src="${pf_url}.jpg?size=small" alt="profile photo" /></a>
		% else:
			<div>No Photo</div>
		% endif

		<form method="post" enctype="multipart/form-data" action="${EMEN2WEBROOT}/upload/${user.userrec.get('name')}/">

			<input type="hidden" value="${ctxt.reverse('User/save', name=user.name, action='save')}" name="Location" class="e2l-hide" />
			<input type="hidden" value="person_photo" name="param" />


			<table class="e2l-kv">
				<tbody>
					<tr>
						<td>Select a new photo:</td>
						<td><input type="file" name="filedata"/></td>
					</tr>
				</tbody>
			</table>

			${buttons.save('Upload photo')}

		</form>

	% else:
		% if user.userrec.get('person_photo'):

			<% pf_url = EMEN2WEBROOT + "/download/" + user.userrec.get('person_photo') + "/" + user.name %>
			<a href="${pf_url}"><img src="${pf_url}.jpg?size=small" alt="profile photo" /></a>

		% else:

			<div>No Photo</div>

		% endif
	
	% endif
	
</%def>




<%def name="page_groups(user, edit)">
	## Fix me.
</%def>





<%def name="page_history(user, edit)">
	<p>Created: <time datetime="${user.userrec.get("creationtime")}">${user.userrec.get("creationtime")}</time></p>
	<p>Modified: <time datetime="${user.userrec.get("modifytime")}">${user.userrec.get("modifytime")}</time></p>
</%def>



<%def name="page_status(user, edit)">
	<form method="post" action="${ctxt.reverse('User/save', name=user.name, action='save')}">
		<input type="radio" name="user.disabled" value="0" ${['checked="checked"',''][user.disabled]}> Enabled <br />
		<input type="radio" name="user.disabled" value="1" ${['','checked="checked"'][user.disabled]}> Disabled
		${buttons.save('Set account status')}
	</form>
</%def>



<%def name="page_privacy(user, edit)">
	Who may view your account information:
			
	<form method="post" action="${ctxt.reverse('User/save', name=user.name, action='save')}">
		<input type="radio" name="user.privacy" value="0" ${['checked="checked"','',''][user.privacy]}> Public <br />
		<input type="radio" name="user.privacy" value="1" ${['','checked="checked"',''][user.privacy]}> Only authenticated users<br />
		<input type="radio" name="user.privacy" value="2" ${['','','checked="checked"'][user.privacy]}> Private<br />
		${buttons.save('Set privacy level')}
	</form>		
</%def>






