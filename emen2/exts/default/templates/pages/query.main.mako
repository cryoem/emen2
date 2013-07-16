<%! 
import jsonrpc.jsonutil 
import random
%>
<%inherit file="/page" />
<%namespace name="query"  file="/pages/query"  />

<style type="text/css">
h1 { margin-top:20px; }
.e2l-test-constraint img, 
.e2l-test-constraint button {
    margin-right:20px;
}
</style>

<%block name="js_ready">
    ${parent.js_ready()}
    // Intialize the Tab controller
    var tab = $("#e2-tab-query");        
    tab.TabControl({});
</%block>


<form method="post" action="${ctxt.root}/query">

    <div style="border:solid red 2px;">This will be fixed soon! I am in the middle of redesigning the query form.</div>

<div class="e2-tab e2-tab-switcher" id="e2-tab-query">
    <ul class="e2l-cf">
        <li class="e2-tab-active" data-tab="keywords">Keywords</li>
        <li data-tab="extra">Constraints</li>
    </ul>
    
    <div class="e2-tab-active" data-tab="keywords">
        <p>Keywords: <input type="text" name="keywords" /></p>
        <input type="submit" />
    </div>

    <div data-tab="extra">
        <p class="e2l-test-constraint">
            <button>X</button><button>+</button>
            <input type="text" name="param" placeholder="Parameter" /> 
            <img src="${ctxt.root}/static/images/query.png" />
            <select><option value="==">is</option></select> 
            <input type="text" name="value" placeholder="Value" />
        </p>

        <p class="e2l-test-constraint">
            <button>X</button><button>+</button>
            <input type="text" name="param" placeholder="Parameter" /> 
            <img src="${ctxt.root}/static/images/query.png" />
            <select><option value="==">is</option></select> 
            <input type="text" name="value" placeholder="Value" />
        </p>

        <p class="e2l-test-constraint">
            <button>X</button><button>+</button>
            <input type="text" name="param" placeholder="Parameter" /> 
            <img src="${ctxt.root}/static/images/query.png" />
            <select><option value="==">is</option></select> 
            <input type="text" name="value" placeholder="Value" />
        </p>

        <input type="submit" />

    </div>
    
</div>

    



</form>

<br /><br /><br /><br />


${query.table(q)}

