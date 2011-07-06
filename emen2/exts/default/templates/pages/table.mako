<%def name="table(q, create=False, name=None, childtype=None, qc=True)">

	<% import jsonrpc.jsonutil %>

	<div class="e2-recordtable">
		<ul class="clearfix floatlist editbar menu editbar e2-table-header"></ul>
		<table class="e2-table-inner shaded" cellspacing="0" cellpadding="0"> 
			<thead>
				% for v in q['table']['headers'].get(None, []):
					<th><div data-name="${v[2]}" data-args="${v[3]}">${v[0]}</div></th>
				% endfor
			</thead>
			<tbody>
				% if not q['names']:
					<tr><td colspan="0">No Records found for this query.</td></tr>
				% endif

				% for rowid, name in enumerate(q['names']):
					<tr>						
					% for v in q['table'].get(name, []):
						<td>${v}</td>
					% endfor
					</tr>
				% endfor			
			</tbody>
		</table>

	<script type="text/javascript">
	//<![CDATA[
		$(document).ready(function() {
			$(".e2-recordtable").TableControl({
				q:${jsonrpc.jsonutil.encode(q)}, 
				qc:${jsonrpc.jsonutil.encode(qc)},
				% if create:
					rectype: ${jsonrpc.jsonutil.encode(childtype)},
					parent: ${jsonrpc.jsonutil.encode(name)}
				% endif
			})
		});	
	//]]>
	</script>

	</div>
	
</%def>
