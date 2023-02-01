<!DOCTYPE HTML>
<html xmlns="http://www.w3.org/1999/xhtml">

## <?xml version="1.0" encoding="utf-8"?>
## <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
## <html xmlns="http://www.w3.org/1999/xhtml" version="-//W3C//DTD XHTML 1.1//EN" xml:lang="en">

## Named blocks:
## => title
## => js_include
## => js_inline
## => js_ready
## => css_include
## => css_inline

<head>

    <%block name="meta">
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    </%block>

    <title>
        <%block name="title">
            ${TITLE}: ${ctxt.title}
        </%block>
    </title>

    <%block name="css_include">
        <link rel="StyleSheet" type="text/css" href="${ROOT}/static-${ctxt.version}/css/custom-theme/jquery-ui-1.8.16.custom.css" />
        <link rel="StyleSheet" type="text/css" href="${ROOT}/tmpl-${ctxt.version}/css/base.css" />
        <link rel="StyleSheet" type="text/css" href="${ROOT}/tmpl-${ctxt.version}/css/site.css" />
    </%block>
    
    <style type="text/css">
        <%block name="css_inline" />
    </style>

    <%block name="js_include">
        ## EMEN2 Settings
        <script type="text/javascript" src="${ROOT}/tmpl-${ctxt.version}/js/settings.js"></script>

        ## jQuery, jQuery-UI, and plugins
        <script type="text/javascript" src="${ROOT}/static-${ctxt.version}/js/jquery/jquery.js"></script>
        <script type="text/javascript" src="${ROOT}/static-${ctxt.version}/js/jquery/jquery-ui.js"></script>
        <script type="text/javascript" src="${ROOT}/static-${ctxt.version}/js/jquery/jquery.json.js"></script>
        <script type="text/javascript" src="${ROOT}/static-${ctxt.version}/js/jquery/jquery.jsonrpc.js"></script>
        <script type="text/javascript" src="${ROOT}/static-${ctxt.version}/js/jquery/jquery.ui.timepicker-addon.js"></script>
        <script type="text/javascript" src="${ROOT}/static-${ctxt.version}/js/jquery/jquery.timeago.js"></script>
        <script type="text/javascript" src="${ROOT}/static-${ctxt.version}/js/jquery/jquery.localize.js"></script>

        ## Base EMEN2 widgets
        <script type="text/javascript" src="${ROOT}/tmpl-${ctxt.version}/js/util.js"></script>
        <script type="text/javascript" src="${ROOT}/tmpl-${ctxt.version}/js/edit.js"></script>
        <script type="text/javascript" src="${ROOT}/tmpl-${ctxt.version}/js/attachments.js"></script>
        <script type="text/javascript" src="${ROOT}/tmpl-${ctxt.version}/js/find.js"></script>
        <script type="text/javascript" src="${ROOT}/tmpl-${ctxt.version}/js/permissions.js"></script>
        <script type="text/javascript" src="${ROOT}/tmpl-${ctxt.version}/js/relationships.js"></script>
        <script type="text/javascript" src="${ROOT}/tmpl-${ctxt.version}/js/query.js"></script>
        <script type="text/javascript" src="${ROOT}/tmpl-${ctxt.version}/js/tile.js"></script>
        <script type="text/javascript" src="${ROOT}/tmpl-${ctxt.version}/js/plot.js"></script>  

        ## D3 visualization library
        <script type="text/javascript" src="${ROOT}/static-${ctxt.version}/js/d3/d3.js"></script>
        <script type="text/javascript" src="${ROOT}/static-${ctxt.version}/js/d3/d3.time.js"></script>
        
        ## Internet Explorer...
        ## <script type="text/javascript" src="https://getfirebug.com/firebug-lite.js"></script>
        <!--[if lt IE 9]>
            <script src="http://ie7-js.googlecode.com/svn/version/2.1(beta4)/IE9.js"></script>
        <![endif]-->            

    </%block>

    <script type="text/javascript">    
        <%block name="js_inline" />        
        $(document).ready(function() {
            $('time.e2-localize').localize({format: 'yyyy/mm/dd HH:MM'});
            $('time.e2-timeago').timeago();
            <%block name="js_ready" />
        });                
    </script>

</head>

<body>

${next.body()}

</body></html>
