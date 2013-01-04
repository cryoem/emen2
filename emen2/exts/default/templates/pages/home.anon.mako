<%inherit file="/page" />

<h1>Welcome to ${TITLE}</h1>

<p>You are currently an anonymous user. <a href="${ctxt.root}/auth/login/">Login here</a></p>

<ul>
    % for i in projs:
        <li><a href="${ctxt.root}/record/${i}/">${recnames.get(i,"Record: %s"%i)}</a></li>
    % endfor
</ul>
