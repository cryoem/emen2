<%! 
import jsonrpc.jsonutil
import operator 
import collections
%>

<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

<%block name="js_ready">
    ${parent.js_ready()}

    $('.e2-record-new').RecordControl({});

    $('.e2-record-edit').RecordControl({
        redirect:window.location.pathname
    });
        
    $('#activity time').timeago();    
    
    ## Recent activity viewer
    var q = ${recent_activity | n,jsonencode};
    $('#recent_activity').PlotHistogram({
        q:q,
        pan: false,
        height:200,
    });
</%block>

<div class="e2l-sidebar-sidebar">
    
    <ul class="e2l-cf e2l-sidebar-projectlist">
        % for k,v in sorted(groups_group.items(), key=lambda x:recnames.get(x[0],'').lower()):
        <li><h2 class="e2l-gradient">${recnames.get(k,k)}</h2></li>
            % for group in sorted(v, key=lambda x:recnames.get(x,'').lower()):
                <li><a href="#groups-${group}">${recnames.get(group,group)}</a></li>
            % endfor
        <li style="margin-bottom:20px;"></li>
        % endfor
    </ul>

	% if ADMIN:
    	<a class="e2-button e2-record-new" href="${ctxt.root}/record/root/new/${default_group.name}/" data-parent="root" data-rectype="${default_group.name}">${buttons.image('new.png')} New ${default_group.desc_short}</a>
	% endif
    
</div>

<div class="e2l-sidebar-main">

    % if banner:
        <h1>
            Welcome to ${TITLE}
            % if banner.writable():
                <a class="e2l-hact e2-button e2-record e2-record-edit" data-name="${banner.name}" href="${ctxt.root}/record/${banner.name}#edit">${buttons.image('edit.png')} Edit</a>
            % endif
        </h1>
        <div class="e2l-cf">
            ${render_banner | n,unicode}
        </div>
        <br /><br />
    % endif

    <h1>
        Activity and recent records
        <a class="e2l-hact e2-button" href="${ctxt.root}/records/">Browse records</a>
        <a class="e2l-hact e2-button" href="${ctxt.root}/query/results/">All records</a>
    </h1>

    <div id="recent_activity">
        <div class="e2-plot"></div>
    </div>

    ## ${unicode(recent_activity_table) | n}

    % for group in groups:
        <h1>
            <a href="${ctxt.root}/record/${group.name}/" id="groups-${group.name}">
            	${recnames.get(group.name, group.name)}
    		</a>
                % if group.writable():
                    <a class="e2l-hact e2-button e2-record-new" href="${ctxt.root}/record/${group.name}/new/${default_project.name}/" data-parent="${group.name}" data-rectype="${default_project.name}">${buttons.image('new.png')} New ${default_project.desc_short}</a>
                % endif
        </h1>
    
        <ul class="e2l-sidebar-projectlist">
            % if not groups_children.get(group.name):
                <li>No projects</li>
            % endif
            % for project in sorted(groups_children.get(group.name, []), key=lambda x:recnames.get(x, '').lower()):
                <li>
                    <a href="${ctxt.root}/record/${project}/">
                        ${recnames.get(project, project)}
                    </a>
                    <span class="e2l-shadow e2l-sidebar-count">
                        ${len(projects_children.get(project, [])) or ''}                        
                    </span>
                    </li>
            % endfor
        </ul>
    
        <br /><br /><br /><br />
    % endfor
    
</div>