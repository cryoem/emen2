<%! import jsonrpc.jsonutil  %>
<%inherit file="/record/record.main" />
<%namespace name="buttons" file="/buttons"  />




<%block name="tools">
Tools?!?!
</%block>


## Tile viewer
% if rec.get('file_binary_image'):
	<div class="e2-tile-outer">
		<div class="e2-tile" style="height:512px;overflow:hidden" data-bdo="${rec.get('file_binary_image')}" data-mode="cached"></div>
	</div>
% endif

## Main rendered record
<form enctype="multipart/form-data" id="e2-edit" method="post" data-name="${rec.name}" action="${EMEN2WEBROOT}/record/${rec.name}/edit/">
	<div id="content_inner" class="e2-view" data-viewname="${viewname}" data-name="${rec.name}" ${['', 'data-edit="true"'][rec.writable()]}>
		${rendered}
	</div>
</form>
