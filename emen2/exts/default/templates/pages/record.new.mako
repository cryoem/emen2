<%inherit file="/pages/record" />
<%namespace name="buttons" file="/buttons" />
<%import jsonrpc.jsonutil %>

<script type="text/javascript">
//<![CDATA[
	$(document).ready(function() {
		record_init_new(${jsonrpc.jsonutil.encode(newrec)});
	});
//]]>
</script>


<ul class="menu editbar floatlist clearfix">

	<li>
		<span class="label">New</span>
	</li>

	
	<li id="e2-editbar-newrecord-info">
		<span class="clickable label">
			Info <img src="${EMEN2WEBROOT}/static/images/caret_small.png" alt="^" />
		</span>
		<div class="hidden">
			You are creating a new <a href="${ctxt.reverse('RecordDef', name=rec.rectype)}">${recdef.desc_short} (${recdef.name})</a>
			record as a child of <a href="${ctxt.reverse('Record', name=rec.name)}">${recnames.get(rec.name, rec.name)}</a>			
			<h4>Protocol Description</h4>
			${recdef.desc_long}
		</div>
	</li>

	<li id="e2-editbar-newrecord-relationships">
		<span class="clickable label">
			Relationships
			<img src="${EMEN2WEBROOT}/static/images/caret_small.png" alt="^" />
		</span>
		<div id="e2-newrecord-relationships" class="hidden"></div>
	</li>

	<li id="e2-editbar-newrecord-permissions">
		<span class="clickable label">
			Permissions
			<img src="${EMEN2WEBROOT}/static/images/caret_small.png" alt="^" />
		</span>
		<div id="e2-newrecord-permissions" class="hidden"></div>
	</li>

	<li id="e2-editbar-newrecord-recorddef">
		<span class="clickable label">Change Protocol <img src="${EMEN2WEBROOT}/static/images/caret_small.png" alt="^" /></span>
		<div class="hidden">
			Blah blah <input type="text" value="${recdef.name}" />
		</div>
	</li>
	
</ul>


<div id="rendered" class="e2-view" data-viewtype="${viewtype}" data-name="None" data-edit="true">
	${rendered}
</div>

<div class="clearfix save">
	<div id="e2-newrecord-save" class="label">Edit</div>
</div>

