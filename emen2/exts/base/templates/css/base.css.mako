<%inherit file="/css/colors.css" />

/* Set some default font and margins. */
body {
	font-family: sans-serif;
}

table {
	width: 100%;
}

/* Paragraphs and uls have an irritating default margin */
ul {
	margin-top: 0px;
	margin-bottom: 0px;
}

/******************************************
 		Basic EMEN2 Layouts

Please note that all EMEN2 classes should
begin with one of the following prefixes:

	.e2l 	Layout classes
	.e2		Widget classes

******************************************/


/***** Layout Styles *****/
/* 
	These are styles that are 
	not part of a particular widget
*/

/* Basic link styling */
a,
.e2l-a
{
	color: #0000EE; /* <%self:LINK />; */
	text-decoration: none;
	cursor: pointer;
}

a:hover,
.e2l-a:hover
{
	text-decoration: underline;
}

/* Commit button */
.e2l-thumbnail {
	vertical-align: top;
	max-height:64px;
	max-width:64px;
}
.e2l-thumbnail-mainprofile {
	max-height: 256px;
	max-width: 256px;
}
/* Basic text size */
.e2l-small {
	font-size: 10pt;
}
.e2l-big {
	font-size:20pt;
}

/* Basic show/hide behavior */
.e2l-show {
	display: block;
}

.e2l-hide {
	display: none;
}

/* Full width */
.e2l-fw {
	width:100% !important;
}

/* Unselectable elements */
.e2l-a,
.e2l-unselect,
.e2-infobox h4
{
	-webkit-user-select: none;
	-moz-user-select: none;	
}

/* I often show actions along 
	the right side of a header */

ul.e2l-actions {
	list-style: none;
	font-size:12pt;
	float: right;
}
ul.e2l-actions li {
	float: right;
}

/* e2-alert: Alerts, notifications, and errors */
.e2-alert {
	list-style: none;
	padding-left: 0px;
}
.e2-alert > li {
	list-style: none;
	padding-left: 0px;
	border: solid 2px <%self:ALERT />;
	background: white;
	padding: 5px;
	margin-bottom:10px;
}

input.e2l-error, 
.e2-alert > li.e2l-error
{
	border: solid 2px <%self:REMOVED />;
}

a.e2l-capsule {
	padding:4px;
	border:solid 2px #ccc;
	background: #eee;
}

.e2l-nonlist {
	list-style:none;
	padding-left:0px;
}

/* e2l-controls: Control boxes */
.e2l-options, 
.e2l-advanced,
.e2l-controls
{
	list-style: none;
	clear: both;
	float: right;
	margin: 0px;
	margin-top: 10px;
	margin-bottom:50px;
	padding: 0px;
}
/*.e2l-advanced, 
.e2l-options
{
	font-size:10pt;
}
*/

/* e2l-spinner: Activity indicator */

/* This is usually just drawn with an inline-style
		display:none
	and displayed/hidden with jQuery.show()/hide()/toggle() */
.e2l-spinner {
}

/* e2l-float: Floating items */
.e2l-float-left {
	float:left !important;
}
.e2l-float-right {
	float:right !important;
}

/* e2l-cf: "Clearfix", for correct wrapping around floating elements */
.e2l-cf {
	clear:both;
}
.e2l-cf:after {
    content: "."; 
    display: block; 
    height: 0; 
    clear: both; 
    visibility: hidden;	
}

/* e2l-shaded: Alternating row colors */
table.e2l-shaded tbody tr:nth-of-type(odd) {
	background: #eee;
}
/* e2l-kv: Simple two column tables */
table.e2l-kv td:first-child {
	vertical-align: top;
	width:250px;
}
table.e2l-shaded tr.e2l-shaded-header {
	background: #BBDAEE !important;
}
table.e2l-shaded tr.e2l-shaded-indent td:first-child {
	padding-left: 40px;
}



/***** These should go in style.css *****/

h1,
h4
{
	border-bottom: solid 1px #ccc;
}

/* e2l-menu: Navigation */
.e2l-menu {
	list-style:none;
	padding-left: 0px;
}
.e2l-menu > li {
	float: left;
	position: relative;
}
.e2l-menu > li > a,
.e2l-menu > li > .e2l-a,
.e2l-menu ul > li > a
 {
	padding: 5px;
	display: block;
}
.e2l-menu > li > ul {
	list-style:none;
}
.e2l-menu > .e2l-hover {
	background:white;
}
.e2l-menu > li > ul,
.e2l-menu .e2l-menu-hidden
{
	position: absolute;
	display: none;
	width: 250px;
	padding:10px;
	z-index:200;
	background:white;
	border: solid 1px #ccc;
	border-top: none;
}
.e2l-menu-divider {
	border-top:solid 1px #ccc;
}
.e2l-menu img {
	vertical-align: bottom;
	margin: 0px;
}
.e2l-menu > li:hover > ul
{
	display: block;
}





