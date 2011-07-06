<%inherit file="/page" />

<%namespace name="login" file="/pages/auth.login"  /> 

<h1>Welcome to ${EMEN2DBNAME}</h1>

${render_banner or ''}

${login.login(action_login, "%s/home/"%EMEN2WEBROOT, user, None, logintext='', defaultname="")}
