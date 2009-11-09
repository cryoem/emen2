var isdown=false;
var nx=0
var ny=0
var level=nx.length-1
var tileid = "";
var divdim = [512,512];
var imgw = 256;
var bid = null;

/*************************************************/


function tile_download(bid,filename) {
	//alert("Download "+bid+", "+filename);
	//http://ncmidb2:8080/download/200412170010B/20041208031758.dm3.gz
	//window.location("/download/"+bid+"/"+filename);
}

function tile_bindresize() {   
	var resizeTimer = null;
	$(window).bind('resize', function() {
		if (resizeTimer) clearTimeout(resizeTimer);
		resizeTimer = setTimeout(tile_fitheight, 100);
	});	
}

function tile_fitheight() {

	var e1=$(window).height();
	$("#outerdiv").height(e1-120);
	tile_center();
	
}

function tile_center() {
	indiv=document.getElementById("innerdiv");	
	indiv.style.left=($("#outerdiv").width() - (imgw*nx[level]))/2 + "px";
	indiv.style.top=($("#outerdiv").height() - (imgw*ny[level]))/2 + "px";
}

function tile_larger(bid) {
	window.location = EMEN2WEBROOT+"/db/tiles/"+bid+"/large/";
}

function tile_pspec(bid) {
	indiv=document.getElementById("innerdiv");
	indiv.style.left="0px";
	indiv.style.top="0px";
	var e=document.createElement("img");
	e.src=EMEN2WEBROOT+'/db/tiles/'+bid+'/image/?level=-1&amp;x=0&amp;y=0';
	e.width=divdim[0];
	e.height=divdim[1];
	$(indiv).empty().append(e);
}
function tile_1d(bid) {
	indiv=document.getElementById("innerdiv");
	indiv.style.left="0px";
	indiv.style.top="0px";
	var e=document.createElement("img");
	e.src=EMEN2WEBROOT+'/db/tiles/'+bid+'/image/?level=-2&amp;x=0&amp;y=0';
	e.width=divdim[0];
	e.height=divdim[1];
	$(indiv).empty().append(e);
}


function tile_init(ibid) {
	bid = ibid;
	
	var outerdivie=document.getElementById("outerdiv");
	var imgw = $("#outerdiv").height() / 2.0;
	if (imgw > 256) {imgw = 256;}
	
	var innerdivie=document.getElementById("innerdiv");
	innerdivie.innerHTML = '<img style="margin-top:60px;" src="'+EMEN2WEBROOT+'/images/spinner.gif" /><br />Checking tiles...'

	$.getJSON(EMEN2WEBROOT+"/db/tiles/"+bid+"/check/", tile_checktile_cb);

}


function tile_rebuild(bid) {
	var innerdivie=document.getElementById("innerdiv");
	innerdivie.innerHTML = '<img style="margin-top:60px;" src="'+EMEN2WEBROOT+'/images/spinner.gif" /><br />Generating tiles...'	
	$.getJSON(EMEN2WEBROOT+"/db/tiles/"+bid+"/create/", tile_createtile_cb);
}


function tile_checktile_cb(r) {
	//console.log("got checktile cb");
	//console.log(r);
	
	var innerdivie=document.getElementById("innerdiv");
	if (r[0][0] > 0) {
		// tile ok
		tile_init2(r[0],r[1],r[2]);
		tile_center();
	} else {
		// generate tile; init on callback
		innerdivie.innerHTML = '<img style="margin-top:60px;" src="'+EMEN2WEBROOT+'/images/spinner.gif" /><br />Generating tiles...'
		tile_rebuild(r[2]);
		//var createtile = new CallbackManager();
		//createtile.register(tile_createtile_cb);
		//createtile.req("createtile",[r[2],ctxid]);

	}
}

function tile_checktile_eb(r) {
	tile_error();
}

function tile_createtile_cb(r) {
	if (r[0][0] > -1) {
		tile_init2(r[0],r[1],r[2]);
	} else {
		tile_error();
	}
}

