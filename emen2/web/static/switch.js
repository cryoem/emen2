var classcache = new Array();

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
	if (state != 'none') {
		document.getElementById(id).style.display = 'none';
	}
	else {
		document.getElementById(id).style.display = 'block';
	}
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

function switchin(type, id) {	
	hideclass("page_" + type);
	switchbutton(type,id);
	try {
		document.getElementById("page_" + type + "_" + id).style.display = 'block';
	} catch (error) { }
}

function hideclass(class) {
	list = classcache[class];
	for (var i=0;i<list.length;i++) {
		try {document.getElementById(list[i]).style.display = 'none';} catch(error) {}
	}
}

function showclass(class) {
	list = classcache[class];
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
	
	classcache["button_main"] = getElementByClass("button_main");
	classcache["page_main"] = getElementByClass("page_main");
	
	classcache["tooltip"] = getElementByClass("tooltip");			
	
	classcache["button_param"] = new Array("button_param_mainview","button_param_tabularview","button_param_onelineview","button_param_defaultview","button_param_records")
	classcache["page_param"] = new Array("page_param_mainview","page_param_tabularview","page_param_onelineview","page_param_defaultview","page_param_records")

	classcache["button_addrecord"] = new Array("button_addrecord_paramvalue","button_addrecord_inplace")
	classcache["page_addrecord"] = new Array("page_addrecord_paramvalue","page_addrecord_inplace")
	
			
	classcache["page_recordview"] = new Array("page_recordview_dicttable","page_recordview_defaultview","page_recordview_protocol")		
			
				
	try {
		switchin("main","mainview");
	} catch(error) {}

}













// tooltip stuff

function tooltip_show(tooltipId)
{
	hideclass('tooltip')
	try {
	document.getElementById(tooltipId).style.display = 'block';
	} catch(error) {}
}

function tooltip_hide(tooltipId)
{
	self.setTimeout('qhide(\'' + tooltipId + '\')', 5000)
//	document.getElementById(tooltipId).style.display = 'none';
}