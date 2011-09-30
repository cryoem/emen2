<%inherit file="/page" />
<%namespace name="login" file="/auth/login"  /> 

<h1>${error}</h1>

${login.login(location=location)}
