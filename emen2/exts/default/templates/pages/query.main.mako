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

<div class="e2-tab e2-tab-switcher" id="e2-tab-query">
    <ul class="e2l-cf">
        <li data-tab="keywords">Keywords</li>
        <li class="e2-tab-active" data-tab="protocol">Protocol</li>
        <li data-tab="em_worksheets">EM Worksheets</li>
        <li data-tab="peas_worksheets">PEAS Worksheets</li>
        <li data-tab="images">Images</li>
        <li data-tab="publications">Publications</li>
        <li data-tab="extra">Add'l.</li>
    </ul>
    
    <div data-tab="keywords">
        <p>Keywords: <input type="text" name="keywords" /></p>
        <input type="submit" />
    </div>
    
    <div class="e2-tab-active"  data-tab="protocol">
        <p>Protocol number: <input type="text" placeholder="" /></p>
        <p>Protocol title: <input type="text" /></p>
        <p>Protocol dates: <input type="text" /> to <input type="text" /></p>
        <p>Protocol PI: <input type="text" /></p>
        <p>Division: <input type="text" /></p>
        <p>Microscrope used: <input type="text" /></p>
        <input type="submit" />
        
        <p>OUTPUT</p>
        <ul>
            <li>Worksheets under each Protocol, division, and PI</li>
            <li>Images per Protocol, division, and PI</li>
           ## <li>View: {{childcount(images)}} {{childcount(worksheets)}}
        </ul>
        <table>
            <thead>
                <tr>
                    <th>
                        <select>
                            <option>By protocol</option>
                            <option>By division</option>
                            <option>By microscope</option>
                            <option>By PI</option>
                        </select>
                    </th>
                    <th>Protocols</th>
                    <th>EM Worksheets</th>
                    <th>PEAS Worksheets</th>
                    <th>Images</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Protocol ABC</td>
                    <td>1</td>
                    <td>${int(random.random()*100)}</td>
                    <td>${int(random.random()*100)}</td>
                    <td>${int(random.random()*100)}</td>
                </tr>                
                <tr>
                    <td>Protocol DEF</td>
                    <td>1</td>
                    <td>${int(random.random()*100)}</td>
                    <td>${int(random.random()*100)}</td>
                    <td>${int(random.random()*100)}</td>
                </tr>                
                <tr>
                    <td>Protocol GHI</td>
                    <td>1</td>
                    <td>${int(random.random()*100)}</td>
                    <td>${int(random.random()*100)}</td>
                    <td>${int(random.random()*100)}</td>
                </tr>                
                                         
            </tbody>
        </table>

    </div>
    
    <div data-tab="em_worksheets">
        <h1>EM Worksheets</h1>
    </div>

    <div data-tab="peas_worksheets">
        <h1>PEAS Worksheets</h1>
    </div>
    
    <div data-tab="images"> </div>
    
    <div data-tab="publications"> </div>
    
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
    </div>
    
</div>

    



</form>

<br /><br /><br /><br />


${query.table(q)}

