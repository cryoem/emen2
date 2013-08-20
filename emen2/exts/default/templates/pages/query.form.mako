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

<form action="${ctxt.root}/query/redirect/" method="post">

<div id="e2-tab-query" class="e2-tab e2-tab-switcher">
    <ul class="e2l-cf">
        <li class="e2-tab-active" data-tab="basic">Basic</li>
        <li data-tab="constraints">Constraints</li>
        <li data-tab="options">Options</li>
        ## <li data-tab="plot">Plot</li>
        <li data-tab="help">Help</li>
    </ul>
    
    <div class="e2-tab-active e2l-cf" data-tab="basic">
        
        ## <h2>Keywords</h2>
        ## <p>
        ##    <input type="text" placeholder="Keywords">    
        ## </p>
            
        <h2>Basic query</h2>
        <ul class="e2l-nonlist e2-query-base e2-query-constraints">
            <li class="e2-query-constraint">
                <strong class="e2-query-label">Protocol:</strong>
                <input type="hidden" name="form_0.param" value="rectype" />
                <input type="hidden" name="form_0.cmp" value="is" />
                <input type="text" name="form_0.value" id="e2-query-find-protocol" placeholder="Select protocol" value="" />
                <img class="e2-query-find" data-keytype="recorddef" data-target="e2-query-find-protocol" src="" />
                <input type="checkbox" name="form_0.recurse_v" id="e2-query-id-rectype"/><label for="e2-query-id-rectype">Include related protocols</label>
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
    </div>


    <div class="e2l-cf" data-tab="constraints">
        <h2>Additional query constraints</h2>
        <ul class="e2l-nonlist e2-query-param e2-query-constraints">
            % for i in range(5,10):
            <li>
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
    </div>
    
    <div data-tab="options">
        <h2>Table options</h2>
        
        <p>
            <strong>Columns:</strong>
        </p>
        <textarea name="view" placeholder="{{recname()}} {{rectype}} {{name}}"></textarea>
        
        <p>
            <strong class="e2-query-label">Rows:</strong> <input type="text" name="count" placeholder="100" /> <span class="e2l-small">(max 1,000)</span>
        </p>

        <p>
            <strong class="e2-query-label">Sort by:</strong> <input type="text" name="sortkey" placeholder="creationtime" /> <input checked="checked" type="checkbox">Reverse?
        </p>
        
        <p>
            <strong class="e2-query-label">Position</strong> <input type="text" name="pos" placeholder="0" />
        </p>        

    </div>

    
    <div data-tab="plot">
        <h2>Plotting options</h2>
        <p>Coming soon...</p>
    </div>

    <div data-tab="attachments">
        <h2>Attachment options</h2>
    </div>

    <div data-tab="help">
        <h2>Help</h2>
        
        <p>You can create a query using the options in the various tabs.</p>
        <br />
        
        <h3>Basic queries</h3>
        
        <p>
            Use the "Basic" tab to perform simple queries. The query icons (<img src="${ctxt.root}/static/images/query.png" />) can be clicked to help find a protocol, parameter, or user. </p>
            
        <p>To search for records of a particular protocol, type or select the desired protocol into the "Protocol" field. If you check the box for "Include related protocols", the query will be expanded to include all child protocols. For example, in an imaging database, <em>image_capture</em> might include the protocols <em>ccd</em>, <em>ddd</em>, and <em>stack</em> that are children of the <em>image_capture</em> protocol. You can use the <a href="${ctxt.root}/recorddefs/tree">protocol relationship browser</a> to view these relationships.</p>

        <p>The "Creator" field searches for records created by a particular user. Type a username or use the query icon to select a user.</p>
        
        <p>The "Child of" field searches based on <a href="${ctxt.root}/records/">record relationships</a>. For example, if you wanted to restrict the search to a particular project, you would enter or select the project's name (an integer) into the field. If the "Recursive" box is checked, the search will include all children recursively.</p>
        
        <p>The "Created" field can be used to search by date. You may specify a start date, an end date, or both to create a range. The current format is "YYYY-MM-DD", for example, "2012-06-05".</p>
        <br />

        <h3>Specifying additional constraints</h3>
        
        <p>This tab contains additional constraints. Type or select a parameter name, select a comparison, and enter a value. For example, "modifytime is greater than 2010-01" would select all records that had been updated since January 2010.</p>
        <br />
        
        <h3>Options</h3>
        
        <p>The table columns in the results page can be specified using the "Columns" field. By default the columns include a summary, protocol, record name, creator, and creation time. If a protocol is specified for the query, the "tabularview" view for that protocol will be used. You can provide the columns in either the new-style {{param}} format, or the older $$param format. Extraneous text and white space is ignored; e.g. you could paste in the entire protocol view and it will parse out the columns.</p>
        
        <p>The number of rows can be specified; the default is 100, the maximum is 1,000.</p>
        
        <p>The sorting column can be specified using "Sort by", with the table sorted by creation time by default. This can be a parameter or a macro, for example, childcount(). The sort order is ascending; the "Reverse" check box reverses this.</p>
        
        <p>The "Position" field simply gives the starting row in the table.</p>
        <br />

        <h3>Bookmarking</h3>
        
        <p>A query result can be bookmarked and shared, allowing quick access to common searches. Currently, the form is  not pre-filled based on a bookmarked query, but this will be added back soon.</p>
        
    </div>


</div>



<ul class="e2l-controls">
    <li><input type="submit" /></li>
</ul>
