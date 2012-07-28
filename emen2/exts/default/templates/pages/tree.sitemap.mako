<%! import jsonrpc.jsonutil  %>
<%inherit file="/page" />
<%namespace name="pages_tree" file="/pages/tree"  /> 

<%block name="js_ready">
    ${parent.js_ready()}
    $('.e2-tree').TreeControl({'attach':true});    
</%block>

<h1>Sitemap</h1>

<div id="sitemap">
    ${pages_tree.traverse(tree, root, recnames, recurse, mode=mode, keytype=keytype, expandable=expandable, id=id, collapsed=collapsed)}
</div>