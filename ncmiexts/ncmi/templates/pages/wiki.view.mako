<%inherit file="/page" />


<h1>
    ${rec.get('wiki_page') | h}
    <span class="e2l-label"><a href="${ctxt.root}/wiki/${rec.get('wiki_page') | u}/edit/"><img src="${ctxt.root}/static/images/edit.png" alt="Edit" /> Edit</a></span>
    </h1>

${rendered}


<p>Revised: ${rec.get('modifytime')} by ${displaynames.get(rec.get('modifyuser'), rec.get('modifyuser'))}</p>