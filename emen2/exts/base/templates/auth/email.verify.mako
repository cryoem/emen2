<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

<h1>${title}</h1>

% if errmsg:

	<div class="notify error">${errmsg}</div>

% endif


% if msg:
	
	<div class="notify">
		${msg}
	</div>	

% endif
