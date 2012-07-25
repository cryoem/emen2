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
	//	redirect:window.location.pathname
	});

	$('.e2-record-edit').RecordControl({
		redirect:window.location.pathname
	});
		
	$('#activity time').timeago();	
</%block>



<div class="home-sidebar">

	## <div class="e2-infobox" style="width:100%">
	##	% if USER.userrec.get('person_photo'):
	##		<img class="e2l-thumbnail" src="${EMEN2WEBROOT}/download/${USER.userrec.get('person_photo')}/user.jpg?size=small" />
	##	% endif	
	##	<div>
	##		<h4>${USER.displayname}</h4>
	##		<div class="e2l-small">
	##			${USER.email}
	##		</div>
	##	</div>
	## </div>
	## <br /><br /><br /><br />

	<ul class="e2l-cf home-projectlist" role="tablist" data-tabgroup="record">
		<li><h2>Groups</h2></li>
		% for group in groups:
			<li><a href="#groups-${group.name}">${recnames.get(group.name,group.name)}</a></li>
		% endfor
	</ul>

	<a class="e2-button e2-record-new" href="${EMEN2WEBROOT}/record/0/new/group/" class="e2-record-new" data-parent="0" data-rectype="group">${buttons.image('new.png')} New group</a>
	
</div>

<div class="home-main">
	${next.body()}
</div>