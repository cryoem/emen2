<%! 
import jsonrpc.jsonutil
import collections
%>

<%inherit file="/em/home" />
<%namespace name="buttons" file="/buttons"  /> 

<%block name="js_ready">
    ${parent.js_ready()}
    ## Recent activity viewer
    var q = ${jsonrpc.jsonutil.encode(recent_activity)}; 
    var plot = new $.emen2.PlotHistogram({
        q:q,
        pan: false,
        height:200,
    }, $('#recent_activity'));
    plot.z.build_legend($("#home-activity-users"));
    
    
    $('#home-project-children').TabControl();

</%block>

<%block name="css_inline">
    ${parent.css_inline()}
    #home-activity-users ul {
        list-style: none;
    }
    #home-activity-users li {
        float: left;
        margin: 5px;
    }

    .e2l-shaded-drop {
        background:#fff;
        margin:10px;
    }

    .e2-tab-active h1 {
        border:none;
        font-size:14pt;
    }

</%block>

<%
groups_d = dict(([i.name, i] for i in groups))
users_d = dict(([i.name, i] for i in users))
recorddefs_d = dict(([i.name, i] for i in recorddefs))

def format_keys(s, names, key='displayname'):
    ret = []
    for i in names:
        item = s.get(i, dict())
        ret.append(item.get(key, i))
    return ", ".join(ret)


pi1 = set(project.get('project_investigators') or [])
pi2 = set(project.get('name_pi') or [])

inv_diff = False
if project['permissions'][0] or project['permissions'][1] or set(project['permissions'][2])^pi1 or set(project['permissions'][3])^pi2:
    inv_diff = True


%>


<div class="home-main">
    
    <h1>
        Project details
        <ul class="e2l-actions">
            <li><a data-name="${project.name}" class="e2-button" href="${EMEN2WEBROOT}/record/${project.name}/">View full record</a></li>
            <li><a data-name="${project.name}" class="e2-button e2-record-edit" href="${EMEN2WEBROOT}/record/${project.name}/edit">${buttons.image('edit.png')} Edit</a></li>
        </ul>
    </h1>
    
    
    <%buttons:singlepage label='Project details'>    
        ${project_render}
    </%buttons:singlepage>


    <%buttons:singlepage label='Permissions'>
        <p>
            These are the current permissions on this project:
            <ul class="e2l-nonlist e2l-shaded-drop">
                <li><strong>Groups:</strong> ${format_keys(groups_d, project['groups'])} </li>
                <li><strong>Read:</strong> ${format_keys(users_d, project['permissions'][0])} </li>
                <li><strong>Comment:</strong> ${format_keys(users_d, project['permissions'][1])} </li>
                <li><strong>Write:</strong> ${format_keys(users_d, project['permissions'][2])} </li>
                <li><strong>Owners:</strong> ${format_keys(users_d, project['permissions'][3])} </li>
            </ul>
        </p>
    
        % if inv_diff and project.isowner():
            <p>
                The project's current investigators are:
                <ul class="e2l-nonlist e2l-shaded-drop">
                    <li><strong>PI:</strong> ${format_keys(users_d, project.get('name_pi',[]))} </li>        
                    <li><strong>Investigators:</strong> ${format_keys(users_d, project.get('project_investigators', []))} </li>        
                </ul>
                <br />
                You may want to reset the permissions to match the current investigators. This action will give the PIs "owner" permissions, and other investigators will be given "write" permissions.     
                <strong>Note:</strong> this will overwrite the permissions in all child records, including any subprojects.
        
                <br />
                <form action="${EMEN2WEBROOT}/em/home/project/${project.name}/resetpermissions/" method="post">
                <ul class="e2l-actions">
                    <li><input type="submit" value="Set permissions to match investigators" /></li>
                </ul>        
                </form>
            </p>
        % endif
    </%buttons:singlepage>

    
    
    <%buttons:singlepage label='Recent activity by user'>    
        <div id="recent_activity">
            <div class="e2-plot"></div>
        </div>
        <div id="home-activity-users"></div>
    </%buttons:singlepage>
    

    <div class="e2-tab e2-tab-switcher" id="home-project-children">
        <ul class="e2l-cf">
        % for count, k in enumerate(childtables):
            % if count == 0:
                <li class="e2-tab-active" data-tab="${k.name}">${k.desc_short}</li>
            % else:
                <li data-tab="${k.name}">${k.desc_short}</li>        
            % endif
        % endfor
        </ul>
    
        % for count, (k,v) in enumerate(childtables.items()):
            % if count == 0:
                <div class="e2-tab-active" data-tab="${k.name}">
            % else:
                <div data-tab="${k.name}">
            % endif
                ${v}
            </div>
        % endfor
    </div>

</div>
