var isdown=false;
var nx=0
var ny=0
var level=nx.length-1
var tileid = "";


function tileinit(nxinit,nyinit,tileidinit) {
	nx = nxinit;
	ny = nyinit;
	tileid = tileidinit;
	level = nx.length-1;
//	alert("nx: " + nx + "\nny: " + ny + "\ntileid: " + tileid + "\nlevel: " + level);
	
	setsize(nx[level]*256,ny[level]*256);
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
	cx=outdiv.clientWidth/2.0;
	cy=outdiv.clientHeight/2.0;

	setsize(nx[lvl]*256,ny[lvl]*256);

	scl=Math.pow(2.0,level-lvl)
	indiv.style.left=cx-((cx-x)*scl);
	indiv.style.top=cy-((cy-y)*scl);

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
	indiv.style.left=x0+event.clientX-mx0;
	indiv.style.top=y0+event.clientY-my0;
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
	x=-Math.ceil(tofloat(indiv.style.left)/256);
	y=-Math.ceil(tofloat(indiv.style.top)/256);
	outdiv=document.getElementById("outerdiv");
	dx=outdiv.clientWidth/256+1;
	dy=outdiv.clientHeight/256+1;
	for (i=x; i<x+dx; i++) {
		for (j=y; j<y+dy; j++) {
			if (i<0 || j<0 || i>=nx[level] || j>=ny[level]) continue;
			nm="im"+i+"."+j
			var im=document.getElementById(nm);
			if (!im) {
				im=document.createElement("img");
				im.src="/db/tileimage/" + tileid + "?level="+level+"&x="+i+"&y="+j;
				im.style.position="absolute";
				im.style.left=i*256+"px";
				im.style.top=j*256+"px";
				im.setAttribute("id",nm);
				indiv.appendChild(im);
			}
		}
	}
	dbug=document.getElementById("dbug");
	dbug.innerHTML = x + " " + y;
}

function setsize(w,h) {
	var indiv=document.getElementById("innerdiv");
	indiv.style.height=h;
	indiv.style.width=w;
}