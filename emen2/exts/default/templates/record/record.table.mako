<%inherit file="/record/record" />
<%block name="css_inline">
	${parent.css_inline()}
	#content {
		width: auto;
		padding: 0px;
	}
</%block>

${table}
