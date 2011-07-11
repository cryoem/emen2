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
		<span class="label">
			You are creating a new <a href="${ctxt.reverse('RecordDef',name=rec.rectype)}">${recdef.desc_short} (${recdef.name})</a>
			record as a child of <a href="${ctxt.reverse('Record',name=rec.name)}">${recnames.get(rec.name, rec.name)}</a>
			
			<div class="hidden show">Test!</div>
		</span>
	</li>
	
	<li>
		<span class="label">${recdef.desc_long}</span>
	</li>

</ul>

<div id="rendered" class="e2-view" data-viewtype="${viewtype}" data-name="None" data-edit="true">
	${rendered}
</div>

<div class="clearfix save">
	<div class="e2-newrecord-save" class="label">Edit</div>
</div>

<%call expr="buttons.singlepage('e2-newrecord-permissions','Permissions')">
	<div class="e2-newrecord-permissions"></div>
</%call>
