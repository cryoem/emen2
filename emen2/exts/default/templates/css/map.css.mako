/********** Relationship Map ***********/
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

/* The backgrounds are listed in live.css.mako, because they need ${EMEN2WEBROOT} */

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

/*
.e2-map.e2-map-parents ul:first-child {
	background:none;
}
*/

.e2-map-hover {
	background:orange;
	padding:0px;
}


/****** BACKGROUND URLS **********/

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



<%def name="mimetype()">text/css</%def>

<%!
public = True
headers = {
	'Cache-Control': 'max-age=86400',
	'Content-Type': 'text/css'
}
%>


