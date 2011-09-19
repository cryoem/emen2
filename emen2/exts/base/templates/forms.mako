<%!
checked = 'checked="checked"'
selected = 'selected="selected"'

def _istrue(exp, value):
	if exp:
		return value
	return ''
%>


<%def name="istrue(exp, value)">${_istrue(exp, value)}</%def>

<%def name="ischecked(exp)">${_istrue(exp, checked)}</%def>

<%def name="isselected(exp)">${_istrue(exp, selected)}</%def>

<%def name="input(name, value, type='text', chk=False)">
	% if type=='text':
		<input type="${type}" name="${name}" value="${value}" />
	% elif type=='checkbox':
		<input type="${type}" name="${name}" value="${value}" ${_istrue(chk, checked)}/>	
	% elif type=='radio':
		<input type="${type}" name="${name}" value="${value}" ${_istrue(chk, checked)}/>	
	% endif
</%def>

<%def name="select(name, value, values=None)">
	<% values = values or [] %>
</%def>


<%def name="input_rec(name, rec, type='text', chk=False)">
	${input(name, rec.get(name,''), type=type, chk=chk)}
</%def>