<%! import collections %>
<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

<%def name="istab(tab1, tab2)">
    % if tab1 == tab2:
        class="e2-tab-active"
    % endif
</%def>


<%
children_groups = collections.defaultdict(set)
for i in children:
    children_groups[i.rectype].add(i)

users_d = dict((i.name, i) for i in users)    
recdefs_d = dict((i.name, i) for i in recdefs)
%>


## Relationship tree
<%block name="precontent">
    ${parent.precontent()}
    ## Disable encoding -- this comes from another template.
    <div class="e2-tree-main" style="overflow:hidden">${parentmap | n,unicode}</div>
</%block>


<%block name="css_inline">
    ${parent.css_inline()}
</%block>


<%block name="js_ready">
    ${parent.js_ready()}

    ${buttons.tocache(rec)}

    emen2.caches['recnames'] = ${recnames | n,jsonencode};

    $('.e2-tree').TreeControl({'attach':true});

    // Record, ptest
    var rec = emen2.caches['record'][${rec.name | n,jsonencode}];
    var ptest = ${rec.ptest() | n,jsonencode}

    // Tile browser
    $('.e2-tile').TileControl({'mode':'cached'});
        
    // Intialize the Tab controller
    var tab = $("#e2-tab-editbar2");        
    tab.TabControl({});

    // Editor
    tab.TabControl('setcb', 'edit', function(page) {
        $('#e2-edit', page).MultiEditControl({
            show: true,
            controls: page,
        })
    });

    // Permissions editor
    tab.TabControl('setcb','permissions', function(page) {
        $('#e2-permissions', page).PermissionsControl({
            name: rec.name,
            edit: ptest[3],
            show: true,
            controls: page,
            summary: true,
            help: true
        })
    });
    
    // Attachments editor
    tab.TabControl('setcb', 'attachments', function(page) {
        $('#e2-attachments', page).AttachmentControl({
            name: rec.name,
            edit: ptest[2] || ptest[3],
            show: true,
            summary: true,
            help: true,
            controls: $('#e2-attachments', page)
        })
    });
    
    // New record editor
    tab.TabControl('setcb', 'new', function(page) {
        page.NewRecordChooserControl({
            parent: rec.name,
            controls: page,
            help: true,
            summary: true
        })
    });        

    // Relationship editor
    tab.TabControl('setcb', 'relationships', function(page) {
        $('#e2-relationships', page).RelationshipControl({
            name: rec.name,
            edit: ptest[2] || ptest[3],
            embed: true,
            show: true,
            summary: true,
            help: true,
            controls: page
        })
    });

    // Comments editor
    tab.TabControl('setcb', 'comments', function(page) {
        page.CommentsControl({
            name: rec.name,
            edit: ptest[1] || ptest[2] || ptest[3],
            controls: page,
            historycount: "#e2l-editbar2-commentcount",
            commentcount: '#e2l-editbar2-historycount'
        })
    });

    // Simple handler for browsing siblings...
    tab.TabControl('setcb', 'siblings', function(page) {
        page.SiblingsControl({
            name: rec.name
        })
    });
    
    // Now that we have all the callbacks added...
    tab.TabControl('checkhash', ${tab | n,jsonencode});
    
    $('.e2-record-new').RecordControl({});
    
</%block>





