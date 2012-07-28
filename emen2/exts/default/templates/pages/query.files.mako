<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />

<%
filesize = sum([(bdo.get('filesize') or 0) for bdo in bdos])
%>

<%block name="js_ready">
    ${parent.js_ready()}
    $("#e2-download").DownloadControl({});
</%block>



<%def name="download(bdos, users=None, recnames=None)">
    <%
    recnames = recnames or {}
    users = users or []
    users_d = dict((i.name, i) for i in users)    
    %>

    <table class="e2l-shaded" cellpadding="0" cellspacing="0">
        <thead>
            <tr>
                <th><input type="checkbox" checked="checked" class="e2-download-allbids" value="" /></th>
                <th>Filename</th>
                <th>Size</th>
                <th>Record</th>
                <th>Creator</th>
                <th>Created</th>
            </tr>
        </thead>
    
        <tbody>
        % for bdo in bdos:
            <tr>
                <td><input type="checkbox" checked="checked" name="bids" value="${bdo.name}" data-filesize="${bdo.get('filesize',0)}" /></td>
                <td>
                    <%
                    ## Grumble...
                    fn = bdo.filename
                    try:
                        if isinstance(fn, str):
                            fn = bdo.filename.decode('utf-8')
                    except:
                        fn = bdo.name
                    %>
                    <a href="${EMEN2WEBROOT}/download/${bdo.name}/${fn}">
                        <img class="e2l-thumbnail" src="${EMEN2WEBROOT}/download/${bdo.name}/thumb.jpg?size=thumb" alt="" /> 
                        ${fn}
                    </a>
                </td>
                <td class="e2-download-filesizes" data-filesize="${bdo.get('filesize',0)}">${bdo.get('filesize',0)}</td>
                <td><a href="${EMEN2WEBROOT}/record/${bdo.record}/">${recnames.get(bdo.record)}</a></td>
                <td><a href="${EMEN2WEBROOT}/user/${bdo.get('creator')}/">${users_d.get(bdo.get('creator'), dict()).get('displayname')}</a></td>
                <td><time class="e2-localize" datetime="${bdo.get('creationtime')}">${bdo.get('creationtime')}</time></td>
            </tr>
        % endfor
        </tbody>

    </table>
</%def>


<form id="e2-download" method="post" action="${EMEN2WEBROOT}/download/">
    <h1>
        <span class="e2-download-filecount">${len(bdos)}</span> files, <span class="e2-download-filesize">${filesize}</span>
        <ul class="e2l-actions">
            <li><input type="submit" value="Download selected attachments" /></li>
        </ul>
    </h1>

    ${download(bdos)}    
</form>
