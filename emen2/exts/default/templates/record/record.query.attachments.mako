<%inherit file="/record/record" />
<%namespace name="query_files" file="/pages/query.files"  /> 

<%block name="js_ready">
    ${parent.js_ready()}
    $("#e2-download").DownloadControl({});
</%block>

<%
filesize = sum([(bdo.get('filesize') or 0) for bdo in bdos])
%>


<form id="e2-download" method="post" action="${EMEN2WEBROOT}/download/">
    <h1>
        Attachments in child records &mdash; <span class="e2-download-filecount">${len(bdos)}</span> files, <span class="e2-download-filesize">${filesize}</span>
        <ul class="e2l-actions">
            <li><input type="submit" value="Download selected attachments" /></li>
        </ul>
    </h1>

    ${query_files.download(bdos, users=users, recnames=recnames)}    

</form>
