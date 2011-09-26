<%inherit file="/page" />

<%block name="js_ready">
	${parent.js_ready()}
	$('#sitemap').RelationshipControl({
		'attach': true,
		'keytype': 'recorddef'
	});
</%block>


<form method="post" action="${EMEN2WEBROOT}/recorddefs/name/">
<h1>
	${title}
	<span class="e2l-label">
		<input value="${q or ''}" name="q" type="text" size="8" />
		<input type="submit" value="Search" />
	</span>
	% if create:
		<span class="e2l-label"><a href="${EMEN2WEBROOT}/recorddef/root/new/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> New</a></span>
	% endif
</h1>
</form>

<div id="sitemap" class="e2l-clearfix">
${childmap}
</div>
