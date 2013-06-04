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
    	<a class="e2-button e2-record-new" href="${ctxt.root}/record/0/new/group/" data-parent="0" data-rectype="group">${buttons.image('new.png')} New group</a>
	% endif
    
</div>

<div class="e2l-sidebar-main">
    ${next.body()}
</div>