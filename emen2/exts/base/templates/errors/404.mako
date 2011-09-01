<%inherit file="/page" />

<%!  public=True %>
<%def name="mimetype()">text/html; encoding=UTF-8</%def>

<%def name="title()">Page Not Found</%def>

<h1>The page you have requested cannot be found.</h1>

The requested URL ${msg | h} was not found on this server.
