<%inherit file="/css/colors.css" />

table.e2l-shaded tbody tr:nth-of-type(odd) {
	background: <%self:LIGHTEST />;
}

th {
	font-weight:normal;
	text-align:left;
	border-right:solid 1px <%self:LIGHTEST />;
}


/***** Layouts *****/

/* body and top level containers */
html,
body
{
	font-family: arial, Verdana, Helvetica, sans-serif;
	margin:0px;
	padding:0px;
	background: <%self:BODY />
}

/* Title and precontent set a background color */
#container {
	width:1000px;
	margin-left:auto;
	margin-right:auto;
}
#title {
	width:auto;
	margin-left:0px;
	margin-right:0px;
}
#content {
    -webkit-box-sizing: border-box; /* Safari/Chrome, other WebKit */
    -moz-box-sizing: border-box;    /* Firefox, other Gecko */
    box-sizing: border-box;         /* Opera/IE 8+ */
	padding:10px;
	padding-bottom:100px;
	margin-bottom:20px;
}
#footer {
	display:none;
}



/******* TOP LEVEL ELEMENTS *******/

img {
	border: none;
}

h4 {
	margin-top: 5px;
	margin-bottom: 5px;
}
h1 .e2l-label {
	padding: 10px;
	float: right;
	display: block;
}
th,
td
{
	padding: 4px;
	vertical-align: top;
}


/************* NAV BAR ************/

#title {
	border-bottom:solid 1px #ccc;
}
#nav {
	padding:8px;
}
#nav a {
	padding:8px;
}
#nav li ul {
	padding:0px;
}
#nav li.divider {
	border-top:solid 1px #ccc;
}
#nav li:last-child ul {
	right:0px;
}
#nav .logo {
	height:36px;
}
#nav input {
	margin-top:4px;
	color: #666;
	font-weight: lighter;
}



/***** tweaks ********/

table ul {
	margin:0px;
	padding:0px;
	list-style:none;
}


/***** Control Styling ********/

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
