<%inherit file="/page" />

<h1>Welcome to ${EMEN2DBNAME}</h1>

<p>You are currently an anonymous user. <a href="${EMEN2WEBROOT}/auth/login/">Login here</a></p>

<ul>
	% for i in projs:
		<li><a href="${EMEN2WEBROOT}/record/${i}/">${recnames.get(i,"Record: %s"%i)}</a></li>
	% endfor
</ul>
