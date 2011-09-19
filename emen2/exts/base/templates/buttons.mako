##########################################################

<%def name="buttons(tabs)">
	<ul class="buttons clearfix floatlist" id="${tabs.getid_buttons()}" data-tabgroup="${tabs.getclassname()}">
	% for i in tabs.order:
		<li class="${tabs.getclass_button(i)}" id="${tabs.getid_button(i)}" data-tabgroup="${tabs.getclassname()}" ${tabs.getjs_button(i)} >${tabs.getcontent_button(i)}</li>
	% endfor
	</ul>
</%def>

##########################################################

<%def name="pages(tabs)">
	<div class="pages clearfix" id="${tabs.getid_pages()}" data-tabgroup="${tabs.getclassname()}">
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

	<div class="pages" id="${tabs.getid_pages()}" data-tabgroup="${tabs.getclassname()}">
		${caller.body()}
	</div>
	
</%def>

##########################################################


<%def name="titlebutton(title)">
	<ul data-tabgroup="main" id="buttons_main" class="buttons clearfix floatlist">
		<li data-tabgroup="main" id="button_main_main" class="button button_main active">${title}</li>
	</ul>
</%def>

<%def name="save(label='Save')">
	<div class="e2-layout-controls clearfix">
		${caller.body()}
		<input value="${label}" type="submit" class="big save">
	</div>
</%def>




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
		body = body or sum([len(i) for i in item.get('permissions',[])])
	else:
		src = "%s/static/images/gears.png"%EMEN2WEBROOT
		title = title or item.get('desc_short') or item.get('name')
		body = body or ''
	%>
	<div class="e2-infobox" data-name="${item.get('name')}" data-keytype="${item.get('keytype')}">

		% if link:
			<a href="${link}"><img alt="Photo" class="thumbnail" src="${src}" /></a>
		% else:
			<img alt="Photo" class="thumbnail" src="${src}" />
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
		<p class="small">${caller.body()}${body}</p>
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
