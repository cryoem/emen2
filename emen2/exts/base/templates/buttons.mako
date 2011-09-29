<%namespace name="forms"  file="/forms"  /> 

##########################################################

<%def name="buttons(tabs)">
	<ul class="e2l-tab-buttons e2l-cf" id="${tabs.getid_buttons()}" data-tabgroup="${tabs.getclassname()}">
	% for i in tabs.order:
		<li class="${tabs.getclass_button(i)}" id="${tabs.getid_button(i)}" data-tabgroup="${tabs.getclassname()}" ${tabs.getjs_button(i)} >${tabs.getcontent_button(i)}</li>
	% endfor
	</ul>
</%def>

##########################################################

<%def name="pages(tabs)">
	<div class="e2l-tab-pages e2l-cf" id="${tabs.getid_pages()}" data-tabgroup="${tabs.getclassname()}">
		% for i in tabs.order:
			<div class="${tabs.getclass_page(i)}" id="${tabs.getid_page(i)}" data-tabgroup="${tabs.getclassname()}">
				${tabs.getcontent_page(i)}
			</div>
		% endfor
	</div>
</%def>		

##########################################################

<%def name="pagewrap(tabs,name)">

	<div class="${tabs.getclass_page(name)}" id="${tabs.getid_page(name)}" data-tabgroup="${tabs.getclassname()}">
		${caller.body()}
	</div>

</%def>

##########################################################


<%def name="pageswrap(tabs)">

	<div class="e2l-tab-pages" id="${tabs.getid_pages()}" data-tabgroup="${tabs.getclassname()}">
		${caller.body()}
	</div>
	
</%def>


## Simple title button

<%def name="titlebutton(title)">
	<ul data-tabgroup="main" class="e2l-tab-buttons e2l-cf">
		<li data-tabgroup="main" class="e2l-tab-button e2l-tab-active">${title}</li>
	</ul>
</%def>


## Some simple form controls

<%def name="spinner(show=True)">
	<img src="${EMEN2WEBROOT}/static/images/spinner.gif" class="e2l-spinner ${forms.iffalse(show, 'e2l-hide')}" alt="Loading" />
</%def>

<%def name="caret()">
	<img src="${EMEN2WEBROOT}/static/images/caret_small.png" alt="^" />
</%def>


<%def name="save(label='Save')">
	<div class="e2l-controls">
		<input value="${label}" type="submit" class="e2l-save">
	</div>
</%def>


## Info Box

<%def name="infobox(item=None, title=None, body=None, time=None, link=None, autolink=False)">
	<%
	item = item or dict()
	
	if autolink:
		link = '%s/%s/%s/'%(EMEN2WEBROOT, item.get('keytype'), item.get('name'))
		
	if item.get('keytype') == 'user':
		src = "%s/static/images/nophoto.png"%EMEN2WEBROOT
		title = title or item.get('displayname') or item.get('name')
		body = body or item.get('email')
		photo = item.get('userrec', dict()).get('person_photo')
		if photo:
			src = "%s/download/%s/?size=thumb"%(EMEN2WEBROOT, photo)
	elif item.get('keytype') == 'group':
		src = "%s/static/images/group.png"%EMEN2WEBROOT
		title = title or item.get('displayname') or item.get('name')
		body = body or '%s members'%sum([len(i) for i in item.get('permissions',[])])
	else:
		src = "%s/static/images/gears.png"%EMEN2WEBROOT
		title = title or item.get('desc_short') or item.get('name')
		body = body or ''
	%>
	<div class="e2-infobox" data-name="${item.get('name')}" data-keytype="${item.get('keytype')}">

		% if link:
			<a href="${link}"><img alt="Photo" class="e2l-thumbnail" src="${src}" /></a>
		% else:
			<img alt="Photo" class="e2l-thumbnail" src="${src}" />
		% endif

		<h4>
			% if link:
				<a href="${link}">
			% endif

			${title}

			% if time:
				@ ${time}
			% endif	

			% if link:
				</a>
			% endif
		</h4>
		<p class="e2l-small">${body}</p>
	</div>
</%def>



##########################################################

<%def name="all(tabs)">
${buttons(tabs)}
${pages(tabs)}
</%def>

##########################################################

<%def name="singlepage(name=None,label=None)">

<%
import random
import hashlib
from emen2.web.markuputils import HTMLTab
tabs = HTMLTab()
tabs.setclassname(name or hashlib.md5(str(random.random())).hexdigest())
tabs.setlabel("main",label)
tabs.setcontent("main",caller.body)
tabs.check()
%>

${buttons(tabs)}
${pages(tabs)}

</%def>
