<%inherit file="/page" />

<%!  public=True %>
<%def name="mimetype()">text/html; encoding=UTF-8</%def>

<%def name="head()">
   <style type="text/css">
      #zone_login {
         display: inline-block;
         border: thin solid black;
         margin: auto;
         text-align: left !important;
      }

   </style>
   ${parent.head()}
</%def>

<h1>${title}</h1>

<div style="text-align: center;color: red;font-style: italic;padding-bottom:1em">${err.msg | h}</div>

%if err.code in set([401, 403]):
   <%namespace name="login" file="/auth/login" />  
   <div style="width:100%;position: relative; text-align:center">
      <div>
         ${login.login(action_login, location=reverseinfo, user=user, errmsg=errmsg, logintext='', defaultname="")}
      </div>
   </div>
%endif