<div class="e2l-sidebar-sidebar">

    <ul id="e2-tab-editbar2" class="e2l-cf e2l-sidebar-projectlist" role="tablist" data-tabgroup="record">

        ## Title
        <li role="tab">
            <h2 class="e2l-gradient">
                <a href="${ROOT}/record/${rec.name}/">Record #${rec.name}</a>
            </h2>
        </li>


        ## Main tab
        ## <li data-tab="main" ${istab(tab, "main")}><a href="#main">Main</a></li>


        ## Edit Record
        % if rec.writable():
            <li role="tab" data-tab="edit" ${istab(tab, "edit")}><a href="#edit">${buttons.image('edit.png')} Edit</a></li>
        % endif


        ## New Record
        % if create:
            <li role="tab" data-tab="new" ${istab(tab, "new")}><a href="#new">${buttons.image('new.png')}New</a></li>
        % endif


        ## Permissions Editor
        <li role="tab" data-tab="permissions"><a href="#permissions">${buttons.image('permissions.png')} Permissions</a></li>


        ## Attachments Editor
        <%
        attachments = []
        # cheap filtering....
        for k in rec.paramkeys():
            v = rec[k]
            if hasattr(v, "__iter__"):
                attachments.extend(x for x in v if 'bdo:' in unicode(x))
            elif "bdo:" in unicode(v):
                attachments.extend([v])
        %>        
        <li role="tab" data-tab="attachments">
            <a href="#attachments">
                ${buttons.image('attachments.png')}
                <span id="attachment_count">
                % if attachments:
                    ${len(attachments)}
                % endif
                </span> Attachments
            </a>
        </li>

        ## Relationship Editor
        <li role="tab" data-tab="relationships"><a href="#relationships">${buttons.image('relationships.png')} Relationships</a></li>


        ## View Selector
        <li role="tab" data-tab="views">
            <a href="#views">${buttons.image('table.png')} Views</a>
        </li>

        ## Comments!
        <%
        displaynames = dict([i.name, i.displayname] for i in users)
        comments = filter(lambda x:not x[2].startswith('LOG'), rec.get('comments', []))
        historycount = len(rec.get('history',[]))
        historycount += len(filter(lambda x:x[2].startswith("LOG:"), rec.get('comments',[])))
        cu = rec.get('creator')
        mu = rec.get('modifyuser')
        %>
        <li role="tab" data-tab="comments">
            <a href="#comments">
                <span id="e2l-editbar2-commentcount">
                    <img src="${ROOT}/static/images/comment.closed.png" alt="Comments" />
                    ${len(comments)} Comments
                </span>
            </a>
        </li>
        
        <li role="tab" data-tab="comments">
            <a href="#comments">
                <span id="e2l-editbar2-historycount">
                    <img src="${ROOT}/static/images/history.png" alt="Edits" />
                    ${historycount} Edits
                </span>            
            </a>
        </li>
        
        
        <li role="tab" style="text-align:center;margin-top:10px">
            ## Yes, it's wrong to use a table for layout -- 
            ##  but easiest way to have this kind of horizontal flow.
            <% 
                siblings_sort = sorted(siblings)
                try:
                    siblings_index = siblings_sort.index(rec.name)
                except ValueError:
                    siblings_index = 0
            %>
            <table>
                <tr>
                    <td></td>
                    <td>
                    
                        ## C: ${users_d.get(cu, dict()).get('displayname', cu)}<br /> 
                        ## <time class="e2-localize" datetime="${rec.get("creationtime")}">${rec.get("creationtime")[:10]}</time>
                        ## <br />
                        ## % if rec.creationtime != rec.modifytime:
                            ${users_d.get(mu, dict()).get('displayname', mu)}<br /> 
                            <time class="e2-localize e2l-tiny" datetime="${rec.get("modifytime")}">${rec.get("modifytime")[:10]}</time>
                        ## % endif
                    </td>
                    <td></td>
                </tr>


                <tr>
                    <td style="width:15px">
                        % if siblings_index > 0:
                            <a href="${ROOT}/record/${siblings_sort[siblings_index-1]}?sibling=${sibling}">&laquo;</a>
                        % endif
                    </td>
                    <td>
                        ## <a href="${ROOT}/recorddef/${rec.rectype}">
                        ${recdefs_d.get(rec.rectype, dict()).get('desc_short', rec.rectype)}
                        ## </a>
                        
                        % if len(siblings) > 1:
                            <br />
                            ${siblings_index+1} of ${len(siblings_sort)}                        
                        % endif
                    </td>
                    <td style="width:15px">
                        % if siblings_index < len(siblings)-1:
                            <a href="${ROOT}/record/${siblings_sort[siblings_index+1]}?sibling=${sibling}">&raquo;</a>
                        % endif
                    </td>
                </tr>
            </table>
        </li>
        
        
        ## Children tabs
        <li role="tab" style="margin-top:50px">
            <h2 class="e2l-cf e2l-gradient">
                <a href="${ROOT}/record/${rec.name}/children/">Children</a>
            </h2>
        </li>

        % if not children_groups:
            ## <li data-tab="new"><a href="#new">No children</a></li>
            <li role="tab"><a href="">No children</a></li>
        % endif

        % for k,v in children_groups.items():
            <li role="tab" ${istab(tab, "children-%s"%k)}>
                <a href="${ROOT}/record/${rec.name}/children/${k}/">${recdefs_d.get(k, dict()).get('desc_short', k)}</a>
                <span class="e2l-shadow e2l-sidebar-count">${len(v)}</span>
            </li>
        % endfor


        ## Tools
        ## ${buttons.image('tools.png')} 
        ## This is a block that can be extended by rectype-specific child templates.
        <%block name="tools">
            ## <li style="margin-top:100px">
            ##    <h2 class="e2l-gradient"><a href="#">Tools</a></h2>
            ## </li>
            ## <li><a href="${ROOT}/record/${rec.name}/email/">Email Users</a></li>
            ## <li><a href="${ROOT}/record/${rec.name}/publish/">Manage public data</a></li>
            ## <li><a href="${ROOT}/record/${rec.name}/query/attachments/">Child attachments</a></li>
            ## <li><a href="${ROOT}/record/${rec.name}/?viewname=kv">Param-value table</a></li>
        </%block>

        
        
    </ul>

