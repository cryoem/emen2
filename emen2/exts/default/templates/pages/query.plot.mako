<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />
<%namespace name="query"  file="/pages/query"  />

<%block name="js_ready">
    ${parent.js_ready()}

    ## Recent activity viewer
    var q = ${jsonrpc.jsonutil.encode(q)}; 
    $('#query-plot').PlotControl({
        q:q
    });
    $('#query-control').QueryControl({
        q:q,
        query: function(self, q){
            console.log("new query:", q);
            $("#query-plot").PlotControl('query', q);
        }
    });


</%block>

<h1>Plot</h1>
<div id="query-plot"><div class="e2-plot"></div></div>

<div class="e2l-cf"></div>

<div id="query-control"></div>