/******************************************
 		EMEN2 Widgets
******************************************/

/***** e2-tab: Tab/page switch. Similar to jQuery.tab *****/
.e2-tab {
	position:relative;
	clear:both;
}
.e2-tab > ul {
	padding-left: 0px;
	list-style: none;
	margin:0px;
}
.e2-tab > ul > li {
	float: left;
}
.e2-tab > ul > li img {
	vertical-align:middle;
}
.e2-tab > ul > li > a,
.e2-tab > ul > li > span
{
	display:inline-block;
	padding:5px;
}
.e2-tab > div {
	display:none;
	z-index: 1000;
}
.e2-tab li.e2-tab-active {	
}
.e2-tab div.e2-tab-active {
	display:block;
}
/* e2l-shaded is the same background as .e2-tab... */
.e2-tab-active table.e2l-shaded {
	background: white;
}



/* e2-switcher: Simple tab widget */
.e2-tab-switcher {
	margin-bottom:20px;
}
.e2-tab-switcher > ul > li {
	border: solid 1px #ccc;
	border-bottom: none;
	padding:10px;
	margin-right: 15px;
	margin-bottom: -1px;
}
.e2-tab-switcher > div {
	border: solid 1px #ccc;
	padding: 10px;
	background: #eee;
}
.e2-tab-switcher li.e2-tab-active {
	padding:10px;
	background: #eee;
}


/* e2-tab-main: Page layout level tabs */
.e2-tab-main > ul {
	border-bottom:solid 1px #ccc;
}
.e2-tab-main > ul > li {
	background: #eee;
	border: solid 1px #ccc;
	margin-right: 15px;
	margin-bottom: -1px;
}
.e2-tab-main li.e2-tab-active {
	border-bottom: solid 1px white;
	background: white;
}


