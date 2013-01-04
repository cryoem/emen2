<%! 
import jsonrpc.jsonutil
import operator 
import collections
%>

<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 


<%block name="js_ready">
    ${parent.js_ready()}

    $('.e2-record-new').RecordControl({
    //    redirect:window.location.pathname
    });

    $('.e2-record-edit').RecordControl({
        redirect:window.location.pathname
    });
        
    $('#activity time').timeago();    
</%block>



<div class="e2l-sidebar-sidebar">
    
    <ul class="e2l-cf e2l-sidebar-projectlist">
        ## <li><h2 class="e2l-gradient">Home</h2></li>
        ## <li><a href="#activity">Activity</a></li>

        <li><h2 class="e2l-gradient">Lab Groups</h2></li>
        % for group in groups:
            <li><a href="#groups-${group.name}">${recnames.get(group.name,group.name)}</a></li>
        % endfor
    </ul>

	% if ADMIN:
    	<a class="e2-button e2-record-new" href="${ctxt.root}/record/0/new/group/" data-parent="0" data-rectype="group">${buttons.image('new.png')} New group</a>
	% endif
    
</div>

<div class="e2l-sidebar-main">
    ${next.body()}
</div>