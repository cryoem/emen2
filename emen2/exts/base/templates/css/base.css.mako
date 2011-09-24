<%inherit file="/css/colors.css" />

/***
Non-prefixed classes:
	show
	hide
	clickable
	editable
	label
	save
	big
	small
	add
	remove
***/

/* Basic table behavior */
table {
	width:100%;
}

/* Basic show/hide behavior */
.show {
	display: block;
}

.hide {
	display: none;
}

/* Basic text size */
.small {
	font-size: 10pt;
}
.big {
	font-size:16pt;
}

/* Basic editable indicators */
.editable {
	color: <%self:EDITABLE />;
}
.editable img.label {
	height: 10px;
	border-bottom: dotted 1px <%self:NEUTRAL />;
	width: 50px;
}

/* Commit button */
.save {
	
}

/* Basic link styling */
a,
.clickable
{
	color: <%self:LINK />;
	text-decoration: none;
	cursor: pointer;
}
a:hover,
.clickable:hover
{
	text-decoration: underline;
}


/******************************************
 		Basic EMEN2 Layouts
******************************************/

.e2l-thumbnail {
	height:64px;
}


.e2l-edit {
	display:inline-block;
}

.e2l-fw {
	display:block;
	width:100%;
}

.e2l-searchbox { 
	padding-bottom: 10px;
	margin-bottom: 10px;
	border-bottom: solid 1px #ccc;
}

.e2l-unselect {
	-webkit-user-select: none;
	-moz-user-select: none;	
}


/***** e2l-menu: Drop-down menu *****/

.e2l-menu > li {
	position: relative;
}
.e2l-menu > li > a,
.e2l-menu > li > .clickable,
.e2l-menu ul > li > a
 {
	padding: 5px;
	display: block;
}
.e2l-menu > li > ul,
.e2l-menu .e2l-menu-hidden
{
	list-style: none;
	position: absolute;
	display: none;
	width: 250px;
	padding:10px;
	z-index:200;
	background:white;
}
.e2l-menu img {
	vertical-align: bottom;
	margin: 0px;
}
.e2l-menu > li:hover > ul
{
	display: block;
}


/***** e2l-alert: Alerts, notifications, and errors *****/

.e2l-alert > li {
	border: solid 2px <%self:ADDED />;
	padding: 5px;
	margin-bottom:10px;
}
.e2l-alert > li.e2l-error {
	border: solid 2px <%self:REMOVED />;
}


/***** e2l-controls: Control boxes *****/

.e2l-controls {
	float:right;
}



/***** e2l-spinner: Progress indicator *****/

.e2l-spinner {
	
}


/***** e2l-tab: Page and tab widget *****/

.e2l-tab-pages > .e2l-tab-page {
	border: solid 1px #ccc;
	display: none;
	padding: 10px;
}
.e2l-tab-pages > .e2l-tab-active {
	display: block;
}
.e2l-tab-buttons > .e2l-tab-button {
	padding: 8px;
	margin-top: 10px;
	margin-right: 10px; 
	background: #ccc;
	border-bottom: solid 1px #ccc;
}
.e2l-tab-buttons > .e2l-tab-active {
	background: none;
	border: solid 1px #ccc;
	border-bottom: none;
	outline: solid 1px white;
}
/* should these be in base template? */
.e2l-tab-page > p {
	margin-top:0px;
}


/***** e2l-float: Floating items *****/

.e2l-float-left {
	float:left !important;
}
.e2l-float-right {
	float:right !important;
}
.e2l-float-list {
	list-style:none;
	padding-left:0px;
	margin-top:0px;
	margin-bottom:0px;
}
.e2l-float-list > li {
	float:left;
}
.e2l-nonlist {
	list-style: none;
	padding-left: 0px;
}


/***** e2l-clearfix: Correct wrapping around floating elements *****/

.e2l-clearfix {
	clear:both;
}
.e2l-clearfix:after {
    content: "."; 
    display: block; 
    height: 0; 
    clear: both; 
    visibility: hidden;	
}


/*** e2l-editbar: Editing bar *****/

