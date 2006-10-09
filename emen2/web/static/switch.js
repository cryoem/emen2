/*
Ian Rees 2006.06.07
Assumes each notebook tab has a button with id "button_view" and a page with "page_view"
Redraws button borders (aesthetics) and changes visible page
*/

var ids=new Array()
var buttons=new Array()

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
//	alert(id + " " + state)
//	if (state == "") {
//		document.getElementById(id).style.display = 'none';
//	}
	if (state != 'none') {
		document.getElementById(id).style.display = 'none';
	}
	else {
		document.getElementById(id).style.display = 'block';
	}
}

function switchid(id) {
	var page = "page_" + id;
	var button = "button_" + id;
	hideallids();
	switch_page(page);
	switch_button(button);
}

function switch_page(id) {	
	document.getElementById(id).style.display = 'block';
}
function switch_button(id) {	
	document.getElementById(id).className = 'switchbuttonactive';
}

function hideallids() {
	for (var i=0;i<ids.length;i++) {
		document.getElementById(ids[i]).style.display = 'none';
	}		  
	for (var i=0;i<headers.length;i++) {
		document.getElementById(headers[i]).style.display = 'none';
	}
	for (var i=0;i<buttons.length;i++) {
		document.getElementById(buttons[i]).className = 'switchbuttoninactive';		
	}		  
}

function showallids() {
	hideallids();
	for (var i=0;i<ids.length;i++) {
		if (ids[i] != "page_mainview") {
			document.getElementById(ids[i]).style.display = 'block';			
		}
	}
	for (var i=0;i<headers.length;i++) {
		document.getElementById(headers[i]).style.display = 'block';
	}
	switch_button("button_allview")
}

function hideclass(class) {
	list = getElementByClass(class);
	for (var i=0;i<list.length;i++) {
		document.getElementById(list[i]).style.display = 'none';			
	}
}
function showclass(class) {
	list = getElementByClass(class);
	for (var i=0;i<list.length;i++) {
		document.getElementById(list[i]).style.display = 'block';			
	}
}
function qshow(id) {
	document.getElementById(id).style.display = 'block';			
}
function qhide(id) {
	document.getElementById(id).style.display = 'none';			
}

function init() {	
	ids = getElementByClass("switchpage");
	buttons = getElementByClass("switchbutton");
	headers = getElementByClass("switchheader");
	
	hideallids();
//	showallids();	
	switchid("mainview");
  		
//	tileinit();
	
}

// tooltip stuff

function tooltip_show(tooltipId)
{
	hideclass('tooltip')
	document.getElementById(tooltipId).style.display = 'block';
}

function tooltip_hide(tooltipId)
{
	self.setTimeout('qhide(\'' + tooltipId + '\')', 5000)
//	document.getElementById(tooltipId).style.display = 'none';
}