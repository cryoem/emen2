
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
		<li data-tabgroup="main" id="button_main_main" class="button button_main active">${title()}</li>
	</ul>
</%def>

##########################################################

<%def name="all(tabs)">
${buttons(tabs)}
${pages(tabs)}
</%def>

##########################################################

<%def name="singlepage(name,label)">

<%
from emen2.web.markuputils import HTMLTab
tabs = HTMLTab()
tabs.setclassname(name)
tabs.setlabel("main",label)
tabs.setcontent("main",caller.body)
tabs.check()
%>

${buttons(tabs)}
${pages(tabs)}

</%def>
