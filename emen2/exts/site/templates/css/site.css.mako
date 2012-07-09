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
	color: #2C2C94;
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
#precontent > .e2-tree-main,
#precontent > .e2-alert-main,
#precontent > .e2-tab-main,
#content,
#content_inner,
.e2-tab-editbar > ul,
.e2-tab-editbar > div
{
/*	width: 1000px; */
	padding-left: 30px;
	padding-right: 30px;
	margin-left: auto;
	margin-right: auto;
}

/* Hide overflow in the parent map */
.e2-tree-main .e2-tree {
	overflow: hidden;
}


.e2-tab-editbar[data-tabgroup=query] > div {
	width: auto;
}
.e2-tree-main > .e2-tree {
	background: white;
	padding-top:4px;
	padding-bottom:4px;
	font-size: 10pt;
	-moz-border-radius: 8px;
	-webkit-border-radius: 8px;
	border-radius: 8px;

}
.e2l-narrow {

}
.e2-alert > li {
	-moz-border-radius: 8px;
	-webkit-border-radius: 8px;	
	border-radius: 8px;
}

.e2l-capsule {
	-moz-border-radius: 8px;
	-webkit-border-radius: 8px;	
	border-radius: 8px;
}

/* Basic layout */
#content {
	padding-top:10px;
	padding-bottom:100px;
	margin-bottom:100px;
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
	border-radius: 8px 8px 0px 0px;
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
	border-radius: 4px;

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

input[type=button]:hover,
input[type=submit]:hover,
button:hover,
.e2-button:hover {
	background: #fff;
	color:#666;
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

.e2l-disabled {
	color:#ccc;
}
input.e2l-save {
	
}
input.e2l-cancel {
	color: red;
}



/* tweaks */
.e2l-shaded-drop, 
.e2l-help
{
	border:solid 1px #ccc;
	background: #eee;
	padding: 10px;
	-moz-box-shadow: 3px 3px 3px #ddd;
	-webkit-box-shadow: 3px 3px 3px #ddd;
	box-shadow: 3px 3px 3px #ddd;
}
.e2l-help:before {
    content: "Help:";
    display: block; 
    clear: both; 
}

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
.e2l-shaded .e2l-gradient {
	border-top:10px solid white;
}

<%!
public = True
headers = {
	'Cache-Control': 'max-age=86400',
	'Content-Type': 'text/css'
}
%>
