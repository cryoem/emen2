<%! import jsonrpc.jsonutil %>

<%def name="table(q, create=False, name=None, childtype=None, qc=True)">
	<script type="text/javascript">
	//<![CDATA[
		var q = ${jsonrpc.jsonutil.encode(q)};
		$(document).ready(function() {
			$(".e2-query").TableControl({
				q: q, 
				% if create:
					rectype: ${jsonrpc.jsonutil.encode(childtype)},
					parent: ${jsonrpc.jsonutil.encode(name)}
				% endif
			})
		});	
	//]]>
	</script>

	<div class="e2-query">

		<div class="e2-tab e2-tab-editbar" data-tabgroup="query" role="tab">
			<ul class="e2-query-header e2l-cf" role="tablist"></ul>
		</div>
		<div class="e2-tab e2-tab-editbar" data-tabgroup="query" role="tabpanel"></div>


		## This form is used for editing table cells
		<form class="e2-query-tableform" method="post" action="${ctxt.reverse('Records/edit')}">
			<input type="hidden" name="_location" value="${REQUEST_LOCATION}" />
		
			<table class="e2-query-table e2l-shaded" cellspacing="0" cellpadding="0"> 
				<thead>
			
					## <th>
					##	<input type="checkbox" />
					## </th>
				
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
					
						## <td>
						## 	<input type="checkbox" data-name="${name}" />
						## </td>
										
						% for v in q['table'].get(name, []):
							<td>${v}</td>
						% endfor
						</tr>
					% endfor			
				</tbody>

			</table>
		
		</form>
		
	</div>
	
</%def>

${table(q)}










