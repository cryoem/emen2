<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />
<%namespace name="query"  file="/pages/query"  />

<%block name="css_inline">
	${parent.css_inline()}
	#content {
		width: auto;
		padding: 0px;
	}
</%block>


${query.table(q)}

