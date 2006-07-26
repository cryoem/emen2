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
//	tooltips = getElementByClass("xstooltip");
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
  	
	Nifty("div.switchbutton","4px transparent top");
	Nifty("div.switchbuttonactive","4px transparent top");
	Nifty("div.switchbuttoninactive","4px transparent top");

	Nifty("div.navtree","4px transparent");
	Nifty("#nav_first","4px transparent left");
	Nifty("#nav_last","4px transparent right");

	Nifty("div.xstooltip","4px transparent");
	
//	tileinit();
	
}



// tooltip stuff

function xstooltip_findPosX(obj) 
{
  var curleft = 0;
  if (obj.offsetParent) 
  {
    while (obj.offsetParent) 
        {
            curleft += obj.offsetLeft
            obj = obj.offsetParent;
        }
    }
    else if (obj.x)
        curleft += obj.x;
    return curleft;
}

function xstooltip_findPosY(obj) 
{
    var curtop = 0;
    if (obj.offsetParent) 
    {
        while (obj.offsetParent) 
        {
            curtop += obj.offsetTop
            obj = obj.offsetParent;
        }
    }
    else if (obj.y)
        curtop += obj.y;
    return curtop;
}

function xstooltip_show(tooltipId, parentId, posX, posY)
{
    it = document.getElementById(tooltipId);
    
    if ((it.style.top == '' || it.style.top == 0) 
        && (it.style.left == '' || it.style.left == 0))
    {
        // need to fixate default size (MSIE problem)
        it.style.width = it.offsetWidth + 'px';
        it.style.height = it.offsetHeight + 'px';
        
        img = document.getElementById(parentId); 
    
        // if tooltip is too wide, shift left to be within parent 
        if (posX + it.offsetWidth > img.offsetWidth) posX = img.offsetWidth - it.offsetWidth;
        if (posX < 0 ) posX = 0; 
        
        x = xstooltip_findPosX(img) + posX;
        y = xstooltip_findPosY(img) + posY;
        
        it.style.top = y + 'px';
        it.style.left = x + 'px';
    }
    
    it.style.visibility = 'visible'; 
}

function xstooltip_hide(id)
{
    it = document.getElementById(id); 
    it.style.visibility = 'hidden'; 
}