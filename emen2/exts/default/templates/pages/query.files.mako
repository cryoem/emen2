<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />
<%namespace name="table" file="/pages/table"  /> 



<%block name="javascript_ready">
	${parent.javascript_ready}

	function updatefilesize() {
		var s = 0;
		var c = $('input[name=bids]:checked');
		c.each(function() {
			var z = parseInt($(this).attr('data-filesize'));
			if (z > 0) {
				s += z;
			}
		});
		$('#filesize').text($.convert_bytes(s));
		$('#filecount').text(c.length);
	}

	$('input[name=checkbids]').click(function() {
		var s = $(this).attr('checked');
		$('input[name=bids]').each(function() {
			$(this).attr('checked', s);
		});
		updatefilesize();
	});
	
	$('input[name=bids]').click(function() {
		updatefilesize();
	});

</%block>


<form method="post" action="${EMEN2WEBROOT}/download/save/">

<h1>
	<span id="filecount">${len(bdos)}</span> files, <span id="filesize">${filesize}</span>
	<div class="e2l-controls">
		<input type="submit" value="Download Checked Files" name="download">
	</div>
</h1>



<table>
	<thead>
		<tr>
			<th><input type="checkbox" checked="checked" name="checkbids" value="" /></th>
			<th>Filename</th>
			<th>Size</th>
			<th>Record</th>
			<th>Creator</th>
			<th>Created</th>
		</tr>
	</thead>
	
	<tbody>
	% for bdo in bdos:
		<tr>
			<td><input type="checkbox" checked="checked" name="bids" value="${bdo.name}" data-filesize="${bdo.get('filesize',0)}" /></td>
			<td>
				<a href="${EMEN2WEBROOT}/download/${bdo.name}/${bdo.filename}/save/">
					<img class="e2l-thumbnail" src="${EMEN2WEBROOT}/download/${bdo.name}/${bdo.filename}?size=thumb" alt="" /> 
					${bdo.filename}
				</a>
			</td>
			<td>${bdo.get('filesize',0)}</td>
			<td><a href="${EMEN2WEBROOT}/record/${bdo.record}/">${rendered.get(bdo.record)}</a></td>
			<td><a href="${EMEN2WEBROOT}/user/${bdo.get('creator')}/">${users.get(bdo.get('creator'), dict()).get('displayname')}</a></td>
			<td>${bdo.get('creationtime')}</td>
		</tr>
	% endfor
	</tbody>

</table>

</form>
