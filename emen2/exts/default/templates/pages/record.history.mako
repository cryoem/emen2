<%inherit file="/pages/record" />

<%namespace name="buttons"  file="/buttons"  /> 

<%block name="js_ready">
	${parent.js_ready()}
	$("#comments").CommentsControl({
		name: ${rec.name}
	})
</%block>

<div id="comments">Loading...</div>

