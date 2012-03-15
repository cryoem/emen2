<%! import jsonrpc.jsonutil %>
<%namespace name="forms"  file="/forms"  /> 

<%def name="newtabs(tabs, cls='')">
	<%
		tabs = tabs or {}
		if not hasattr(tabs, 'items'):
			tabs = {'main':tabs}
		active = getattr(tabs, 'active', 'main')
		uris = getattr(tabs, 'uris', dict())
	%>
	<div class="e2-tab ${cls}">
		<ul class="e2l-cf">
			% for k,v in tabs.items():
				% if k == active:
					<li class="e2-tab-active"><a href="${uris.get(k,REQUEST_LOCATION)}">${v}</a></li>
				% else:
					<li><a href="${uris.get(k,REQUEST_LOCATION)}">${v}</a></li>				
				% endif
			% endfor
		</ul>
	</div>		
</%def>



<%def name="singlepage(label, cls='e2-tab-switcher')">
	<div class="e2-tab e2-tab-switcher">
		<ul class="e2l-cf">
			<li class="e2-tab-active"><span>${label}</span></li>
		</ul>
		<div class="e2-tab-active e2l-cf" id="${cls}-main">${caller.body()}</div>
	</div>			
</%def>


## Some simple helpers

<%def name="image(name, alt='', cls='')">
	<img src="${EMEN2WEBROOT}/static-${VERSION}/images/${name}" class="${cls}" alt="${alt}" />
</%def>


<%def name="spinner(show=True, cls='')">
	<img src="${EMEN2WEBROOT}/static/images/spinner.gif" class="e2l-spinner ${forms.iffalse(show, 'e2l-hide')} ${cls}" alt="Loading" />
</%def>


<%def name="caret(state='down')">
	% if state == 'up':
		<img src="${EMEN2WEBROOT}/static/images/caret.up.png" alt="^" />
	% elif state == 'down':
		<img src="${EMEN2WEBROOT}/static/images/caret.down.png" alt="^" />	
	% endif
</%def>


<%def name="save(label='Save')">
	<div class="e2l-controls">
		<input value="${label}" type="submit">
	</div>
</%def>


<%def name="editicon()">
	<img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" />
</%def>


<%def name="tocache(item)">
	<%
	name = item.name
	if name == None:
		name = 'None'
	%>
	emen2.caches[${jsonrpc.jsonutil.encode(item.keytype)}][${jsonrpc.jsonutil.encode(name)}] = ${jsonrpc.jsonutil.encode(item)};
</%def>


## Info Box

<%def name="infobox(item=None, title=None, body=None, time=None, link=None, autolink=False)">
	<%
	item = item or dict()
	
	if autolink:
		link = '%s/%s/%s/'%(EMEN2WEBROOT, item.get('keytype'), item.get('name'))

	src = "%s/static/images/gears.png"%EMEN2WEBROOT
	title = title or item.get('desc_short') or item.get('name')
	body = ''
		
	if item.get('keytype') == 'user':
		src = "%s/static/images/nophoto.png"%EMEN2WEBROOT
		title = item.get('displayname') or item.get('name')
		body = body or item.get('email')
		photo = item.get('userrec', dict()).get('person_photo')
		if photo:
			src = "%s/download/%s/?size=thumb"%(EMEN2WEBROOT, photo)
	elif item.get('keytype') == 'group':
		src = "%s/static/images/group.png"%EMEN2WEBROOT
		title = item.get('displayname')
		body = body or '%s members'%sum([len(i) for i in item.get('permissions',[])])
	elif item.get('keytype') == 'paramdef':
		body = '%s (%s)'%(item.name, item.vartype)

	%>
	<div class="e2-infobox" data-name="${item.get('name')}" data-keytype="${item.get('keytype')}">

		% if link:
			<a href="${link}"><img alt="Photo" class="e2l-thumbnail" src="${src}" /></a>
		% else:
			<img alt="Photo" class="e2l-thumbnail" src="${src}" />
		% endif

		<div>
			<h4>
				% if link:
					<a href="${link}">
				% endif

				${title}

				% if time:
					@ <time class="e2-localize" datetime="${time}">${time}</time>
				% endif	

				% if link:
					</a>
				% endif
			</h4>
			<div class="e2l-small">${body}</div>
		</div>
	</div>
</%def>
