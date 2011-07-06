<%inherit file="/page" />


<h1>
	${rec.get('wiki_page') | h}
	<span class="label"><a href="${EMEN2WEBROOT}/wiki/${rec.get('wiki_page') | u}/edit/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="Edit" /> Edit</a></span>
	</h1>

${rendered}


<p>Revised: ${rec.get('modifytime')} by ${displaynames.get(rec.get('modifyuser'), rec.get('modifyuser'))}</p>