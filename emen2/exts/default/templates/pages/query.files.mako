<%! import jsonrpc.jsonutil %>
<%inherit file="/page" />
<%

def convert_bytes(bytes):
	bytes = float(bytes)
	if bytes >= 1099511627776:
		terabytes = bytes / 1099511627776
		size = '%.2f TB' % terabytes
 	elif bytes >= 1073741824:
		gigabytes = bytes / 1073741824
		size = '%.2f GB' % gigabytes
	elif bytes >= 1048576:
		megabytes = bytes / 1048576
		size = '%.2f MB' % megabytes
	elif bytes >= 1024:
		kilobytes = bytes / 1024
		size = '%.2f KB' % kilobytes
	else:
		size = '%.2f bytes' % bytes
	return size
%>


<%block name="js_ready">
	${parent.js_ready()}

	function updatefilesize() {
		var s = 0;
		var c = $('input[name=bids]:checked');
		c.each(function() {
			var z = parseInt($(this).attr('data-filesize'));
			if (z > 0) {
				s += z;
			}
		});
		$('#filesize').text(emen2.template.prettybytes(s));
		$('#filecount').text(c.length);
	}

	$('#allbids').click(function() {
		var s = $(this).attr('checked');
		if (!s) {s=false}
		$('input[name=bids]').each(function() {
			$(this).attr('checked', s);
		});
		updatefilesize();
	});
	
	$('input[name=bids]').click(function() {
		updatefilesize();
	});

	updatefilesize();

</%block>


<form method="post" action="${EMEN2WEBROOT}/download/">
<h1>
	<span id="filecount">${len(bdos)}</span> files, <span id="filesize">${filesize}</span>
	<ul class="e2l-actions">
		<li>
			<input type="submit" value="Download Checked Files" />
		</li>
	</ul>
</h1>



<table class="e2l-shaded" cellpadding="0" cellspacing="0">
	<thead>
		<tr>
			<th><input type="checkbox" checked="checked" id="allbids" value="" /></th>
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
				<a href="${EMEN2WEBROOT}/download/${bdo.name}/${bdo.filename}">
					<img class="e2l-thumbnail" src="${EMEN2WEBROOT}/download/${bdo.name}/thumb.jpg?size=thumb" alt="" /> 
					${bdo.filename}
				</a>
			</td>
			<td>${convert_bytes(bdo.get('filesize',0))}</td>
			<td><a href="${EMEN2WEBROOT}/record/${bdo.record}/">${rendered.get(bdo.record)}</a></td>
			<td><a href="${EMEN2WEBROOT}/user/${bdo.get('creator')}/">${users.get(bdo.get('creator'), dict()).get('displayname')}</a></td>
			<td><time class="e2-localize" datetime="${bdo.get('creationtime')}">${bdo.get('creationtime')}</time></td>
		</tr>
	% endfor
	</tbody>

</table>

</form>
