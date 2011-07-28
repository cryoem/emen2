<?xml version="1.0" encoding="utf-8"?>
<%!
import jsonrpc.jsonutil
import time
import email.utils
from emen2.db.vartypes import parse_datetime
import xml.sax.saxutils

rfc822 = lambda x: email.utils.formatdate(time.mktime(parse_datetime(x)[0].timetuple()))
%>
<rss version="2.0"
   xmlns:content="http://purl.org/rss/1.0/modules/content/"
   xmlns:slash="http://purl.org/rss/1.0/modules/slash/">
  <channel>
	<title>${title}</title>
	<link>${ctxt.reverse('Home', _full=True)}</link>
	<description>EMEN2 record feed retrieved by modifytime</description>
	<lastBuildDate>${email.utils.formatdate()}</lastBuildDate>
   <language>en</language>
	<generator>http://blake.bcm.edu/emanwiki/EMEN2</generator>
	<docs>http://blake.bcm.edu/emanwiki/EMEN2</docs>
    %for item in items:
      <item>
        <title>${item.title}</title>
        <guid isPermaLink="false">${ctxt.reverse('Record', item.name, _full=True)}</guid>
        <pubDate>${rfc822(item.date)}</pubDate>
        <description>${item.title}</description>
        <content:encoded>
            <![CDATA[
               ${xml.sax.saxutils.escape(jsonrpc.jsonutil.encode(item.data))}
            ]]>
        </content:encoded>
        <slash:comments>${len(item.data.comments)}</slash:comments>
      </item>
    %endfor
  </channel>
</rss>
