<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

<% 
import jsonrpc.jsonutil 
import operator
sortfunc = lambda x:rendered.get(x, '').lower()
lenfunc = lambda x:len(x[1])
import urllib
%>

<%call expr="buttons.pageswrap(pages)">

% for k,v in sortitems.items():

	<%call expr="buttons.pagewrap(pages,k)">

	##<h1>
	##	Projects, grouped by ${sortkey}: ${k}
	##</h1>

	<% order = map(recsdict.get, sorted(v, key=sortfunc)) %>

	<div class="outline">
		<ul>
		% for rec in order:
		 	<li><a href="#${rec.name}">${rendered.get(rec.name)}</a></li>
		% endfor
		</ul>
	</div>

	% for rec in order:
		<h1 id="${rec.name}">
			${rendered.get(rec.name)}
			<span class="label"><a href="${EMEN2WEBROOT}/query/children.name.${rec.name}*/"><img src="${EMEN2WEBROOT}/static/images/query.png" alt="Query" /> Query</a></span>			
			<span class="label"><a href="${EMEN2WEBROOT}/record/${rec.name}/edit/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> Edit</a></span>			
		</h1>


		% if rec.get('project_status') or rec.get('project_block'):
		<p>
			Project Status: ${rec.get('project_status')} <br />
			Driving Person: ${rec.get('project_block')}
		</p>
		% endif


		
		% if details.get(rec.name, dict()).get('grouped', dict()):
			<table>
				<thead>
					<th style="width:100px">Protocol</th>
					<th style="width:100px">Count</th>
					<th style="width:100px">Most Recent</th>
					<th style="width:200px"></th>
				</thead>
				<tbody>
				
				% for k2,v2 in sorted(details.get(rec.name, dict()).get('grouped', dict()).items(), key=lenfunc, reverse=True):
					<% mostrecent = details.get(rec.name, dict()).get('mostrecent', dict()).get(k2) %>
					<tr>
						<td><a href="${EMEN2WEBROOT}/query/children.name.${rec.name}*/rectype==${k2}/">${k2}</td>
						<td>${len(v2)}</td>
						<td><a href="${EMEN2WEBROOT}/record/${mostrecent}/">${recsdict.get(mostrecent, dict()).get('creationtime')}</a></td>
						<td><a href="${EMEN2WEBROOT}/record/${mostrecent}/">${rendered.get(mostrecent)}</a></td>
					</tr>
				% endfor

				</tbody>
			</table>
		% else:
			<p>No child records</p>
		% endif
		
		
	% endfor

	</%call>

% endfor

</%call>
