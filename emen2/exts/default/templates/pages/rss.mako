<%! import jsonrpc.jsonutil 
%><?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
	<title>${title}</title>
	<link>http://localhost:65535/</link>
	<description>Random RSS stuff</description>
	<lastBuildDate>Fri, 05 Jun 2009 16:58:21 GMT</lastBuildDate>
	<generator>EMEN2 w/ Mako</generator>
	<docs>http://ncmi.bcm.edu/software</docs>
    %for item in items:
      <item>
        <title>${item.title}</title>
        <description>${jsonrpc.jsonutil.encode(item.data) | h}</description>
        <guid isPermaLink="true">${ctxt.reverse('Record', item.name, _full=True)}</guid>
        <pubDate>${item.date}</pubDate>
      </item>
    %endfor
  </channel>
</rss>
