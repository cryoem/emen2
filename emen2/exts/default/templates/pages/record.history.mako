<%inherit file="/pages/record" />

<%namespace name="buttons"  file="/buttons"  /> 

<%block name="javascript_ready">
	${parent.javascript_ready()}
	$("#comments").CommentsControl({
		name: ${rec.name}
	})
</%block>

<div id="comments">Loading...</div>

