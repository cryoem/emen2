<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

<% 
import jsonrpc.jsonutil 
%>

<div id="rendered" class="e2-view" data-viewname="${viewname}" data-name="${rec.name}" ${['', 'data-edit="true"'][rec.writable()]}>
	${rendered}
</div>

