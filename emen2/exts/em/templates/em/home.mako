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



<div class="home-sidebar">

    <ul class="e2l-cf home-projectlist" role="tablist" data-tabgroup="record">
        <li><h2>Groups</h2></li>
        % for group in groups:
            <li><a href="#groups-${group.name}">${recnames.get(group.name,group.name)}</a></li>
        % endfor
    </ul>

	% if ADMIN:
    	<a class="e2-button e2-record-new" href="${EMEN2WEBROOT}/record/0/new/group/" class="e2-record-new" data-parent="0" data-rectype="group">${buttons.image('new.png')} New group</a>
	% endif
    
</div>

<div class="home-main">
    ${next.body()}
</div>