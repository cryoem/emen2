<%inherit file="/pages/record" />
<%namespace name="table" file="/pages/table"  /> 

% if not q.get('names'):
	<div id="rendered">
		No Records found for this query.
	</div>
% else:
	${table.table(q, childtype=childtype, name=name, create=create)}
% endif