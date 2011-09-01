<%inherit file="/page" />

<%def name="login(action,location,user,errmsg,logintext='Login',defaultname='',accounttext='Account Name or Email',registertext='Apply for new account',registerlocation='/users/new/')">

	<script type="text/javascript">
	//<![CDATA[
	$(document).ready(function() {
		$("input[name=name]").focus();
	});
	//]]>
	</script>


	% if logintext:
		<h1>${logintext}</h1>
	% endif

	% if errmsg:
		<div class="notify error">
			${errmsg}
		</div>
	% endif

	<form action="${EMEN2WEBROOT}/auth/login/" method="post">
	    <input type="hidden" name="location" value="${EMEN2WEBROOT}/home/" />
		<table class="login" cellpadding="0" cellspacing="0">
			<tr>
				<td>${accounttext}:</td>
				<td><input tabindex="1" type="text" name="name" value="" /></td>
				<td><a href="${EMEN2WEBROOT}${registerlocation}">${registertext}</a></td>
			</tr>
			<tr>
				<td>Password:</td>
				<td><input tabindex="2" type="password" name="pw" /></td>
				<td><a href="${EMEN2WEBROOT}/auth/password/reset/">Forgot Password?</a></td>
			</tr>
			<tr>
				<td />
				<td><input type="submit" value="Login" /></td>
				<td></td>
			</tr>
		</table>
	</form>

</%def>


${login(action,location,user,errmsg)}