/* Linear gradient... */
/* e2-tab-editbar: Editing Bar */
.e2l-gradient,
.e2-tab-editbar[role=tab] {
	border-bottom: solid 1px #ccc;
	/* background-image: -moz-linear-gradient(#fff, #fff, #eee); */
	background: -moz-linear-gradient(top, rgba(255,255,255,0) 0%, rgba(0,0,0,0.1) 100%);
	background: -webkit-gradient(linear, left top, left bottom, color-stop(0%,rgba(255,255,255,0)), color-stop(100%,rgba(0,0,0,0.1)));
	background: -webkit-linear-gradient(top, rgba(255,255,255,0) 0%,rgba(0,0,0,0.1) 100%);
	background: -o-linear-gradient(top, rgba(255,255,255,0) 0%,rgba(0,0,0,0.1) 100%);
	background: -ms-linear-gradient(top, rgba(255,255,255,0) 0%,rgba(0,0,0,0.1) 100%);
	background: linear-gradient(top, rgba(255,255,255,0) 0%,rgba(0,0,0,0.1) 100%);
}
.e2-tab-editbar > ul > li {
	border-right: solid 1px #ccc;
	margin-bottom:-1px;
}
.e2-tab-editbar > ul > li.e2l-float-right {
	border-left: solid 1px #ccc;
	border-right: none;
}
.e2-tab-editbar > ul input,
.e2-tab-editbar > ul select {
	font-size: 10pt;
/*	vertical-align: top;*/
/*	margin-top: -2px; */	
	margin: 0px;
	padding-top: 1px;
	padding-bottom: 1px;
	padding-left: 3px;
	padding-right: 3px;
	
}
.e2-tab-editbar > div {
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


/***** e2l-edit: Editing controls *****/
.e2-edit {
	color: <%self:EDITABLE />;
}
.e2-edit img.e2l-label {
	height: 10px;
	border-bottom: dotted 1px <%self:NEUTRAL />;
	width: 50px;
}
/* Editable items */
.e2-edit-widget {
	display:inline-block;
}
.e2-edit-containers {
	list-style: none;
}
.e2l-help {
	display:none;
}

/***** e2-upload: Upload Control *****/
.e2-upload-table td {
	height: 32px;
}
.e2-upload-action {
	padding-left: 4px;
	padding-right: 4px;
}
/***** e2-query: Query Results *****/
.e2-query table.e2-query-table {
/*	table-layout: fixed; */
}
/*.e2-query table.e2-query-table th {
	font-weight: bold;
}*/
.e2-query .e2-query-sort th,
.e2-query .e2-query-sort button {
	padding: 2px;
}
.e2-query .e2-query-table ul {
	list-style: none;
	padding-left: 0px;
}
.e2-query .e2-query-table li {
	margin-right:10px;
}
.e2-query-extraspacing span {
	padding-right: 5px;
	padding-left: 5px;
}


/***** e2-find: Find popup *****/
/* Search box */
.e2-find-searchbox { 
	padding-bottom: 10px;
	margin-bottom: 10px;
	border-bottom: solid 1px #ccc;
}


/***** e2-infobox: Display Infobox *****/
.e2-infobox {
	float:left;
	position:relative;
	width:280px;
	margin-right:50px;
	padding:5px;
	padding-left:0px;
	padding-right:0px;
	border-bottom:solid 1px #ddd;
}
.e2-infobox h4 {
/*	white-space:nowrap;
	overflow-x: hidden;
*/	border-bottom: none;
	margin-top: 0px;
	margin-bottom: 5px;
	font-weight:normal;
	font-size:12pt;
}
.e2-infobox > div {
	margin:0px;
	margin-left: 50px;
}
.e2-infobox-input {
	float: left;
	margin:10px;
	margin-left:0px;
}
.e2-infobox img.e2l-thumbnail {
	float: left;
	height: 32px;
	width: 32px;
	margin-right: 4px;
}
.e2-infobox-hover {
}

.e2-infobox-selected {
	background: <%self:ADDED />;
}

/* Non-floating InfoBoxes */
.e2-comments .e2-infobox,
.e2l-fw .e2-infobox,
#e2-relationships .e2-infobox
{
	clear: both;
	width: auto;
	float: none;
	margin-right: 0px;
}

/* Full-width textareas */
.e2l-fw textarea,
textarea.e2l-fw

{
	max-width:100%;
	min-width:100%;	
}
textarea.e2l-fw {
	margin: 0px;
/*	margin-top: 10px;
	margin-bottom: 10px; */
}


/***** e2-wordcount: Wordcount widget *****/
.e2-wordcount-count {
	text-align: right;
	padding-top: 10px;
	padding-bottom: 10px;
}
.e2-wordcount-error {
	color: <%self:REMOVED />;
}


/***** e2-siblings: Sibling relationship widget *****/
.e2-siblings h1 {
	margin-bottom: 10px;
}
.e2-siblings li {
	margin-left: 10px;
	list-style-type: none;
}
.e2-siblings li.e2-siblings-active {
	list-style-type: disc;
}


/***** e2-tree: Relationship tree *****/

/* This very sensitive to changes. Be careful! */
/* Total width per item should be 249px */
/* Nested lists */
.e2-tree.e2-tree-children ul {
	padding-left: 0px;
	margin-left: 299px;	
}
.e2-tree.e2-tree-parents ul {
	padding-left: 0px;
	margin-left: -299px;	
	/* text-align:right; */
}

/* List items */
.e2-tree li {
	list-style: none;
	padding-bottom: 4px;
	position: relative;	
	width: 299px;
}

.e2-tree ul li a {
	top:0px;
	z-index:100;
	display:block;
	margin-left:16px;
	margin-right:16px;
}
.e2-tree.e2-tree-parents ul li a.draggable {
	text-align:right;
}

.e2-tree img.e2-tree-expand {
	z-index:101;
	position:absolute;
	top:0px;
}
.e2-tree.e2-tree-children img.e2-tree-expand {
	right:0px;	
}
.e2-tree.e2-tree-parents img.e2-tree-expand {
	left:0px;	
}

/* root element */

.e2-tree ul:first-child {
	margin-left: 0px;
	margin-top: 0px;
}

.e2-tree.e2-tree-parents ul:first-child {
	float:right;
}

/* Backgrounds */
.e2-tree.e2-tree-children li {
	background:url('${EMEN2WEBROOT}/static-${VERSION}/images/bg.F.children.png') repeat-y;	
}
.e2-tree.e2-tree-parents li {
	background:url('${EMEN2WEBROOT}/static-${VERSION}/images/bg.F.parents.png') repeat-y;	
	background-position:top right;	
}
.e2-tree.e2-tree-children li:first-child {
	background:url('${EMEN2WEBROOT}/static-${VERSION}/images/bg.T.children.png') repeat-y;	
}
.e2-tree.e2-tree-parents li:first-child {
	background:url('${EMEN2WEBROOT}/static-${VERSION}/images/bg.T.parents.png') repeat-y;	
	background-position:top right;
}
.e2-tree.e2-tree-children li:last-child {
	background:url('${EMEN2WEBROOT}/static-${VERSION}/images/bg.L.children.png') no-repeat;
}
.e2-tree.e2-tree-parents li:last-child {
	background:url('${EMEN2WEBROOT}/static-${VERSION}/images/bg.L.parents.png') no-repeat;
	background-position:top right;
}
.e2-tree.e2-tree-children ul li:only-child {
	background:url('${EMEN2WEBROOT}/static-${VERSION}/images/bg.-.children.png') no-repeat;
}
.e2-tree.e2-tree-parents ul li:only-child {
	background:url('${EMEN2WEBROOT}/static-${VERSION}/images/bg.-.parents.png') no-repeat;
	background-position:top right;
}
.e2-tree:first-child > ul:first-child > li:first-child {
	background:none
}


/***** e2-select: Selection helper *****/

.e2-select-count {
	display:block;
}

/***** e2-browse: Relationship Editor and Selector *****/

.e2-browse-active {
	background-color:#eee !important;
}

.e2-browse-hover {
	background-color: #999 !important;
}

.e2-browse-selected {
	background-color: orange !important;
}

.e2-browse-helper {
	z-index: 1000;
	width:200px;
	background:white;
	padding:5px;
	border:solid red 2px;
}


/***** e2-tile: Tile image preview *****/
.e2-tile .e2-tile-controls {
	display: block;
	position: absolute;
	top: 20px;
	right: 0px;
	padding: 5px;
	z-index: 100;
	border-right-style: dashed;
	border-right-width: 1px;
	text-align: center;
	background:#eee;
}

.e2-tile .e2l-controls {
	margin: 0px;
	display: block;
	padding: 0px;
	width: 565px;
	position: absolute;
	top: 0px;
	right: 0px;
	height: 100%;
	overflow: auto;
}

.e2-tile {
	z-index: 0;
	height: 100%;
	position: relative;
	overflow: hidden;
}

.e2-tile-outer {
	position:relative;
	border-bottom:solid 1px #ccc;
}




/***** e2-box: Boxer *****/

.e2-box-img {
}

.e2-box-box {
	z-index: 100;
	position: absolute;
	top: 0px;
	left: 0px;
	border: solid red 1px;
	width: 10px;
	height: 10px;
}

.e2-box-hover {
	outline: solid red 5px;
}

.e2-box-boxarea {
	height: 25px;
	padding: 4px;
}

.e2-box-boxarea .e2-box-img {
	border-style: solid;
	border-width: 2px;
	margin: 0px;
	margin-right: 2px;
	margin-bottom: 2px;
}

/***** Plots *****/

path.line {
  fill: none;
  stroke: #666;
  stroke-width: 1.5px;
}

path.area {
  fill: #e7e7e7;
}

line {
	stroke: black;
}

.axis {
  shape-rendering: crispEdges;
}
.axis line {
  stroke-opacity: .1;
  stroke: #000;
}
.axis path {
  fill: none;
  stroke: #000;
}
.e2-plot {
	font-size:10pt;
}
.e2-plot-bg {
	fill: white;
}
.e2-plot-controls {
	float:right;
	width:230px;
	list-style:none;
	padding-left:0px;
}
.e2-plot-label {
	display: inline-block;
	width: 60px;
}
.e2-plot-controls input.e2-plot-bounds {
	width:60px;
}
.e2-plot-color {
	width:20px;
}
.e2-plot-totals td {
	border-top:solid 1px #ccc;
}
.e2-plot-sparkbox {
	width:10px;
	border-bottom:solid 1px #ccc;
	padding:0px;
	margin:0px;
	background:#1F77B4;
	float:left;
}


/* Grumble */
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
.e2-button img {
	margin: 0px;
	padding: 0px;
	vertical-align: middle;
}
.e2l-shadow {
	-moz-box-shadow: 2px 2px 4px #ccc;
	-webkit-box-shadow: 2px 2px 4px #ccc;
	box-shadow: 2px 2px 4px #ccc;
}

/***** jQuery UI Overrides *****/


.ui-autocomplete {
	max-width: 300px;
	max-height: 300px;
	overflow-y: auto;
}

/* css for timepicker */
/* css for timepicker */
.ui-timepicker-div .ui-widget-header { margin-bottom: 8px; }
.ui-timepicker-div dl { text-align: left; }
.ui-timepicker-div dl dt { height: 25px; margin-bottom: -25px; }
.ui-timepicker-div dl dd { margin: 0 10px 10px 65px; }
.ui-timepicker-div td { font-size: 90%; }
.ui-tpicker-grid-label { background: none; border: none; margin: 0; padding: 0; }


/* Dialogs that aren't allowed to close */
.e2-dialog-no-close .ui-dialog-titlebar-close {display: none }

/* IE 6 doesn't support max-height
 * we use height instead, but this forces the menu to always be this tall
* html .ui-autocomplete {
	height: 300px;
}
*/

<%!
public = True
headers = {
	'Cache-Control': 'max-age=86400',
	'Content-Type': 'text/css'
}
%>
