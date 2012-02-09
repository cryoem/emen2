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

#nav > ul,
#precontent > .e2-map-main,
#precontent > .e2-alert-main,
#precontent > .e2-tab-main,
#content,
#content_inner,
#content_subview,
.e2-tab-editbar > ul,
.e2-tab-editbar > div
{
	width: 1000px;
	margin-left: auto;
	margin-right: auto;
}
.e2-tab-editbar[data-tabgroup=query] > div {
	width: auto;
}
.e2-map-main > .e2-map {
	background: white;
	padding-top:4px;
	padding-bottom:4px;
	font-size: 10pt;
	-moz-border-radius: 8px;
	-webkit-border-radius: 8px;
}
.e2l-narrow {

}
.e2-alert > li {
	-moz-border-radius: 8px;
	-webkit-border-radius: 8px;	
}

.e2l-capsule {
	-moz-border-radius: 8px;
	-webkit-border-radius: 8px;	
}

/* Basic layout */
#content {
	padding:10px;
	padding-bottom:100px;
	margin-bottom:20px;
}
#content_inner {
	margin-bottom:100px;
}
#content_inner input[type=submit] {
	font-size:18pt;
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

.e2-tab-editbar div.e2-tab-active {
	-moz-box-shadow: 3px 3px 3px #eee;
	-webkit-box-shadow: 3px 3px 3px #eee;
	box-shadow: 3px 3px 3px #eee;
}

/***** Input control Styling ********/

button,
select,
input,
textarea,
.e2-button
{
	-moz-border-radius: 4px;
	-webkit-border-radius: 4px;
	font-size:12pt;
	font-weight:normal;
	display:inline-block;
	margin: 4px;
	padding: 4px;
	background: #eee;
	color: #000;
	border:solid 1px #aaa;
	box-sizing:  content-box;
}
.e2-button img {
	margin: 0px;
	padding: 0px;
	vertical-align: middle;
}

input[type=text],
input[type=password],
input[type=email],
select,
textarea {
	background: white;
}

textarea {
	width: 100%;
    -webkit-box-sizing: border-box;
    -moz-box-sizing: border-box;
    box-sizing: border-box;
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



/* tweaks */
.e2-query-table th {
	border-right:solid 1px #eee;
}

.e2l-shaded th {
	border-bottom:none;
	border-right:solid 1px #999;
}
.e2l-shaded tr:last-child th {
	border-bottom:solid 1px #999;
	border-right:solid 1px #999;
}
.e2l-shaded th:last-child {
	border-right:none;
}


<%!
public = True
headers = {
	'Cache-Control': 'max-age=86400',
	'Content-Type': 'text/css'
}
%>
