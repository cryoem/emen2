<%inherit file="/page" />



<form method="post" action="${EMEN2WEBROOT}/paramdefs/name/">
<h1>

	${title}

	<span class="label search">
		<input value="${q or ''}" name="q" type="text" size="8" />
		<input type="submit" value="Search" />
	</span>

	% if create:
		<span class="label"><a href="${EMEN2WEBROOT}/paramdef/root/new/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> New</a></span>
	% endif
</h1>
</form>

<script type="text/javascript">
	$(document).ready(function() {
		$('#sitemap').RelationshipControl({
			'attach':true,
			'keytype':'paramdef'
		});
	});	
</script>

<div id="sitemap" class="e2l-clearfix">
${childmap}
</div>