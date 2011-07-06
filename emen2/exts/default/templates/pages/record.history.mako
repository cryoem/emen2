<%def name="revisiontable(rec)">

	<%
	import collections
	import operator
	import cgi
	revs, _p = rec.revision(revision)
	revcount = len(revs)
	%>

	<table cellspacing="0" cellpadding="0" class="shaded">
		<thead>
			% if revision == None:
				<th>Date</th>
				<th>User</th>
			% endif
		
			<th>Parameter</th>
			<th>Old Value</th>
		</thead>
	
		<tbody>

			% for revid, t in enumerate(sorted(revs.keys(), reverse=True)):			

				% if revision == None or (revision != None and revision == t):
				
					% for count, (user, param, value) in enumerate(sorted(revs.get(t,[]), key=operator.itemgetter(1))):

						<tr>
						
							% if revision == None:
								% if count == 0:
									<td><a href="${EMEN2WEBROOT}/record/${rec.name}/history/${t.replace(" ", "+")}">${t}</td>
									<td><a href="${EMEN2WEBROOT}/user/${user}/">${displaynames.get(user, user)}</a></td>
								% else:
									<td/>
									<td/>
								% endif
							% endif

							% if param == None:
								<td colspan="2"><strong>Comment:</strong> ${value|h}</td>
							% else:
								<td>${param}</td>
								<td>
									% if simple and len(unicode(value)) > 50:
										${cgi.escape(unicode(value))[:50]} ...&raquo;
									% else:
										${cgi.escape(unicode(value))}
									% endif						
								</td>						
							% endif	
							
						</tr>

					% endfor
				% endif
			% endfor


		</tbody>
	</table>

</%def>


<p><a href="${EMEN2WEBROOT}/record/${rec.name}/history/">View complete history</a></p>


<!-- if called bare -->

${revisiontable(rec)}









