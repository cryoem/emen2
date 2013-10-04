<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

<% 
import jsonrpc.jsonutil 
%>


% if rec.get('hidden'):
    <div class="notify deleted">Hidden Record</div>
% endif

<div id="rendered" class="view" data-viewname="${viewname}" data-name="${rec.name}" ${['', 'data-edit="true"'][rec.writable()]}>
    ${rendered}
</div>

