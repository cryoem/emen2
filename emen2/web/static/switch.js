var name;
var classcache = new Array();
var statecache = new Array();
var classstatecache = new Array();


/***********************************************/

Function.prototype.bind = function() {	
	var z=this;
	var args = Array.prototype.slice.call(arguments);
	var obj=args.shift();
  return function () {
		z.apply(obj, args.concat(Array.prototype.slice.call(arguments))); 
   }
}


// ANGER AT IE!!
/*
Element.prototype.addClass = function(classname) {
}
Element.prototype.removeClass = function(classname) {	
}
Element.prototype.clearChildren = function() {
	while (this.firstChild) {this.removeChild(this.firstChild)};	
}	

Document.prototype.getElementsByClassName = function(classname) {
	var elements=[];
	var alltags=document.all? document.all : document.getElementsByTagName("*")
	var length = alltags.length;
	for (i=0; i<length; i++) {
		if (alltags[i].className.indexOf(classname) != -1){elements.push(alltags[i])}
	}
	return elements;
}
*/
if(![].indexOf) Array.prototype.indexOf = function(needle){ for(var i=0; i<this.length; i++) if(this[i] == needle) return i; return -1 }


/***********************************************/

function clearChildren(elem) {
	while (elem.firstChild) {elem.removeChild(elem.firstChild)};	
}

function clearAlerts() {
	// use with timer to clear alerts
	// var el = document.getElementById("alert");
	var el = document.getElementById("alert");
	clearChildren(el);
}


function topalert(msg) {
	// draw alert messages in top of window
	// now integrated with previous notify mechanism
	clearAlerts();
	el=document.getElementById("alert");
	
	if (msg == null) {return}
	
	if (typeof(msg) == typeof(Array())) {
		for (var i=0;i<msg.length;i++) {
			var d = document.createElement("li");
			d.innerHTML = msg[i];
			d.className = "notification";
			el.appendChild(d);
		}
	}	else {
		var d = document.createElement("li");
		d.innerHTML = msg;
		d.className = "notification";
		el.appendChild(d);
	}
	scroll(0,0);
}



function dict() {
}

//getcomputedstyle shortcut: fixed for IE
function getStyle(elem, cssRule, ieProp) {
		var iep = ieProp || cssRule;
    if (elem.currentStyle) {
      return elem.currentStyle[iep];
    } else if (window.getComputedStyle) {
			return document.defaultView.getComputedStyle( elem, '' ).getPropertyValue(cssRule);
    }
    return "";
}


function initialstyle() {
	var alltags=document.getElementsByTagName("*");
	for (var i=0; i<alltags.length; i++) {
		var style = document.defaultView.getComputedStyle( alltags[i], '' ).getPropertyValue("display");
		statecache[alltags[i].id] = style
		classstatecache[alltags[i].className] = style

		if (!classcache[alltags[i].className]) {classcache[alltags[i].className]=new Array(alltags[i].id)}
		else {classcache[alltags[i].className].push(alltags[i].id);}

	}
}


// fixme: change to return list of actual elements instead of list of id's.. change this behavior everywhere (=faster)
function getElementByClass(classname,update) {
	if (classcache[classname] && update == 0) { return classcache[classname] }

//	var testClass = new RegExp("(^|\\s)" + classname + "(\\s|$)");
	var elements=[];
	var alltags=document.all? document.all : document.getElementsByTagName("*")
	var length = alltags.length;
	for (var i=0; i<length; i++) {
		if (alltags[i].className.indexOf(classname) != -1){elements.push(alltags[i].id)}
//			if (testClass.test(alltags[i].classname)){elements.push(alltags[i].id)}
	}
	classcache[classname] = elements;
	return elements;
}
function getElementByClass2(classname,update) {
	if (classcache[classname] && update == 0) { return classcache[classname] }
	var elements=[];
	var alltags=document.all? document.all : document.getElementsByTagName("*")
	var length = alltags.length;
	for (i=0; i<length; i++) {
		if (alltags[i].className.indexOf(classname) != -1){elements.push(alltags[i])}
	}
	classcache[classname] = elements;
	return elements;
}	


function toggleclass(classname,update) {
	var list = getElementByClass(classname,update);
	for (var i=0;i<list.length;i++){
		toggle(list[i]);
	}
}

function togglesidebar(elem2) {
	var elem=elem2.parentNode;
	var st = getStyle(elem.nextSibling,"display");
	if (st == "none") {
		// fixme: do this:
		// addClassname(elem,"sidebar_active")
		elem.childNodes[0].style.background="#F0F0F0";
		elem.nextSibling.style.display="block";
	} else {
		// rmClassname(elem,"sidebar_active")
		elem.childNodes[0].style.background="white";
		elem.nextSibling.style.display="none";
	}
}

function toggle(id) {
	var el = document.getElementById(id);
	if (el == null) {return};

	var state = getStyle(el,"display");
	var cache;
	if (id in statecache) {cache = statecache[id]} else {
			(el.nodeName == "DIV") ? cache = 'block' : cache = 'inline';
		}
	statecache[id] = state;
	(state == 'none') ?	el.style.display = cache :  el.style.display = "none";
 
}

function togglelink(id,target,reverse) {
	reverse = reverse || 0;
	var target = document.getElementById(target);
	if (id.checked) {
		target.disabled = 1-reverse;
	} else {
		target.disabled = 0+reverse;
	}
}

function setdisable(id) {
	var el = document.getElementById(id);
	if (el.disabled) {el.disabled = 0} else {el.disabled = 1};
}

function switchbutton(type,id) {
	var list = getElementByClass("button_"+type);
	
	for (var i=0;i<list.length;i++) {
		if (list[i] != "button_" + type + "_" + id) {
			if (document.getElementById(list[i])) {document.getElementById(list[i]).className = "button button_" + type}
		}
		else {
			if (document.getElementById(list[i])) {document.getElementById(list[i]).className = "button button_active button_" + type + " " + "button_" + type + "_active"}
		}
	}
}


switchedin=new Array();
switchedin["recordview"]="defaultview";
// hide class members, show one, switch the button
function switchin(classname, id) {
	switchedin[classname]=id;
 	getElementByClass(classname,1);
	switchbutton(classname,id);
	hideclass("page_" + classname);
	document.getElementById("page_" + classname + "_" + id).style.display = 'block';	
}

// show/hide all members of a class. cannot operate at stylesheet level because we tend to set styles for single elements.
function hideclass(classname,update) {
	var list = getElementByClass2(classname,update);		

	try {
		var state = getStyle(list[0],"display");
		classstatecache[classname] = state;
	} catch(error) {	}

	for (var i=0;i<list.length;i++) {
		list[i].style.display = 'none'; 
	}
}

function showclass(classname,update) {
	var list = getElementByClass2(classname,update);

	var cache;
	if (classname in classstatecache) {cache = classstatecache[classname]} else {
		cache = 'block' 
	}

	for (var i=0;i<list.length;i++) {
		list[i].style.display = "block";			
	}

}


/************************/

function init() {
}











