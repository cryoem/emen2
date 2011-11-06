<%inherit file="/css/colors.css" />
<%block name="BODY">#BBDAEE</%block>

/***** Layouts *****/

/* body and top level containers */
html,
body
{
	font-family: arial, Verdana, Helvetica, sans-serif;
	margin:0px;
	padding:0px;
}

a, .e2l-a {
	color: #202060;
}

img {
	border: none;
}

h4 {
	margin-top: 5px;
	margin-bottom: 5px;
}
th,
td
{
	padding: 4px;
	vertical-align: top;
}
th {
	font-weight:normal;
	text-align:left;
	border-right:solid 1px <%self:LIGHTEST />;
}

ul {
	margin-top:0px;
}


/* Container elements: left-right margin */

#precontent {
	background: <%self:BODY />;
	padding-top: 10px;
}

#nav ul,
#precontent > .e2-map-main,
#precontent > .e2-alert-main,
#precontent > .e2-tab-main,
#content,
#rendered,
#e2-editbar-record > ul,
#e2-editbar-record > div
{
	width: 1000px;
	margin-left: auto;
	margin-right: auto;
}
.e2-map-main {
	background: white;
	padding: 4px;
	font-size: 10pt;
	-moz-border-radius: 8px;
	-webkit-border-radius: 8px;
}
.e2l-narrow {

}

/* Basic layout */
#content {
	padding:10px;
	padding-bottom:100px;
	margin-bottom:20px;
}

#footer {
	display:none;
}



/***** Nav bar *****/

#nav {
	background:white;
	margin:0px;
	border-bottom:solid 2px #ccc;
}
#nav > ul a {
	padding:8px;
}
#nav > ul li ul {
	padding:0px;
}
#nav > ul li:last-child ul {
	right:0px;
}
#nav #logo {
	height:36px;
}
#nav input {
	margin-top:4px;
	color: #666;
	font-weight: lighter;
}



/***** Main tabs ********/


.e2-tab-main > ul {
	margin-top:10px;
	border:none;
}

.e2-tab-main > ul > li {
	padding:4px;
	border:none;
	-moz-border-radius-topright: 8px;
	-moz-border-radius-topleft: 8px; 
	-webkit-border-top-right-radius: 8px;
	-webkit-border-top-left-radius: 8px;
}

/***** Input control Styling ********/

button,
select,
input,
textarea,
label
{
	border-width:1px;
	font-size:12pt;
	margin:4px;
	margin-left:0px;
	padding:2px;
	-moz-border-radius: 4px;
	-webkit-border-radius: 4px;
}

button, 
input[type=button],
input[type=submit],
input[type=file],
input[type=password],
input[type=text]
{
	display:inline-block;
}

textarea {
	margin: 0px;
	width: 100%;
    -webkit-box-sizing: border-box; /* Safari/Chrome, other WebKit */
    -moz-box-sizing: border-box;    /* Firefox, other Gecko */
    box-sizing: border-box;         /* Opera/IE 8+ */
}

textarea, 
input[type=text],
input[type=password]
{
	border:solid 1px #aaa;
}

input.e2l-save {
	color: white;
	border-color: #ccc;
	background: #5B74A8;
}
input.e2l-cancel {
	background-color: #eee;
	color: #666;
}





<%!
public = True
headers = {
	'Cache-Control': 'max-age=86400',
	'Content-Type': 'text/css'
}
%>
