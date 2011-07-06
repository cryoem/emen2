<%inherit file="/page" />
<%namespace name="record_history" file="/pages/record.history"  /> 


% if revision == None:
	
	<h1>Revision History for <a href="${EMEN2WEBROOT}/record/${rec.name}/">${renderedrecname}</a></h1>

% else:

	<h1>
		Revision ${revision} for <a href="${EMEN2WEBROOT}/record/${rec.name}/">${renderedrecname}</a>
		<span class="label">
			<a href="${EMEN2WEBROOT}/record/${rec.name}/history/">All Revisions</a>
		</span>
	</h1>

% endif

${record_history.revisiontable(rec)}

<br /><br />

% if revision != None:

##	<div class="clearfix"><div class="infobuttons">Revision: ${revision}</div></div>
##	<div class="info">
##	${rendered}
##	</div>

% endif