function tile_error() {
	var innerdivie=document.getElementById("innerdiv");	
	innerdivie.innerHTML = '<img style="margin-top:60px;" src="'+EMEN2WEBROOT+'/images/error.gif" /><br />Error: Could not create or access tiles.'
}

/*************************************************/



function tile_init2(nxinit,nyinit,tileidinit) {
	nx = nxinit;
	ny = nyinit;
	tileid = tileidinit;
	level = nx.length-1;
//	alert("nx: " + nx + "\nny: " + ny + "\ntileid: " + tileid + "\nlevel: " + level);
	
	setsize(nx[level]*imgw,ny[level]*imgw);
	var outdiv=document.getElementById("outerdiv");
	outdiv.onmousedown = mdown;
	outdiv.onmousemove = mmove;
	outdiv.onmouseup = mup;
	outdiv.ondragstart = function() { return false; }
	recalc();
}

function tofloat(s) {
	if (s=="") return 0.0;
	return parseFloat(s.substring(0,s.length-2));
}

function zoom(lvl) {
	if (lvl==level || lvl<0 || lvl>=nx.length) return;
	indiv=document.getElementById("innerdiv");
	x=tofloat(indiv.style.left);
	y=tofloat(indiv.style.top);

	outdiv=document.getElementById("outerdiv");

	cx=outdiv.clientWidth / 2.0;
	cy=outdiv.clientHeight / 2.0;


	setsize(nx[lvl]*256,ny[lvl]*256);

	scl=Math.pow(2.0,level-lvl)
	indiv.style.left=cx-((cx-x)*scl) + "px";
	indiv.style.top=cy-((cy-y)*scl) + "px";
//	//console.log([cx-((cx-x)*scl),cy-((cy-y)*scl)]);

	for (i=indiv.childNodes.length-1; i>=0; i--) indiv.removeChild(indiv.childNodes[i]);
	level=lvl
	recalc();
}

function zoomout() {
	zoom(level+1);
}

function zoomin() {
	zoom(level-1);
}

function mdown(event) {
	if (!event) event=window.event;		// for IE
	indiv=document.getElementById("innerdiv");
	isdown=true;
	y0=tofloat(indiv.style.top);
	x0=tofloat(indiv.style.left);
	mx0=event.clientX;
	my0=event.clientY;
	return false;
}

function mmove(event) {
	if (!isdown) return;
	if (!event) event=window.event;		// for IE
	indiv=document.getElementById("innerdiv");
	indiv.style.left=x0+event.clientX-mx0 + "px";
	indiv.style.top=y0+event.clientY-my0 + "px";

	recalc();
}

function mup(event) {
	if (!event) event=window.event;		// for IE
	isdown=false;
	recalc();
}

function recalc() {
//	alert("Recalc");
	indiv=document.getElementById("innerdiv");
	x=-Math.ceil(tofloat(indiv.style.left)/imgw);
	y=-Math.ceil(tofloat(indiv.style.top)/imgw);
	outdiv=document.getElementById("outerdiv");
	dx=outdiv.clientWidth/imgw+1;
	dy=outdiv.clientHeight/imgw+1;
	for (i=x; i<x+dx; i++) {
		for (j=y; j<y+dy; j++) {
			if (i<0 || j<0 || i>=nx[level] || j>=ny[level]) continue;
			nm="im"+i+"."+j
			var im=document.getElementById(nm);
			if (!im) {
				im=document.createElement("img");
				im.src=EMEN2WEBROOT+"/db/tiles/" + tileid + "/image/?level="+level+"&x="+i+"&y="+j;
				im.style.position="absolute";
				im.style.height=imgw+"px";
				im.style.width=imgw+"px";
				im.style.left=i*imgw+"px";
				im.style.top=j*imgw+"px";
				im.setAttribute("id",nm);
				indiv.appendChild(im);
			}
		}
	}
}

function setsize(w,h) {
	var indiv=document.getElementById("innerdiv");
	indiv.style.height=h;
	indiv.style.width=w;
}