.e2l-editbar {
	background-image: -moz-linear-gradient(#fff, #fff, #eee);
	border-bottom:solid 1px #ccc;
}
.e2l-editbar > li {
	position:relative;
	border-right:solid 1px #ccc;
}
.e2l-editbar > li.e2l-editbar-lastitem {
	border-right:none;
}
.e2l-editbar > li > .label {
	padding:5px;
	display:inline-block;
}
/*.editbar input, 
.editbar select
{
	font-size: 10pt;
	padding: 2px;
	margin: 2px;
	margin-right: 4px;
	margin-left: 4px;
}
*/




/******************************************
 		EMEN2 Widgets
******************************************/


/***** e2-infobox: Display Infobox *****/

.e2-infobox {
	position:relative;
	border-bottom:solid 1px #ddd;
	width:350px;
	padding:5px;
	padding-left:0px;
	padding-right:0px;
}
.e2-infobox h4 {
	margin-top:0px;
	margin-left: 50px;
	font-size:10pt;
	border-bottom: none;
}
.e2-infobox p {
	margin:0px;
	margin-left: 50px;
}
.e2-infobox img.e2l-thumbnail {
	float: left;
	height: 40px;
	margin-right: 4px;
}
/* Infobox in the permissions widget floats
to fit more information */
.e2-permissions-level .e2-infobox {
	float:left;
}


/***** e2-wordcount: Wordcount widget *****/

.e2-wordcount-count {
	text-align:right;
	padding-top:10px;
	padding-bottom:10px;
}
.e2-wordcount-error {
	color:<%self:REMOVED />;
}


/***** e2-siblings: Sibling relationship widget *****/

.e2-siblings h1 {
	margin-bottom:10px;
}
.e2-siblings li {
	margin-left:10px;
	list-style-type:none;
}
.e2-siblings li.e2-siblings-active {
	list-style-type:disc;
}



/***** e2-map: Relationship Map *****/

/* total width per item should be 249px */
/* Nested lists */
.e2-map.e2-map-children ul {
	padding-left:0px;
	margin-left:249px;	
}
.e2-map.e2-map-parents ul {
	padding-left:0px;
	margin-left:-249px;	
	/* text-align:right; */
}

/* List items */
.e2-map li {
	list-style:none;
	padding-bottom:4px;
	position:relative;	
	width:249px;
}

.e2-map ul li a {
	top:0px;
	z-index:100;
	display:block;
	margin-left:16px;
	margin-right:16px;
}
.e2-map.e2-map-parents ul li a.draggable {
	text-align:right;
}

.e2-map img.e2-map-expand {
	z-index:101;
	position:absolute;
	top:0px;
}
.e2-map.e2-map-children img.e2-map-expand {
	right:0px;	
}
.e2-map.e2-map-parents img.e2-map-expand {
	left:0px;	
}

/* root element */

.e2-map ul:first-child {
	margin-left:0px;
}

.e2-map.e2-map-parents ul:first-child {
	float:right;
}

.e2-map-hover {
	background:orange;
	padding:0px;
}

/* Backgrounds */
.e2-map.e2-map-children li {
	background:url('${EMEN2WEBROOT}/static/images/bg-F.children.png') repeat-y;	
}
.e2-map.e2-map-parents li {
	background:url('${EMEN2WEBROOT}/static/images/bg-F.parents.png') repeat-y;	
	background-position:top right;	
}
.e2-map.e2-map-children li:first-child {
	background:url('${EMEN2WEBROOT}/static/images/bg-T.children.png') repeat-y;	
}
.e2-map.e2-map-parents li:first-child {
	background:url('${EMEN2WEBROOT}/static/images/bg-T.parents.png') repeat-y;	
	background-position:top right;
}
.e2-map.e2-map-children li:last-child {
	background:url('${EMEN2WEBROOT}/static/images/bg-L.children.png') no-repeat;
}
.e2-map.e2-map-parents li:last-child {
	background:url('${EMEN2WEBROOT}/static/images/bg-L.parents.png') no-repeat;
	background-position:top right;
}
.e2-map.e2-map-children ul li:only-child {
	background:url('${EMEN2WEBROOT}/static/images/bg--.children.png') no-repeat;
}
.e2-map.e2-map-parents ul li:only-child {
	background:url('${EMEN2WEBROOT}/static/images/bg--.parents.png') no-repeat;
	background-position:top right;
}
.e2-map:first-child > ul:first-child > li:first-child {
	background:none
}




/***** jQuery UI Overrides *****/

.ui-autocomplete {
	max-width: 300px;
	max-height: 300px;
	overflow-y: auto;
}
/* IE 6 doesn't support max-height
 * we use height instead, but this forces the menu to always be this tall
 */
* html .ui-autocomplete {
	height: 300px;
}

<%!
public = True
headers = {
	'Cache-Control': 'max-age=86400',
	'Content-Type': 'text/css'
}
%>
