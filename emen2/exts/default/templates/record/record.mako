<%! 
import jsonrpc.jsonutil
import operator 
import collections
%>

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
    <div class="e2-tree-main" style="overflow:hidden">${parentmap}</div>
</%block>


<%block name="css_inline">
    ${parent.css_inline()}
</%block>


<%block name="js_ready">
    ${parent.js_ready()}

    ${buttons.tocache(rec)}

    emen2.caches['recnames'] = ${jsonrpc.jsonutil.encode(recnames)};

    $('.e2-tree').TreeControl({'attach':true});

    // Record, ptest
    var rec = emen2.caches['record'][${jsonrpc.jsonutil.encode(rec.name)}];
    var ptest = ${jsonrpc.jsonutil.encode(rec.ptest())}

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
        });
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
        });
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
        });
    });
    
    // New record editor
    tab.TabControl('setcb', 'new', function(page) {
        page.NewRecordChooserControl({
            parent: rec.name,
            controls: page,
            help: true,
            summary: true
        });
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
        });
    });

    // Comments editor
    tab.TabControl('setcb', 'comments', function(page) {
        page.CommentsControl({
            name: rec.name,
            edit: ptest[1] || ptest[2] || ptest[3],
            controls: page,
            historycount: "#e2l-editbar2-commentcount",
            commentcount: '#e2l-editbar2-historycount'
        });
    });

    // Simple handler for browsing siblings...
    tab.TabControl('setcb', 'siblings', function(page) {
        page.SiblingsControl({
            name: rec.name
        })
    });
    
    // Now that we have all the callbacks added...
    tab.TabControl('checkhash', ${jsonrpc.jsonutil.encode(tab)});
    
    $('.e2-record-new').RecordControl({});
    
</%block>





<div class="home-sidebar">

    <ul id="e2-tab-editbar2" class="e2l-cf home-projectlist" role="tablist" data-tabgroup="record">

        ## Title
        <li>
            <h2 class="e2l-gradient">
                <a href="${EMEN2WEBROOT}/record/${rec.name}/">
                    Record: ${recnames.get(rec.name, rec.name)}
                    ## Record
                    ## ${rec.name}
                    ## % if tab == "main":
                    ##    <span class="e2l-float-right" style="padding-right:5px;">&raquo;</span>
                    ## % endif
                </a>
            </h2>
        </li>


        ## Main tab
        ## <li data-tab="main" ${istab(tab, "main")}><a href="#main">Main</a></li>


        ## Edit Record
        % if rec.writable():
            <li data-tab="edit" ${istab(tab, "edit")}><a href="#edit">${buttons.image('edit.png')} Edit</a></li>
        % endif


        ## New Record
        % if create:
            <li data-tab="new" ${istab(tab, "new")}><a href="#new">${buttons.image('new.png')}New</a></li>
        % endif


        ## Permissions Editor
        <li data-tab="permissions"><a href="#permissions">${buttons.image('permissions.png')} Permissions</a></li>


        ## Attachments Editor
        <%
        attachments = []
        # cheap filtering....
        for k in rec.paramkeys():
            v = rec[k]
            if hasattr(v, "__iter__"):
                attachments.extend(x for x in v if 'bdo:' in str(x))
            elif "bdo:" in unicode(v):
                attachments.extend([v])
        %>        
        <li data-tab="attachments">
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
        <li data-tab="relationships"><a href="#relationships">${buttons.image('relationships.png')} Relationships</a></li>


        ## View Selector
        <li data-tab="views">
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
        <li data-tab="comments">
            <a href="#comments">
                <span id="e2l-editbar2-commentcount">
                    <img id="e2l-editbar2-comments-img" src="${EMEN2WEBROOT}/static/images/comment.closed.png" alt="Comments" />
                    ${len(comments)} Comments
                </span>
            </a>
        </li>
        
        <li data-tab="comments">
            <a href="#comments">
                <span id="e2l-editbar2-historycount">
                    <img id="e2l-editbar2-comments-img" src="${EMEN2WEBROOT}/static/images/history.png" alt="Edits" />
                    ${historycount} Edits
                </span>            

                <p style="text-align:center">
                ## C: ${users_d.get(cu, dict()).get('displayname', cu)}<br /> <time class="e2-localize" datetime="${rec.get("creationtime")}">${rec.get("creationtime")[:10]}</time>
                ## <br />
                ## % if rec.creationtime != rec.modifytime:
                ${users_d.get(mu, dict()).get('displayname', mu)}<br /> <time class="e2-localize e2l-tiny" datetime="${rec.get("modifytime")}">${rec.get("modifytime")[:10]}</time>
                ## % endif
                </p>

            </a>
        </li>
        
        
        ## Children tabs
        <li style="margin-top:50px">
            <h2 class="e2l-cf e2l-gradient">
                <a href="${EMEN2WEBROOT}/record/${rec.name}/children/">Children</a>
            </h2>
        </li>

        % if not children_groups:
            ## <li data-tab="new"><a href="#new">No children</a></li>
            <li><a href="">No children</a></li>
        % endif

        % for k,v in children_groups.items():
            <li ${istab(tab, "children-%s"%k)}>
                <a href="${EMEN2WEBROOT}/record/${rec.name}/children/${k}/">${recdefs_d.get(k, dict()).get('desc_short', k)}</a>
                <span class="e2l-shadow home-count">${len(v)}</span>
            </li>
        % endfor


        ## Tools
        ## ${buttons.image('tools.png')} 
        ## This is a block that can be extended by rectype-specific child templates.
        <%block name="tools">
            ## <li style="margin-top:100px">
            ##    <h2 class="e2l-gradient"><a href="#">Tools</a></h2>
            ## </li>
            ## <li><a href="${EMEN2WEBROOT}/record/${rec.name}/email/">Email Users</a></li>
            ## <li><a href="${EMEN2WEBROOT}/record/${rec.name}/publish/">Manage public data</a></li>
            ## <li><a href="${EMEN2WEBROOT}/record/${rec.name}/query/attachments/">Child attachments</a></li>
            ## <li><a href="${EMEN2WEBROOT}/record/${rec.name}/?viewname=dicttable">Param-value table</a></li>
        </%block>

        
        
    </ul>

