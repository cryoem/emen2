<%! public = True %>
<%inherit file="/page" />

<h1>Test!</h1>

<form method="post">

<%
rendered = DB.view('137', viewname='mainview', options={'output':'newform', 'markdown':True})
%>

${rendered | n}

<p><input type="submit" value="Submit" /></p>

<script type="text/javascript">

bind_edit(document);

</script>