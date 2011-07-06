<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

<% 
import jsonrpc.jsonutil 
%>


<script type="text/javascript">
//<![CDATA[

	// init view edit
	$(document).ready(function() {
##		record_init(${jsonrpc.jsonutil.encode(rec)}, ${jsonrpc.jsonutil.encode(rec.ptest()}, true);
	});	

//]]>
</script>



% if rec.get('deleted'):
	<div class="notify deleted">Deleted Record</div>
% endif


<div id="rendered" class="view" data-viewtype="${viewtype}" data-name="${rec.name}" ${['', 'data-edit="true"'][rec.writable()]}>
	${rendered}
</div>


% if pages_comments:
	${buttons.all(pages_comments)}
% endif





