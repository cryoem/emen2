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

function toggle(id) {
	state = document.getElementById(id).style.display
	if (state == "") {
		document.getElementById(id).style.display = 'none';
	}
	if (document.getElementById(id).style.display != 'none') {
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
//	alert("ok!")
}


function init() {	
	ids = getElementByClass("switchpage");
	buttons = getElementByClass("switchbutton");
	headers = getElementByClass("switchheader");
	
//	alert(buttons);
	

	hideallids();
	
//	document.getElementById("standardtable").style.display = 'block';
	
	switchid("mainview");

//	RUZEE.Borders.add({
//		'#nav_first': { borderType:'simple', cornerRadius:8, edges:'ltb' },
//		'#nav_last': { borderType:'simple', cornerRadius:8, edges:'rtb' },
//		'ul.table li': { borderType:'simple', cornerRadius:8, edges:'lrt' },
//		'div.navtree': { borderType:'simple', cornerRadius:8 }
//	});
	
//	RUZEE.Borders.render();
  	
//	Nifty("ul.table li","4px transparent top");
//	Nifty("div.navtree","4px transparent");
//	Nifty("#nav_first","4px transparent left");
//	Nifty("#nav_last","4px transparent right");
	
//	tileinit();
	
}
