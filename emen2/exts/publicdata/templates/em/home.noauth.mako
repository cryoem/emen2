<%! 
import jsonrpc.jsonutil
import operator 
import collections
%>

<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 
<%namespace name="user_util" file="/pages/user"  /> 

<h1>Welcome to ${TITLE}</h1>


<p>    
    This database stores (or will store) the raw data and experimental records related to our various published structures. 
    We firmly believe that transparency is critical to scientific advancement, and when possible such data should be 
    available to anyone for development or testing purposes. We ask only that you contact us prior to using any 
    of this data in a new publication (wah@bcm.edu or sludtke@bcm.edu).
</p>

<p>
    The web pages you are currently viewing is the main interface for the EMEN2 (Electron Microscopy Electronic Notebook)
    database that we develop and use internally to store records of all experiments in the NCMI. This server is not our 
    main database, of course, but simply a clone of the portion of the data which has been released to the public. 
    The interface should be fairly simple to learn, but if you'd like a quick tutorial, just go to:
<p>


<ul>
    <li><a href="http://blake.bcm.edu/emanwiki/EMEN2/Public_Data_Server">Simple EMEN2 Tutorial</a></li>
</ul>

<p>
    Currently, data for the following projects is available. We will be adding more
    over the coming months:
</p>


<ul>
% for i in DB.getindexbyrectype('subproject'):
    <li><a href="${ctxt.root}/record/${i}">${DB.renderview(i)}</a></li>
% endfor
</ul>