<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" version="-//W3C//DTD XHTML 1.1//EN" xml:lang="en">

## Named blocks:
##	title
## 	javascript_include
##	javascript_inline
##	javascript_onload
##	stylesheet_include
##	stylesheet_inline

<%def name="alert()"></%def>
<%def name="precontent()"></%def>

<head>

	<meta http-equiv="Content-type" content="text/html; charset=utf-8" />
	<meta http-equiv="Content-Language" content="en-us" />

	<title>
		<%block name="title">
			${EMEN2DBNAME}: ${context.get('title','No Title')}
		</%block>
	</title>

	<%block name="javascript_include">
		<script src="${EMEN2WEBROOT}/tmpl-${VERSION}/js/settings.js/" type="text/javascript"></script>
		<script src="${EMEN2WEBROOT}/static-${VERSION}/js/jquery/jquery.js" type="text/javascript"></script>
		<script src="${EMEN2WEBROOT}/static-${VERSION}/js/jquery/jquery-ui.js" type="text/javascript"></script>
		<script src="${EMEN2WEBROOT}/static-${VERSION}/js/jquery/jquery.json.js" type="text/javascript"></script>
		<script src="${EMEN2WEBROOT}/static-${VERSION}/js/jquery/jquery.timeago.js" type="text/javascript"></script>
		<script src="${EMEN2WEBROOT}/static-${VERSION}/js/jquery/jquery.jsonrpc.js" type="text/javascript"></script>
		<script src="${EMEN2WEBROOT}/static-${VERSION}/js/comments.js" type="text/javascript"></script>
		<script src="${EMEN2WEBROOT}/static-${VERSION}/js/edit.js" type="text/javascript"></script>
		<script src="${EMEN2WEBROOT}/static-${VERSION}/js/editdefs.js" type="text/javascript"></script>
		<script src="${EMEN2WEBROOT}/static-${VERSION}/js/file.js" type="text/javascript"></script>
		<script src="${EMEN2WEBROOT}/static-${VERSION}/js/find.js" type="text/javascript"></script>
		<script src="${EMEN2WEBROOT}/static-${VERSION}/js/permission.js" type="text/javascript"></script>
		<script src="${EMEN2WEBROOT}/static-${VERSION}/js/relationship.js" type="text/javascript"></script>
		<script src="${EMEN2WEBROOT}/static-${VERSION}/js/table.js" type="text/javascript"></script>
		<script src="${EMEN2WEBROOT}/static-${VERSION}/js/tile.js" type="text/javascript"></script>
		<script src="${EMEN2WEBROOT}/static-${VERSION}/js/calendar.js" type="text/javascript"></script>
		<script src="${EMEN2WEBROOT}/static-${VERSION}/js/util.js" type="text/javascript"></script>	
	</%block>

	<script type="text/javascript">
		// Global cache
		var caches = {};
		caches['user'] = {};
		caches['group'] = {};
		caches['record'] = {};
		caches['paramdef'] = {};
		caches['recorddef'] = {};
		caches['children'] = {};
		caches['parents'] = {};
		caches['displaynames'] = {};
		caches['groupnames'] = {};
		caches['recnames'] = {};	
		<%block name="javascript_inline" />
		$(document).ready(function() {
			<%block name="javascript_ready" />
		});		
	</script>

	<%block name="stylesheet_include">
		<link rel="StyleSheet" href="${EMEN2WEBROOT}/static-${VERSION}/css/custom-theme/jquery-ui-1.8.2.custom.css" type="text/css" />
		<link rel="StyleSheet" href="${EMEN2WEBROOT}/static-${VERSION}/css/base.css" type="text/css" />
		<link rel="StyleSheet" href="${EMEN2WEBROOT}/static-${VERSION}/css/style.css" type="text/css" />
		<link rel="StyleSheet" href="${EMEN2WEBROOT}/static-${VERSION}/css/boxer.css" type="text/css" />
		<link rel="StyleSheet" href="${EMEN2WEBROOT}/tmpl-${VERSION}/css/map.css/" type="text/css" />
	</%block>
	
	<style type="text/css">
		<%block name="stylesheet_inline" />
	</style>
	
</head>

<body>

${next.body()}

</body></html>
