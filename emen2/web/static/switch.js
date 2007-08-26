var classcache = new Array();
var statecache = new Array();
var classstatecache = new Array();

classstatecache["input_elem"] = "inline";

/***** callback manager *****/


function CallbackManager() {
	this.f = new Array();
	this.end = function (r) {};
	this.register = function(callbackFunction) {
//	console.log("Registered "+callbackFunction);
	this.f.push(callbackFunction);
	}
	this.callback = function(r) {
//		console.log("Triggered callback");
		for (i=0;i<this.f.length;i++) {
			this.f[i](r);
		}
		this.end(r);
	}
}

/***** end callback manager *****/



function dict() {
}



//getcomputedstyle shortcut: fixed for IE
function getStyle(elem, cssRule, ieProp) {
		iep = ieProp || cssRule;
    if (elem.currentStyle) {
      return elem.currentStyle[iep];
    } else if (window.getComputedStyle) {
			return document.defaultView.getComputedStyle( elem, '' ).getPropertyValue(cssRule);
    }
    return "";
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
	list = getElementByClass(classname,update);
	for (var i=0;i<list.length;i++){
		toggle(list[i]);
	}
}


function toggle(id) {
	el = document.getElementById(id);
	if (el == null) {return};
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

function togglelink(id,target,reverse) {
	reverse = reverse || 0;
	target = document.getElementById(target);
	if (id.checked) {
		target.disabled = 1-reverse;
	} else {
		target.disabled = 0+reverse;
	}
}

function setdisable(id) {
	el = document.getElementById(id);
	if (el.disabled) {el.disabled = 0} else {el.disabled = 1};
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
	list = getElementByClass2(classname,update);		

	try {
		state = getStyle(list[0],"display");
		classstatecache[classname] = state;
	} catch(error) {
	}

	for (var i=0;i<list.length;i++) {
		list[i].style.display = 'none'; 
	}
}

function showclass(classname,update) {
	list = getElementByClass2(classname,update);

	if (classname in classstatecache) {cache = classstatecache[classname]} else {
//			if (document.getElementById(list[0]).nodeName == "DIV") {
				 cache = 'block' 
//			} else {cache = 'inline' }
	}

	for (var i=0;i<list.length;i++) {
		list[i].style.display = cache;			
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


/************************/


//var init = new CallbackManager();
//init.register(function (r) {
//	ctxid_init_start('TWISTED_SESSION_ctxid');	
//	});

//window.onload = init.callback("");

function init() {
	ctxid_init_start('TWISTED_SESSION_ctxid');	
	}

// old init
// these have to be cached or specified for the switching methods
//	initialstyle();
// saves a little time by caching		
//	classcache["page_recordview"] = new Array("page_recordview_dicttable","page_recordview_defaultview","page_recordview_protocol")						

//	if (document.getElementById("page_main_mainview")) {
//		switchin("main","mainview");
//	}

//	if (document.getElementById("page_recordview_defaultview")) {
//		hideclass('page_recordview');
//		qshow('page_recordview_defaultview');	