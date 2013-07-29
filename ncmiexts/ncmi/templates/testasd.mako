<%!
public = True
%>
<%inherit file="/page" />


<%
params = DB.paramdef.filter()
users = DB.user.filter()
groups = DB.group.filter()
%>

Test! !@#

<h2>Groups:</h2>
<ul>
% for group in groups:
  <li>${group}</li>
% endfor
</ul>


