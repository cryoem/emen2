<%! import jsonrpc.jsonutil  %>
<%inherit file="/record/record" />
<%namespace name="buttons" file="/buttons"  /> 

## Tile viewer
<%
check = ['file_binary_image', 'ddd_binary_sum']
found = None
for i in check:
    if rec.get(i):
        found = rec.get(i)
        if hasattr(found, "__iter__"):
            found = found.pop()
        break
%>
% if found:
    <div class="e2-tile-outer">
        <div class="e2-tile" style="height:512px;overflow:hidden" data-bdo="${found}" data-mode="cached"></div>
    </div>
% endif

${next.body()}

