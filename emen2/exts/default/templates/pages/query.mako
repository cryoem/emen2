<%! import jsonrpc.jsonutil %>

<%def name="table(q, create=False, name=None, childtype=None, qc=True)">

	<script type="text/javascript">
	//<![CDATA[
		$(document).ready(function() {
			$(".e2-query").TableControl({
				q: ${jsonrpc.jsonutil.encode(q)}, 
				% if create:
					rectype: ${jsonrpc.jsonutil.encode(childtype)},
					parent: ${jsonrpc.jsonutil.encode(name)}
				% endif
			})
		});	
	//]]>
	</script>

	<div class="e2-query">

		<ul class="e2l-menu e2l-clearfix e2l-editbar e2-query-header">
		</ul>
		
		<table class="e2-query-table e2l-shaded" cellspacing="0" cellpadding="0"> 
			<thead>
			
				<th>
					<input type="checkbox" />
				</th>
				
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
					
					<td>
						<input type="checkbox" data-name="${name}" />
					</td>
					
										
					% for v in q['table'].get(name, []):
						<td>${v}</td>
					% endfor
					</tr>
				% endfor			
			</tbody>

		</table>
	</div>
	
</%def>

${table(q)}










