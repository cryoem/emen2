/*
Ian Rees 2006.06.07
Assumes each notebook tab has a button with id "button_view" and a page with "page_view"
Redraws button borders (aesthetics) and changes visible page
*/

var ids=new Array()
var buttons=new Array()

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
	for (var i=0;i<buttons.length;i++) {
		document.getElementById(buttons[i]).className = 'switchbuttoninactive';		
	}		  
}

function init() {
	ids = getElementByClass("switchpage");
	buttons = getElementByClass("switchbutton");

	hideallids();
	
	switchid("mainview");
	
	Nifty("ul.table li","4px transparent top");
	Nifty("div.navtree","4px transparent");
	Nifty("#nav_first","4px transparent left");
	Nifty("#nav_last","4px transparent right");
	
	tileinit();
	
}