</div>





<div class="e2-tab e2-tab-editbar2 e2l-sidebar-main" data-tabgroup="record" role="tabpanel">

    % for k,v in children_groups.items():
        % if k == childtype:
            ## Disable filtering -- this comes from another template.
            <div data-tab="children-${k}" class="e2-tab-active">${table | n,unicode}</div>
        % else:
            <div data-tab="children-${k}"></div>        
        % endif
    % endfor

    <div data-tab="main" ${istab(tab, "main")}>
        ${next.body()}
    </div>

    <div data-tab="edit" ${istab(tab, "edit")}>
        <form enctype="multipart/form-data" id="e2-edit" method="post" data-name="${rec.name}" action="${ROOT}/record/${rec.name}/edit/">
            ## Disable filtering -- each param/macro renderer is responsible for this.
            ${rendered | n,unicode}
        </form>    
    </div>
    
    <div data-tab="new"></div>
    
    <div data-tab="relationships">
        <form id="e2-relationships" method="post" action="${ROOT}/record/${rec.name}/edit/relationships/"></form>
    </div>     
    
    <div data-tab="permissions">
        <form id="e2-permissions" method="post" action="${ROOT}/record/${rec.name}/edit/permissions/"></form>
    </div>
    
    <div data-tab="attachments">
        <form id="e2-attachments" method="post" enctype="multipart/form-data" action="${ROOT}/record/${rec.name}/edit/attachments/"></form>
    </div>
    
    <div data-tab="comments"></div>
    
    <div data-tab="views">
        <%
        prettynames = {'defaultview': 'default', 'mainview': 'protocol', 'recname': 'record name', 'tabularview':'table columns', 'kv':'parameter-value table'}
        recdef.views['defaultview'] = recdef.views.get('defaultview') or recdef.mainview        
        %>
        <h2>Record views</h2>
        
        <p>You are viewing the ${prettynames.get(viewname, viewname)} view for this record.</p>

        <p>This record uses the <a href="${ROOT}/recorddef/${recdef.name}">${recdef.desc_short} protocol</a>, which provides ${len(recdef.views)+2} views:
            <ul>
                <li><a href="${ROOT}/record/${rec.name}/?viewname=mainview">Protocol</a></li>
                <li><a href="${ROOT}/record/${rec.name}/?viewname=kv">Parameter-Value table</a></li>                
                % for v in recdef.views:
                    <li><a href="${ROOT}/record/${rec.name}/?viewname=${v}">${prettynames.get(v, v).capitalize()}</a></li>
                % endfor
            </ul>
        </p>        
    </div>
</div>




