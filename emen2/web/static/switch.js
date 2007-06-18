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

function getElementByClass2(className,update){
	var testClass = new RegExp("(^|\\s)" + className + "(\\s|$)");
	var tag = "*";
	var elm = document;
	var elements = (tag == "*" && elm.all)? elm.all : elm.getElementsByTagName(tag);
	var returnElements = [];
	var current;
	var length = elements.length;
	for(var i=0; i<length; i++){
		current = elements[i];
		if(testClass.test(current.className)){
			returnElements.push(current);
		}
	}
	return returnElements;
}


function toggleclass(classname) {
	list = getElementByClass(classname);

	for (var i=0;i<list.length;i++){
		toggle(list[i]);
	}
}


function toggle(id) {
	try {
		state = getStyle(document.getElementById(id),"display");
		if (id in statecache) {cache = statecache[id]} else {cache = "block"}
		statecache[id] = state;

		if (state == 'none') {
			document.getElementById(id).style.display = cache;
		} else {
			document.getElementById(id).style.display = "none";
		}
	} catch(error) {}

	try {
		button = document.getElementById(id + "_button");		
		if (state != 'none') {
			button.innerHTML = "+";
		} else {
			button.innerHTML = "-";
		}
	} catch(error) {}

}


function switchbutton(type,id) {
	list = getElementByClass("button_"+type);
	
	for (var i=0;i<list.length;i++) {
		if (list[i] != "button_" + type + "_" + id) {
			try {
				document.getElementById(list[i]).className = "button_" + type;
			} catch(error) {}
		}
		else {
			try {document.getElementById(list[i]).className = "button_" + type + " " + "button_" + type + "_active";} catch(error) {}
		}
	}
}


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
function hideclass(classname) {
	list = getElementByClass(classname);		
	for (var i=0;i<list.length;i++) {
		document.getElementById(list[i]).style.display = 'none'; 
	}
}

function showclass(classname) {
	list = getElementByClass(classname);
	if (classname in classstatecache) {cache = classstatecache[classname]} else {cache = "inline"}

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


	switchin("main","mainview");

	try {
		hideclass('page_recordview');qshow('page_recordview_defaultview');	
	} catch(error) {}

}





// tooltip stuff
function tooltip_show(tooltipId)
{
//	hideclass('tooltip')
	try {
//	document.getElementById(tooltipId).style.display = 'block';
	} catch(error) {}
}

function tooltip_hide(tooltipId)
{
//	self.setTimeout('qhide(\'' + tooltipId + '\')', 5000)
////	document.getElementById(tooltipId).style.display = 'none';
}