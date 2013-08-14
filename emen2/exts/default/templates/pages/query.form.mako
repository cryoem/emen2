<%! 
import jsonrpc.jsonutil 
import random
%>
<%inherit file="/page" />

<%block name="js_ready">
    ${parent.js_ready()}
    
    // Tab control
    var tab = $("#e2-tab-query");        
    tab.TabControl();
    
    $('.e2-query-find')
        .attr('src', emen2.template.uri(['static', 'images', 'query.png']))
        .FindControl({});
        
    $('.e2-query-tree').TreeBrowseControl({
        root: "0",
        keytype: "record",
        selected: function(ui, name) {
            // Hacked: fix
            $('#e2-query-find-record').val(name);
        }
    })    
    
</%block>


<%
## Useful stuff.
## "contains": "contains",
comparators = (
    ("is", "is"),
    ("not", "is not"),
    ("gt", "is greater than"),
    ("lt", "is less than"),
    ("gte", "is greater than or equal to"),
    ("lte", "is less than or equal to"),
    ("any", "is any value"),
    ('noop', "no constraint")
    )

%>

<div class="e2-tab e2-tab-switcher">
    <ul class="e2l-cf">
        <li data-tab="keywords">Keywords</li>
        <li class="e2-tab-active" data-tab="constraints">Constraints</li>
    </ul>
    
    <div data-tab="keywords">
        This is a development version of the database. The query form is currently being redesigned, and will be back soon.
    </div>

    <div class="e2-tab-active e2l-cf" data-tab="constraints">
        
        <form action="/query/redirect/?count=100" method="post">
            
        <h2>Query constraints</h2>
        <ul class="e2l-nonlist e2-query-base e2-query-constraints">
            <li class="e2-query-constraint">
                <strong class="e2-query-label">Protocol:</strong>
                <input type="hidden" name="form_0.param" value="" />
                <input type="hidden" name="form_0.cmp" value="is" />
                <input type="text" name="form_0.value" id="e2-query-find-protocol" placeholder="Select protocol" value="" />
                <img class="e2-query-find" data-keytype="recorddef" data-target="e2-query-find-protocol" src="" />
                <input type="checkbox" name="form_0.recurse_v" id="e2-query-id-rectype"/><label for="e2-query-id-rectype">Include child protocols</label>
            </li>
            <li class="e2-query-constraint">
                <strong class="e2-query-label">Creator:</strong>
                <input type="hidden" name="form_1.param" value="creator" />
                <input type="hidden" name="form_1.cmp" value="is" />
                <input type="text" name="form_1.value" id="e2-query-find-user" placeholder="Select user" value="" />
                <img class="e2-query-find" data-keytype="user" data-target="e2-query-find-user" src="" />
            </li>
            <li class="e2-query-constraint">
                <strong class="e2-query-label">Child of:</strong>
                <input type="hidden" name="form_2.param" value="children" />
                <input type="hidden" name="form_2.cmp" value="name" />
                <input type="text" name="form_2.value" id="e2-query-find-record" placeholder="Select record"/>
                <img class="e2-query-tree" data-keytype="record" data-target="e2-query-find-record" src="" />
                <input type="checkbox" name="form_2.recurse_v" id="e2-query-paramid-children" checked="checked" /><label for="e2-query-paramid-children">Recursive</label>
            </li>
            <li>
                <strong class="e2-query-label">Created:</strong>
                <span class="e2-query-constraint">
                    <input type="hidden" name="form_3.param" value="creationtime" />
                    <input type="hidden" name="form_3.cmp" value="gte" />
                    <input type="text" name="form_3.value" placeholder="Start date" />

                    </span>&nbsp;&nbsp;&nbsp;to&nbsp;&nbsp;&nbsp;<span class="e2-query-constraint">

                    <input type="hidden" name="form_4.param" value="creationtime" />
                    <input type="hidden" name="form_4.cmp" value="lte" />
                    <input type="text" name="form_4.value" placeholder="end date" />
                </span>
            </li>
        </ul>
        <ul class="e2l-nonlist e2-query-param e2-query-constraints">
            % for i in range(5,8):
            <li>
                <strong class="e2-query-label">&nbsp;</strong>
                <input type="text" id="e2-query-find-${i}-param" name="form_${i}.param" value="" placeholder="Parameter" />
                <img class="e2-query-find" data-keytype="paramdef" data-target="e2-query-find-${i}-param" src="" />

                <select>
                % for k,v in comparators:
                <option value="${k}">${v}</option>
                % endfor
                </select>
                <input type="text" name="form_${i}.value" value="" placeholder="Value" />
                
            </li>
            % endfor
        </ul>
        
        <ul class="e2l-controls">
            <li><input type="submit" /></li>
        </ul>

    </div>









</div>


