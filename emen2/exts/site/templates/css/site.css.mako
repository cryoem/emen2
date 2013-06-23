<%inherit file="/css/colors.css" />
<%block name="BODY">#BBDAEE</%block>

/***** Layouts *****/

p {
    margin-top:10px;
    margin-bottom: 10px;
}

table {
    width: 100%;
    border-spacing:0;
    border-collapse:collapse;
}

/* Paragraphs and uls have an irritating default margin */
ol, ul {
    padding-left:20px;
}

h1, h2, h3, h4 {
    font-size:16pt;
    position:relative;
    border-bottom: solid 1px #ccc;
    margin-top:10px;
    margin-bottom:10px;
}
h3, h4 {
    font-size: 12pt;
}

/* body and top level containers */
html,
body
{
    margin:0px;
    padding:0px;
}

html,
body,
input,
select,
textarea {
    font-family: arial, Verdana, Helvetica, sans-serif;
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

#navigation > ul,
#precontent > .e2-tree-main,
#precontent > .e2-alert-main,
#precontent > .e2-tab-main,
#content
{
    padding-left: 30px;
    padding-right: 30px;
    margin-left: auto;
    margin-right: auto;
}

/* Hide overflow in the parent map */
.e2-tree-main .e2-tree {
    overflow: hidden;
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

#navigation {
    background:white;
    margin:0px;
    border-bottom:solid 2px #ccc;
}
#navigation > ul a {
    padding:8px;
}
#navigation > ul li ul {
    padding:0px;
}
#navigation > ul li:last-child ul {
    right:0px;
}
#navigation #logo {
    height:36px;
}
#navigation input {
    margin-top:4px;
    color: #666;
    font-weight: lighter;
}


/***** Editbar ******/
/* Linear gradient... */
.e2l-gradient,
.e2-tab-query[role=tablist] {
    border-bottom: solid 1px #ccc;
    background: -moz-linear-gradient(top, rgba(255,255,255,0) 0%, rgba(0,0,0,0.1) 100%);
    background: -webkit-gradient(linear, left top, left bottom, color-stop(0%,rgba(255,255,255,0)), color-stop(100%,rgba(0,0,0,0.1)));
    background: -webkit-linear-gradient(top, rgba(255,255,255,0) 0%,rgba(0,0,0,0.1) 100%);
    background: -o-linear-gradient(top, rgba(255,255,255,0) 0%,rgba(0,0,0,0.1) 100%);
    background: -ms-linear-gradient(top, rgba(255,255,255,0) 0%,rgba(0,0,0,0.1) 100%);
    background: linear-gradient(top, rgba(255,255,255,0) 0%,rgba(0,0,0,0.1) 100%);
}
.e2-tab-query > ul > li {
    padding:10px;
}
.e2-tab-query > ul > li > input,
.e2-tab-query > ul > li > form > input,
.e2-tab-query > ul > li > select {
    font-size:12pt;
    padding:2px;
    margin:0px;
    margin-top:-4px;
    margin-bottom:-4px;
}

/*.e2-tab-query > ul > li {
    border-right: solid 1px #ccc;
    margin-bottom:-1px;
}
.e2-tab-query > ul > li.e2l-float-right {
    border-left: solid 1px #ccc;
    border-right: none;
}
.e2-tab-query > ul input,
.e2-tab-query > ul select {
    font-size: 10pt;
    margin: 0px;
    padding-top: 1px;
    padding-bottom: 1px;
    padding-left: 3px;
    padding-right: 3px;
    
}
.e2-tab-query > * {
    padding:10px;
    border: solid 1px #ccc;
    border-top: none;
}
.e2-tab-editbar li.e2-tab-active {
    background: #f4f4f4;
}
.e2-tab-editbar div.e2-tab-active {
    display: block;
    background: #f4f4f4;
}
*/

/***** Main tabs ********/

.e2-tab-main > ul {
    margin-top:10px;
    border:none;
}

.e2-tab-main > ul > li {
    padding:8px;
    border:none;
    -moz-border-radius-topright: 8px;
    -moz-border-radius-topleft: 8px; 
    -webkit-border-top-right-radius: 8px;
    -webkit-border-top-left-radius: 8px;
    border-radius: 8px 8px 0px 0px;
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
    font-size: 12pt;
    font-weight: normal;
    display: inline-block;
    margin: 0px;
    margin-right:4px;
    margin-bottom:4px;
    padding: 4px;
    background: #eee;
    color: #000;
    border:solid 1px #aaa;
    box-sizing: content-box;
}

h1 .e2l-actions button,
h1 .e2l-actions input,
h1 .e2l-actions .e2-button {
    margin-top:-10px;
    margin-left:10px;
}
h1 label {
    font-weight: normal;
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
.e2l-help {
    display:block;
}
.e2l-help:before {
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
