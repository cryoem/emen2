var classcache = new Array();
var oldvalues = new Array();
var statecache = new Array();

function getStyle( element, cssRule )
{
  if( document.defaultView && document.defaultView.getComputedStyle )
  {
    var value = document.defaultView.getComputedStyle( element, '' ).getPropertyValue( 
      cssRule.replace( /[A-Z]/g, function( match, char ) 
      { 
        return "-" + char.toLowerCase(); 
      } ) 
    );
  }
  else if ( element.currentStyle ) var value = element.currentStyle[ cssRule ];
  else                             var value = false;
  return value;
}

function getElementByClass(classname) {
	var inc=0
	var elements=new Array()
	var alltags=document.all? document.all : document.getElementsByTagName("*")
	for (i=0; i<alltags.length; i++) {
		if (alltags[i].className==classname)
		elements[inc++]=alltags[i].id
	}
	return elements;
}


function toggle(id) {
	state = getStyle(document.getElementById(id),"display");
	if (id in statecache) {cache = statecache[id]} else {cache = "block"}
	if (state == 'none') {
		document.getElementById(id).style.display = cache;
	} else {
		document.getElementById(id).style.display = "none";
	}
	statecache[id] = state;

//	if (state != 'none') {
//		document.getElementById(id).style.display = 'none';
//	}
//	else {
//		document.getElementById(id).style.display = 'block';
//	}
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
	list = classcache["button_" + type];
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


function classprop(theClass,element,value) {
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
   if (document.styleSheets[S][cssRules][R].selectorText == theClass) {
    document.styleSheets[S][cssRules][R].style[element] = value;
   }
  }
 }	
}


// hide class members, show one, switch the button
function switchin(class, id) {	
//	classprop(".page_" + class,"display","none")
	hideclass("page_" + class);
	switchbutton(class,id);
	try { document.getElementById("page_" + class + "_" + id).style.display = 'block'; } catch (error) {}
}

// show/hide all members of a class. cannot operate at stylesheet level because we tend to set styles for single elements.
function hideclass(class) {
//	classprop("." + class,"display","none")
	list = classcache[class];
	if (!list) { list = getElementByClass(class) }
	for (var i=0;i<list.length;i++) {
		try { document.getElementById(list[i]).style.display = 'none'; } catch (error) {}
	}
}

function showclass(class) {
//		classprop("." + class,"display","block")
	list = classcache[dclass];
	if (!list) { list = getElementByClass(class) }
	for (var i=0;i<list.length;i++) {
		document.getElementById(list[i]).style.display = 'block';			
	}
}

function showclassexcept(class,except) {
	hideclass(class)
	list = getElementByClass(class);
	for (var i=0;i<list.length;i++) {
		if (list[i] != except) {
			document.getElementById(list[i]).style.display = 'block';			
		}
	}
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
	// these have to be cached or specified for a variety of complex reasons
	classcache["button_main"] = getElementByClass("button_main");
	classcache["page_main"] = getElementByClass("page_main");
	classcache["tooltip"] = getElementByClass("tooltip");			
	classcache["button_param"] = new Array("button_param_mainview","button_param_tabularview","button_param_onelineview","button_param_defaultview","button_param_records")
	classcache["page_param"] = new Array("page_param_mainview","page_param_tabularview","page_param_onelineview","page_param_defaultview","page_param_records")
	classcache["button_addrecord"] = new Array("button_addrecord_paramvalue","button_addrecord_inplace")
	classcache["page_addrecord"] = new Array("page_addrecord_paramvalue","page_addrecord_inplace")			
	classcache["page_recordview"] = new Array("page_recordview_dicttable","page_recordview_defaultview","page_recordview_protocol")						

	statecache["xmlrpc_makeedits_commit"] = "inline";
	statecache["xmlrpc_makeedits_cancel"] = "inline";

//javascript:hideclass('page_recordview');qshow('page_recordview_defaultview');

	switchin("main","mainview");

//	try {
//		hideclass('page_recordview');qshow('page_recordview_defaultview');	
//	} catch(error) {}

}


function submitattachfile() {
	for (var i=0;i<document.fileform.elements.length;i=i+2) {
		if (document.fileform.elements[i].value != "") {
			try {document.fileform.elements[i+1].value = document.fileform.elements[i].value;}
			catch(error) {}
		} 
	}
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