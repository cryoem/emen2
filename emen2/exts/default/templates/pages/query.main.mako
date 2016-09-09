<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />
<%namespace name="query"  file="/pages/query"  />

<h1>Query</h1>

<form method="post" action="${ctxt.root}/query">
    <ul class="e2l-nonlist e2-query-base e2-query-constraints"> 
        <li class="e2-query-constraint"> 
            <strong class="e2-query-label">Protocol:</strong> 
            <input type="hidden" name="param" value="rectype" /> 
            <input type="hidden" name="cmp" value="is" /> 
            <input type="text" name="value" id="e2-query-find-protocol" placeholder="Select protocol" /> 
            <img class="e2-query-find" data-keytype="recorddef" data-target="e2-query-find-protocol" src="" /> 
            <input type="checkbox" name="recurse_v" id="e2-query-id-rectype"/><label for="e2-query-id-rectype">Include child protocols</label> 
        </li> 
        <li class="e2-query-constraint"> 
            <strong class="e2-query-label">Creator:</strong> 
            <input type="hidden" name="param" value="creator" /> 
            <input type="hidden" name="cmp" value="is" /> 
            <input type="text" name="value" id="e2-query-find-user" placeholder="Select user" /> 
            <img class="e2-query-find" data-keytype="user" data-target="e2-query-find-user" src="" /> 
        </li> 
        <li class="e2-query-constraint"> 
            <strong class="e2-query-label">Child of:</strong> 
            <input type="hidden" name="param" value="children" /> 
            <input type="hidden" name="cmp" value="name" /> 
            <input type="text" name="value" id="e2-query-find-record" placeholder="Select record"/> 
            <img class="e2-query-tree" data-keytype="record" data-target="e2-query-find-record" src="" /> 
            <input type="checkbox" name="recurse_v" id="e2-query-paramid-children" /><label for="e2-query-paramid-children">Recursive</label> 
        </li> 
        <li> 
            <strong class="e2-query-label">Created:</strong> 
            <span class="e2-query-constraint"> 
                <input type="hidden" name="param" value="creationtime" /> 
                <input type="hidden" name="cmp" value=">=" /> 
                <input type="text" name="value" placeholder="Start date" /> 
                </span>&nbsp;&nbsp;&nbsp;to&nbsp;&nbsp;&nbsp;<span class="e2-query-constraint"> 
                <input type="hidden" name="param" value="creationtime" /> 
                <input type="hidden" name="cmp" value="<=" /> 
                <input type="text" name="value" placeholder="end date" /> 
            </span> 
        </li> 
    </ul> 

    <ul class="e2l-nonlist e2-query-param e2-query-constraints"></ul>

    <ul class="e2l-controls">
        <li><input type="submit" value="Query" /><li>
    </ul>
</form>

<br /><br /><br /><br />


${query.table(q)}

