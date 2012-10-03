<%namespace name="buttons" file="/buttons"  />
<%inherit file="/page" />

<%def name="login(redirect='')">
    <form action="${EMEN2WEBROOT}/auth/login/" method="post">

        <input type="hidden" name="_redirect" value="${redirect}" />
        <table class="login" cellpadding="0" cellspacing="0">
            <tr>
                <td>Email:</td>
                <td><input tabindex="1" type="text" name="username" value="" autofocus autocomplete="off" /></td>
            </tr>
            <tr>
                <td>Password:</td>
                <td><input tabindex="2" type="password" name="password" /></td>
            </tr>
            <tr>
                <td />
                <td><button type="submit" onclick="emen2.ui.buttonfeedback(this)">Login</button> <span class="e2l-small">(<a href="${EMEN2WEBROOT}/auth/password/reset/">Forgot password?</a>)</span></td>
            </tr>
        </table>
    </form>

</%def>

<h1>Login</h1>

${login()}