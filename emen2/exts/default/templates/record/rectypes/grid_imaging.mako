<%! import jsonrpc.jsonutil  %>
<%inherit file="/record/record.main" />
<%namespace name="buttons" file="/buttons"  />
<%include file="/record/rectypes/_default" />

<%
children = DB.rel.children(rec.name, recurse=-1, rectype=['image_capture*'])
bdos = DB.binary.find(record=children, count=0)
children_recnames = DB.record.render(children)
%>

## <br /><br /> <%buttons:singlepage label='In this session...'>
<h1>In this session...</h1>

	<p>There are ${len(children)} image records in this imaging session, with ${len(bdos)} attachments. <a href="/query/children.is.${rec.name}*/attachments/">Download all attachments</a>.</p>

	% for bdo in bdos:
		<div class="e2l-float-left" style="margin-right:10px;margin-bottom:10px;padding:10px;border:solid 1px #ccc">
			<a href="${EMEN2WEBROOT}/record/${bdo.record}/">
				<img src="${EMEN2WEBROOT}/download/${bdo.name}/thumb.jpg?size=small&format=jpg" /><br />
				${children_recnames.get(bdo.record)}
			</a>
		</div>
	% endfor


## </%buttons:singlepage>