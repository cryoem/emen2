<%! import jsonrpc.jsonutil  %>
<%inherit file="/record/record" />
<%namespace name="buttons" file="/buttons"  /> 

## Tile viewer
% if rec.get('file_binary_image'):
	<div class="e2-tile-outer">
		<div class="e2-tile" style="height:512px;overflow:hidden" data-bdo="${rec.get('file_binary_image')}" data-mode="cached"></div>
	</div>
% endif

<div id="content_inner">
	${next.body()}
</div>

