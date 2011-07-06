<%inherit file="/page" />

<form method="post" action="${EMEN2WEBROOT}/recorddefs/name/">
<h1>

	${title}

	<span class="label search">
		<input value="${q or ''}" name="q" type="text" size="8" />
		<input type="submit" value="Search" />
	</span>

	% if create:
		<span class="label"><a href="${EMEN2WEBROOT}/recorddef/root/new/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> New</a></span>
	% endif

</h1>
</form>


<script type="text/javascript">
	$(document).ready(function() {
		$('#sitemap').RelationshipControl({
			'attach': true,
			'keytype': 'recorddef'
		});
	});	
</script>

<div id="sitemap" class="clearfix">
${childmap}
</div>
