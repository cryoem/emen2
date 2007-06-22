var classcache = new Array();
var oldvalues = new Array();
var statecache = new Array();
var classstatecache = new Array();

function dict() {
}

//dict.prototype.update = function(l) {
//	for (var i=0;i<l.length;i++) {
//		this[String(l[i][0])] = l[i][1];
//	}
//}


//getcomputedstyle shortcut
function getStyle(element, cssRule) {
  var value = document.defaultView.getComputedStyle( element, '' ).getPropertyValue(cssRule);
  return value;
}

function initialstyle() {
	var alltags=document.getElementsByTagName("*");
	for (i=0; i<alltags.length; i++) {
		style = document.defaultView.getComputedStyle( alltags[i], '' ).getPropertyValue("display");
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
	for (i=0; i<length; i++) {
		if (alltags[i].className.indexOf(classname) != -1){elements.push(alltags[i].id)}
//			if (testClass.test(alltags[i].classname)){elements.push(alltags[i].id)}
	}
	classcache[classname] = elements;
	return elements;
}



function toggleclass(classname) {
	list = getElementByClass(classname);
	for (var i=0;i<list.length;i++){
		toggle(list[i]);
	}
}


function toggle(id) {
	el = document.getElementById(id);
	state = getStyle(el,"display");
	if (id in statecache) {cache = statecache[id]} else {
			(el.nodeName == "DIV") ? cache = 'block' : cache = 'inline';
		}
	statecache[id] = state;
	(state == 'none') ?	el.style.display = cache :  el.style.display = "none";

	if (document.getElementById(id + "_button")) {
		button = document.getElementById(id + "_button");		
		if (state != 'none') {
			button.innerHTML = "+";
		} else {
			button.innerHTML = "-";
		}
	} 
}


function switchbutton(type,id) {
	list = getElementByClass("button_"+type);
	
	for (var i=0;i<list.length;i++) {
		if (list[i] != "button_" + type + "_" + id) {
			if (document.getElementById(list[i])) {document.getElementById(list[i]).className = "button_" + type}
		}
		else {
			if (document.getElementById(list[i])) {document.getElementById(list[i]).className = "button_" + type + " " + "button_" + type + "_active"}
		}
	}
}



// fixme: no longer needed once new permissions script is done
function classprop(classname,element,value) {
//based on http://www.shawnolson.net/scripts/public_smo_scripts.js
 var cssRules;
 if (document.all) {
  cssRules = 'rules';
 }
 else if (document.getElementById) {
  cssRules = 'cssRules';
 }
 for (var S = 0; S < document.styleSheets.length; S++){
  for (var R = 0; R < document.styleSheets[S][cssRules].length; R++) {
   if (document.styleSheets[S][cssRules][R].selectorText == classname) {
    document.styleSheets[S][cssRules][R].style[element] = value;
   }
  }
 }	
}


// hide class members, show one, switch the button
function switchin(classname, id) {	
 	getElementByClass(classname,1);
	switchbutton(classname,id);
	hideclass("page_" + classname);
	qshow("page_" + classname + "_" + id);
}

// show/hide all members of a class. cannot operate at stylesheet level because we tend to set styles for single elements.
function hideclass(classname,update) {
	list = getElementByClass(classname,update);		
	try {
		el = document.getElementById(list[0]);
		state = getStyle(el,"display");
		classstatecache[classname] = state;
	} catch(error) {
//		alert(classname + " : " + list[0]);
	}

	for (var i=0;i<list.length;i++) {
		document.getElementById(list[i]).style.display = 'none'; 
	}
}

function showclass(classname,update) {
	list = getElementByClass(classname,update);

	if (classname in classstatecache) {cache = classstatecache[classname]} else {
			(document.getElementById(list[0]).nodeName == "DIV") ? cache = 'block' : cache = 'inline';
		}

	for (var i=0;i<list.length;i++) {
		document.getElementById(list[i]).style.display = cache;			
	}

}

function showclassexcept(classname,except) {
	hideclass(classname);
	showclass(classname);
	qhide(except);
}


// quick show or hide a single ID
function qshow(id) {
	try {
		document.getElementById(id).style.display = 'block';			
	} catch(error) {}
}
function qhide(id) {
	try {
		document.getElementById(id).style.display = 'none';			
	} catch(error) {}
}


function init() {
	ctxid_init_start('TWISTED_SESSION_ctxid');	

// these have to be cached or specified for the switching methods
//	initialstyle();
// saves a little time by caching		
//	classcache["page_recordview"] = new Array("page_recordview_dicttable","page_recordview_defaultview","page_recordview_protocol")						

	if (document.getElementById("page_main_mainview")) {
		switchin("main","mainview");
	}

	if (document.getElementById("page_recordview_defaultview")) {
		hideclass('page_recordview');
		qshow('page_recordview_defaultview');	
	}
	

}