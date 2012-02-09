## Tile viewer

<div class="e2-tile-outer">
	% if rec.get('file_binary_image'):
		<div class="e2-tile" style="height:512px;overflow:hidden" data-bdo="${rec.get('file_binary_image')}" data-mode="cached"></div>
	% else:
		<div style="height:512px;overflow:hidden">No image</div>
	% endif
</div>