</div>





<div class="e2-tab e2-tab-editbar2 home-main" data-tabgroup="record" role="tabpanel">

    % for k,v in children_groups.items():
        % if k == childtype:
            <div data-tab="children-${k}" class="e2-tab-active">${table}</div>
        % else:
            <div data-tab="children-${k}"></div>        
        % endif
    % endfor

    <div data-tab="main" ${istab(tab, "main")}>
        ${next.body()}
    </div>

    <div data-tab="edit" ${istab(tab, "edit")}>
        <form enctype="multipart/form-data" id="e2-edit" method="post" data-name="${rec.name}" action="${EMEN2WEBROOT}/record/${rec.name}/edit/">
            ${rendered}
        </form>    
    </div>
    
    <div data-tab="new"></div>
    
    <div data-tab="relationships">
        <form id="e2-relationships" method="post" action="${EMEN2WEBROOT}/record/${rec.name}/edit/relationships/"></form>
    </div>     
    
    <div data-tab="permissions">
        <form id="e2-permissions" method="post" action="${EMEN2WEBROOT}/record/${rec.name}/edit/permissions/"></form>
    </div>
    
    <div data-tab="attachments">
        <form id="e2-attachments" method="post" enctype="multipart/form-data" action="${EMEN2WEBROOT}/record/${rec.name}/edit/attachments/"></form>
    </div>
    
    <div data-tab="comments"></div>
    
    <div data-tab="views">
        <%
        prettynames = {'defaultview': 'default', 'mainview': 'protocol', 'recname': 'record name', 'tabularview':'table columns', 'dicttable':'parameter-value table'}
        recdef.views['defaultview'] = recdef.views.get('defaultview') or recdef.mainview        
        %>
        <h2>Record views</h2>
        
        <p>You are viewing the ${prettynames.get(viewname, viewname)} view for this record.</p>

        <p>This record uses the <a href="${EMEN2WEBROOT}/recorddef/${recdef.name}">${recdef.desc_short} protocol</a>, which provides ${len(recdef.views)+2} views:
            <ul>
                <li><a href="${EMEN2WEBROOT}/record/${rec.name}/?viewname=mainview">Protocol</a></li>
                <li><a href="${EMEN2WEBROOT}/record/${rec.name}/?viewname=dicttable">Parameter-Value table</a></li>                
                % for v in recdef.views:
                    <li><a href="${EMEN2WEBROOT}/record/${rec.name}/?viewname=${v}">${prettynames.get(v, v).capitalize()}</a></li>
                % endfor
            </ul>
        </p>        
    </div>
</div>




