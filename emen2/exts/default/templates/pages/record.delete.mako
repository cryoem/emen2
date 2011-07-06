<%inherit file="/page" />


<div>

	% if commit:

		<p>Record ${name} deleted. ${len(orphans)} orphaned child records.</p>
		
		<p>
		<a href="${EMEN2WEBROOT}/home/">Home</a>
		<p>
		</p>
	
	% else:

		<p>Delete this record?</p>

		<form action="" method="post">
			<input type="submit" value="Delete Record" />
			<input type="hidden" name="commit" value="True" />
		</form>

		<p>${len(orphans)} Records will be orphaned: <br />

		<ul>

			<%
			import operator
			sorted_orphans = [ j[0] for j in sorted( [ (i, recnames.get(i,"")) for i in orphans ], key=operator.itemgetter(1) ) ]
			%>

			% for i in sorted_orphans:
				<li><a href="${EMEN2WEBROOT}/record/${i}">${recnames.get(i)} (${i})</a></li>
			% endfor
		</ul>

		<p>(e.g. they will not have a valid path to the root node)</p>

		</p>

	% endif
	
</div>

