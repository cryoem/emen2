var url = "/RPC2"; 

//replace with element value
var currentparam = "root_recorddef";

var ctxid = "";
var valuecache = new Array();

/***********************************************/

var callbacks = new Object();
var errbacks = new Object();

/***********************************************/

function items_dict(items) {
	r = new Object();
	for (var i=0;i<items.length;i++) {
		r[i[0]] = i[1];
	}
	return r;
}

function dict_items(dict) {
	r = new Array();
	for (i in dict) {
		r.push([i,dict[i]]);
	}
	return r;
}

/*****************************/

function combobox_onfocus(elem) {
	target=elem.parentNode.getElementsByTagName("ul")[0];	
	target.style.display = "block";
}
function combobox_setv(elem,setvalue) {
	target=elem.parentNode.parentNode.getElementsByTagName("input")[0];
	control=elem.parentNode;
	if (setvalue==null) {value=elem.innerHTML} else {value=setvalue}
	target.value = value;
	control.style.display = "none";
}

function combobox_onkeypress(elem,e) {
	if(window.event) {
		keycode = e.keyCode
	} else if(e.which)	{
		keycode = e.which
	}

	choices = elem.parentNode.getElementsByTagName("li")
	target=elem;
	v = target.value;
	len=v.length;
	switch (keycode) {
		case 8: //backspace  
			v=v.substr(0,len-1);
			break;
		case 46: //delete
			v=v.substr(0,len-1);		
			break;
		case 38: //up arrow		
		case 40: //down arrow
		case 37: //left arrow
		case 39: //right arrow
		case 33: //page up  
		case 34: //page down	 
		case 36: //home	
		case 35: //end				   
		case 13: //enter	 
		case 9: //tab  
		case 27: //esc  
		case 16: //shift	 
		case 17: //ctrl	
		case 18: //alt  
		case 20: //caps lock
			break;

		default:
			v = target.value + String.fromCharCode(keycode);
   } 
	
	for (i=0;i<choices.length;i++) {
		value=choices[i].innerHTML.toLowerCase();
		if ((value.indexOf(v.toLowerCase()) >= 0)||(v=="")) {
			choices[i].style.display = "block";
		} else {
			choices[i].style.display = "none";
		}
	}	
}

/*****************************/

//function selecttarget() {
//	write = document.getElementById(target);
//	write.value = write.value + " $$" + currentparam + "=";
//}

function ctxid_init_start(cookieName) {
	var sessiondid;
	var labelLen = cookieName.length;
	var cookieData = document.cookie;
	var cLen = cookieData.length;
	var i = 0;
	var cEnd;
	while (i < cLen) {
		var j = i + labelLen;
		if (cookieData.substring(i,j) == cookieName) {
			cEnd = cookieData.indexOf (";" , j);
			if (cEnd == -1) {
				cEnd = cookieData.length;
			}
				ctxid = unescape(cookieData.substring(j+1,cEnd));
			}
		i++;
	}
}

function parambrowserinit(init) {
	param = init || "root_parameter";
	currentparam = param;
	display(param,"paramdef");
}
 
function protobrowserinit(init) {
	param = init || "root_protocol";
	currentparam = param;
	display(param,"recorddef");
}

function recordbrowserinit(init) {
	param = init || "root_protocol";
	currentparam = param;
	recdisplay(param);
}


function display(param,type) {
	currentparam = param;
	browsertype = type;


	if (browsertype == "paramdef") {
		clearchildelements('getparamdef');				
		xmlrpcrequest("getparamdef", [param])
		}
	if (browsertype == "recorddef") {
		clearchildelements('getrecorddef');		
		xmlrpcrequest("getrecorddef",[param])
	}
	
	clearchildelements('getchildrenofparents');
	clearchildelements('getchildren');

	xmlrpcrequest("getchildrenofparents",[param,type,0,ctxid]);
	xmlrpcrequest("getchildren",[param,type,0,ctxid]);
	xmlrpcrequest("getcousins",[param,type,ctxid]);
}
function recdisplay(param) {
	currentparam = param;
	browsertype = "record";
	xmlrpcrequest("getrelatedrecswithnames",[param,"children",ctxid]);
	xmlrpcrequest("getrelatedrecswithnames",[param,"parents",ctxid]);
	xmlrpcrequest("getcousins",[param,type,ctxid]);
}

/***********************************************/

function clearchildelements(id) {
	p = document.getElementById(id);
	while (p.firstChild) {p.removeChild(p.firstChild)};	
}

function xmlrpc_getrelatedrecswithnames_cb(r) {
	d = document.createElement('div');
	d.id = "getchildren_box";
	d.className = "parent";
	d.innerHTML = "children:";
	var z = document.createElement('div');
	z.id = "getchildren_box2";
	z.className = "parents";
	p.appendChild(d);
	p.appendChild(z);

	for (var j=0;j<r.length;j++) {
		var y = document.createElement('a');
		y.href = "javascript:recdisplay('" + r[j][0] + "','" + browsertype + "')";
		y.innerHTML = r[j][1] + " ";
		y.className = "child";
		y.style.display = "block";
		y.style.width = "270px";
		y.style.height = "auto";

		z.appendChild(y);
	}
}

/***********************************************/


function xmlrpc_getchildrenofparents_cb(r) {
	p = document.getElementById('getchildrenofparents');
	
	for (var i=0;i<r.length;i++) {
		var x = document.createElement('div');
		x.className = "parent";
		x.id = "parent_" + r[i][0];

		var xn = document.createElement('a');
		xn.href = "javascript:display('" + r[i][0] + "','" + browsertype + "')";
		xn.innerHTML = 'parent: ' + r[i][0];
		x.appendChild(xn);

		var z = document.createElement('div');
		z.id = "getchildrenofparents_" + r[i][0]
		z.className = "parents";
		p.appendChild(x);
		p.appendChild(z);

		for (var j=0;j<r[i][1].length;j++) {
			var y = document.createElement('a');
			y.href = "javascript:display('" + r[i][1][j] + "','" + browsertype + "')";
			y.innerHTML = r[i][1][j] + " ";
			y.className = "child";
			z.appendChild(y);
		}
	}
}


function xmlrpc_getchildren_cb(r) {
	p = document.getElementById('getchildren');

	if (r.length == 0) {return}

	d = document.createElement('div');
	d.id = "getchildren_box";
	d.className = "parent";
	d.innerHTML = "children:";
	var z = document.createElement('div');
	z.id = "getchildren_box2";
	z.className = "parents";
	p.appendChild(d);
	p.appendChild(z);

	for (var j=0;j<r.length;j++) {
		var y = document.createElement('a');
		y.href = "javascript:display('" + r[j] + "','" + browsertype + "')";
		y.innerHTML = r[j] + " ";
		y.className = "child";
		z.appendChild(y);
	}
}


function xmlrpc_getrecorddef_cb(r) {
  recdef = new Object();
	for (var i=0;i<r.length;i++) {
		recdef[r[i][0]] = r[i][1];
	}
	
	// internet explorer is mysterious...
	viewfullie = document.getElementById("viewfull");
	viewfullie.href = "/db/recorddef/" + currentparam;
	
	f = document.getElementById("recdef_name");
	f.innerHTML = currentparam;
	d = document.getElementById("getrecorddef");

	k = document.createElement('span');
	k.innerHTML = "Creator: " + recdef["creator"] + "<br />Created: " + recdef["creationtime"];
	br = document.createElement('br');
	d.appendChild(k);
	d.appendChild(br);

	var views = new Object();
	views["mainview"] = recdef["mainview"];
	for (j in recdef["views"]) {
		views[j] = recdef["views"][j];
	}
	
	rdv = document.getElementById("recorddefviews");	
	clearchildelements('recorddefviews');

	fcb = document.createElement('div');
	fcb.className = "floatcontainer";
	fcb.id = "button_rdv_container";
	
	for (j in views) {
		k = document.createElement('div');
		k.className = "button_rdv";
		k.id = "button_rdv_" + j;
		kl = document.createElement('a');
		kl.innerHTML = j;
		kl.className = "jslink";
		kl.href = "javascript:switchin('rdv','"+ j + "');"
		k.appendChild(kl);
		fcb.appendChild(k);
	}
	k = document.createElement('div');
	k.className="button_rdv";
	k.id="button_rdv_records";
	k.innerHTML = '<a href=\"/db/query?parent=&query=find+'+recdef["name"]+'\">Records</a>';
	fcb.appendChild(k);
	rdv.appendChild(fcb);

	fcp = document.createElement('div');
	fcp.style.clear = 'both';
	fcp.className="floatcontainer";
	fcp.id = "page_rdv_container";	
	
	for (j in views) {
		k = document.createElement('div');
		kt = document.createElement('div');
		k.className = "page_rdv";
		kt.className = "view_rdvt";
		k.id = "page_rdv_" + j;
		kt.id = "page_rdvt_" + j ;
		kt.innerHTML = views[j];
		k.appendChild(kt);
		fcp.appendChild(k);
	}

	rdv.appendChild(fcp);
	
	editfield=document.getElementById("form_protobrowser_edit");
	if (global_user == recdef["creator"] || global_user == recdef["owner"]) {
		editfield.style.display = "inline";
	}
	a=document.getElementById("form_protobrowser_newrecorddeftarget");
	a.href="/db/newrecorddef/"+recdef["name"];
	
	switchin('rdv','mainview');
	
}



function xmlrpc_getcousins_cb(r) {
}

function xmlrpc_getparamdef_cb(r) {
	f = document.getElementById("paramdef_name");
	f.innerHTML = currentparam;

	def = document.getElementById("getparamdef");	
	clearchildelements('getparamdef');

	for (var i=0;i<r.length;i++) {
		k = document.createElement('span');
		k.innerHTML = r[i][0] + ": ";
		v = document.createElement('span');
		v.innerHTML = r[i][1];
		br = document.createElement('br');
		def.appendChild(k);
		def.appendChild(v);
		def.appendChild(br);
	}
	
}


/***********************************************/


function form_addfile(formobj) {
	formobj.fname.value = formobj.filedata.value;
}


/***********************************************/

function form_addcomment(formobj) {
	comment = formobj.comment.value;
	recid = parseInt(document.form_record_generaloptions.recid.value);
	r = xmlrpcrequest("addcomment",[recid,comment,ctxid],0);
	window.location.reload();
}



/***********************************************/


/***********************/

function clearalerts() {
	// use with timer to clear alerts
	el = document.getElementById("alert");
	clearchildelements('alert');
}

function topalert(msg) {
	// draw alert messages in top of window
	// now integrated with previous notify mechanism
	el = document.getElementById("alert");
	clearchildelements('alert');
	if (typeof(msg) == typeof(Array())) {
		for (var i=0;i<msg.length;i++) {
			d = document.createElement("div");
			d.innerHTML = msg[i];
			d.className = "notification_inner2";
			el.appendChild(d);
		}
	}	else {
		d = document.createElement("div");
		d.innerHTML = msg;
		d.className = "notification_inner2";
		el.appendChild(d);
	}
	scroll(0,0);
}

function getselectchoice(obj) {
	//replace into formelementgetvalue
	r = new Array();
	for (var i=0;i<obj.length;i++) {
    if (obj.options[i].selected) {
			r.push(obj.options[i].text);
		}
  }
	return r;
}

function addtextfield(id) {
	//add an item to an extensible list of values (e.g. stringlist)
	e = document.getElementById(id);
	expanded = id.name.split("___");
	ekind = expanded[0] || "r";
	ename = expanded[1];
	etype = expanded[2] || "string";
	elist = parseInt(expanded[3]) || 0;
	epos = expanded[4] || 0;
}

function form_addrecorddef(formobj) {
	//collects values, validates, and adds recorddef
	rv=collectpubvalues_new(formobj);
	r=rv["r"];

	if (r["views"]["defaultview"]==undefined) {
		r["views"]["defaultview"] = r["mainview"];
	}
	
	if (r["name"]==undefined||r["name"]=="") {
		alerts.push("You must specify a name");
	}
	if (r["mainview"]==undefined||r["mainview"]=="") {
		alerts.push("You must describe the experimental protocol.");
	}
	if (r["views"]["tabularview"]==undefined||r["views"]["tabularview"]=="") {
		alerts.push("You must specify a table view.");
	}
	if (r["views"]["recname"]==undefined||r["views"]["recname"]=="") {
		alerts.push("You must specify a format for the record name.");
	}
	if (r["views"]["defaultview"]!=undefined&&r["views"]["defaultview"]=="") {
		alerts.push("A default view is required.");
	}
			
	if (alerts.length > 0) {
		topalert(alerts);
		return
	} 

	callbacks["addrecorddef"] = new CallbackManager();
	callbacks["addrecorddef"].end = function(r) {
		window.location = window.location.protocol + "//" + window.location.host + "/db/recorddef/" + r + "?notify=" + 7;	
	}

	for (i in rv["p"]["parents"]) {
		callbacks["addrecorddef"].register(eval("function (r) {xmlrpcrequest('pclink',['"+i+"','"+r["name"].toLowerCase()+"','recorddef',ctxid],0)}"));
	}
	for (i in rv["p"]["children"]) {
		callbacks["addrecorddef"].register(eval("function (r) {xmlrpcrequest('pclink',['"+r["name"].toLowerCase()+"','"+i+"','recorddef',ctxid],0)}"));
	}

	xmlrpcrequest("addrecorddef",[r,ctxid]);
	
}



function xmlrpc_putrecorddef(formobj) {
	r = xmlrpcrequest("getrecorddef",[currentparam,ctxid],0)
	recdef = new dict();
	// instead of .update()
	for (var i=0;i<r.length;i++) {
		recdef[r[i][0]] = r[i][1];
	}

	recdef["mainview"] = formobj.mainview.value;
	recdef["views"]["defaultview"] = formobj.defaultview.value;
	recdef["views"]["tabularview"] = formobj.tabularview.value;
	recdef["views"]["onelineview"] = formobj.onelineview.value;
	
	// syncronous because of linking required
	r=xmlrpcrequest("putrecorddef",[recdef,ctxid],0);

	parents = getselectchoice(formobj.parents);
	children = getselectchoice(formobj.children);
	
	// relink as necessary
	for (var i=0;i<parents.length;i++) {
		if (valuecache["parents"].indexOf(parents[i]) == -1) { // new link
			l = xmlrpcrequest("pclink",[parents[i],currentparam,"recorddef",ctxid],0);
		}
	}
	for (var i=0;i<valuecache["parents"].length;i++) {
		if (parents.indexOf(valuecache["parents"][i]) == -1) { // removed link
			l = xmlrpcrequest("pcunlink",[valuecache["parents"][i],currentparam,"recorddef",ctxid],0);
		}
	}
	
	for (var i=0;i<children.length;i++) {
		if (valuecache["children"].indexOf(children[i]) == -1) { // new link
			l = xmlrpcrequest("pclink",[currentparam,children[i],"recorddef",ctxid],0);
		}
	}
	for (var i=0;i<valuecache["children"].length;i++) {
		if (children.indexOf(valuecache["children"][i]) == -1) { // removed link
			l = xmlrpcrequest("pcunlink",[currentparam,valuecache["children"][i],"recorddef",ctxid],0);
		}
	}
	
	topalert("Changes saved.");
	
}


function form_protobrowser_cancel(formobj) {
	showclass("parent");
	showclass("parents");

	toggle("form_protobrowser_edit");
	toggle("form_protobrowser_commit");
	toggle("form_protobrowser_cancel");	
	
	recdefname = document.getElementById("recdef_name")
	recdefnameparent = recdefname.parentNode;
	newrecdefname = document.createElement('div');
	newrecdefname.id = "recdef_name";
	newrecdefname.innerHTML = currentparam;
	
	recdefnameparent.replaceChild(newrecdefname,recdefname);	

	left = document.getElementById("left");
	left.removeChild(document.getElementById("recdef_parents"));
	right = document.getElementById("right");
	right.removeChild(document.getElementById("recdef_children"));
		
	xmlrpcrequest("getrecorddef",[currentparam])
	
/*
	list = getElementByClass("view_rdvt");
	for (var i=0;i<list.length;i++) {
		el = document.getElementById(list[i]);
		pn = el.parentNode;
		view = document.createElement('div');
		view.className = "view_rdvt";
		view.id = el.id;
		view.innerHTML = valuecache[el.id.split("_")[2]]
		pn.removeChild(el);
		pn.appendChild(view);
	}*/	
	
}

function form_protobrowser_edit(formobj) {
	hideclass("parents",1);
	hideclass("parent",1);
	qhide("button_rdv_records");
	toggle("form_protobrowser_edit");
	toggle("form_protobrowser_commit");
	toggle("form_protobrowser_cancel");	
	
	list = getElementByClass("view_rdvt");
	recdefname = document.getElementById("recdef_name")
	recdefnameparent = recdefname.parentNode;

	newrecdefname = document.createElement('input');
	newrecdefname.type = "text";
	newrecdefname.style.width="270px";
	newrecdefname.name = "name";
	newrecdefname.id = "recdef_name";
	newrecdefname.value = currentparam;
	
	recdefnameparent.replaceChild(newrecdefname,recdefname);
	
	
	for (var i=0;i<list.length;i++) {
		el = document.getElementById(list[i]);
		pn = el.parentNode;
		textarea = document.createElement('textarea');
		textarea.id = el.id;
		textarea.className = "view_rdvt";
		textarea.name = el.id.split("_")[2];
		valuecache[textarea.name] = el.innerHTML;
		textarea.cols = "80";
		textarea.rows = "20";
		textarea.value = el.innerHTML
		pn.removeChild(el);
		pn.appendChild(textarea);
	}
	
	// ok, now multiple select lists...
	xp = xmlrpcrequest("getparents",[currentparam,"recorddef",0,ctxid],0);
	xc = xmlrpcrequest("getchildren",[currentparam,"recorddef",0,ctxid],0);
	valuecache["parents"] = xp;
	valuecache["children"] = xc;

	r = xmlrpcrequest("getrecorddefnames",[],0);

	parents = document.createElement('select');
	parents.name = "parents"
	parents.multiple = true;
	parents.style.width = "300px";
	parents.size = 8;
	parents.id = "recdef_parents";
	for (var i=0;i<r.length;i++) {
		option = document.createElement('option');
		if (xp.indexOf(r[i]) > -1) {option.selected = 1}
		option.value=r[i];
		option.text=r[i];
		parents.appendChild(option);
	}
	left = document.getElementById("left");
	left.appendChild(parents);
	
	
	children = document.createElement('select');
	children.name = "children"
	children.multiple = true;
	children.style.width = "300px";
	children.size = 8;
	children.id = "recdef_children";
	for (var i=0;i<r.length;i++) {
		option = document.createElement('option');
		if (xc.indexOf(r[i]) > -1) {option.selected = 1}
		option.value=r[i];
		option.text=r[i];
		children.appendChild(option);
	}
	right = document.getElementById("right");
	right.appendChild(children);
	
}



/***********************************************/

function action_addparamdef(formobj) { 
	newvalues=collectpubvalues_new(formobj);
//	console.log(newvalues["r"]);
//	console.log(newvalues["p"]);

	callbacks["addparamdef"] = new CallbackManager();
	callbacks["addparamdef"].end = function(r) {
		window.location = window.location.protocol + "//" + window.location.host + "/db/paramdef/" + r + "?notify=" + 8;	
	}

	xmlrpcrequest("addparamdef",[dict_items(newvalues["r"]),ctxid,newvalues["p"]["parent"]]);
}


/***********************************************/

function xmlrpc_echo() {
	test = ["one","two","three"];
	xmlrpcrequest("echo",[test]);
}
function xmlrpc_echo_cb(a) {
//	alert("callback");
	document.getElementById("xmlrpc_output").value = a;
}
function xmlrpc_echo_eb(faultCode,faultString) {
	alert("error callback: " + faultCode);
}


/***********************************************/

function form_makeedits(formobj){
	formobj.commit.style.display = "block";
	formobj.cancel.style.display = "block";
	formobj.edit.style.display = "none";

//	qshow("tab_generaloptions");
	showclass('input_elem');
	hideclass('param_display');
	return false;
}

function form_makeedits_cancel(formobj) {
	formobj.commit.style.display = "none";
	formobj.cancel.style.display = "none";
	formobj.edit.style.display = "block";

//	qhide("tab_generaloptions");
	showclass('param_display');
	hideclass('input_elem');
	return false;
}

function form_makeedits_putrecord(formobj) {
	newvalues = collectpubvalues_new(formobj)["r"];
	if (newvalues) {
		newvalues["rectype"]=rectype;
		recid = parseInt(document.form_record_generaloptions.recid.value);
		newvalues["recid"]=recid;
		console.log(newvalues);
		xmlrpcrequest("putrecord",[dict_items(newvalues),ctxid]);	
	}
}

function form_makeedits_putnewrecord(formobj) {
	newvalues = collectpubvalues_new(formobj)["r"];
	if (newvalues) {
		newvalues["rectype"]=rectype;

		if (document.form_record_generaloptions.inheritpermissions.checked) {
			parentid = parseInt(document.form_record_generaloptions.permissionsparent.value);
			p = xmlrpcrequest("getrecord",[parentid,ctxid],0);
			parentdict = new dict();
			for (var i=0;i<p.length;i++) {
				parentdict[p[i][0]] = p[i][1];
			}
			newvalues["permissions"]=parentdict["permissions"];	
		}
	
		if (alerts.length > 0) {
			topalert(alerts);
			return
		} 

	//	console.log(dict_items(newvalues));
		xmlrpcrequest("putrecord",[dict_items(newvalues),ctxid]);
	}
}

function input_moreoptions(elem) {
	target=elem.parentNode;
	i=target.getElementsByTagName("input");
	expanded = i[0].name.split("___");
	len=i.length;
	newname = new Array();
	newname.push(expanded[0]);
	newname.push(expanded[1]);
	newname.push(expanded[2]);
	newname.push(expanded[3]);
	newname.push(len+1);	
	newname = newname.join("___");
//r___%s___%s___1___%s
// <span class="jslink" onclick="input_moreoptions(this)">[+]</span> <br/>
	n=document.createElement("input");
	n.type = "text";
	n.name=newname;
	n2=document.createElement("br");
	n3=document.createElement("span");
	target.appendChild(n2); 
	target.appendChild(n); 	
}	


function formelementgetvalue(elem) {
	if (elem.type == "select-multiple") {
		value = new Object();
		for (var i = 0; i < elem.options.length; i++) {
			if (elem.options[i].selected) { value[elem.options[i].value]=1 }
		}
	} else if (elem.type == "checkbox") {
		if (e.checked) { value = 1 } else { value = 0 }
	} else {
		value = elem.value;
	}
	if (value==""){value=null}
	return value;
}


function validate_date(date) {
	sp = date.split(" ");
	sd = sp[0].split("/");
	st=0;
	if (sp.length>1) {st=sp[1].split(":")}
	if (st.length<3) {throw RangeError}
	year=parseInt(sd[0]);
	if (sd[0].length != 4) {throw RangeError}
	month=parseInt(sd[1]);
	if (month > 12 || sd[1].length != 2) {throw RangeError}
	day=parseInt(sd[2]);
	if (day > 31 || sd[1].length != 2) {throw RangeError}
	if (st) {
		if (st.length<3){throw RangeError};
		hours=parseInt(st[0]);
		if (hours>23 || st[0].length != 2){throw RangeError}
		minutes=parseInt(st[1]);
		if (minutes>59 || st[1].length != 2){throw RangeError}
		seconds=parseInt(st[2]);
		if (seconds>59 || st[2].length != 2){throw RangeError}
	}
	return date
}
function validate_float(f) {
	r=parseFloat(f);
	if (isNaN(r)) {throw TypeError}
	return f
}
function validate_int(i) {
	r=parseInt(i);
	if (isNaN(r)) {throw TypeError}
	return r
}
function validate_bool(b) {
	b = parseInt(b);
	if (b>1||b<0) {throw TypeError}
	return b
}

function collectpubvalues_new(formobj) {
	var r = new Object();
	r["r"] = new Object();
	r["p"] = new Object();
	alerts=new Array();
	
	for (var i=0;i<formobj.elements.length;i++) {
		expanded = formobj.elements[i].name.split("___");
		e = formobj.elements[i];
		ekind = expanded[0] || "r";
		ename = expanded[1];
		etype = expanded[2] || "string";
		elist = parseInt(expanded[3]) || 0;
		epos = expanded[4] || null;
		
		if (e.disabled||e.type=="button") {continue}
		
		if ( (elist) && (!r[ekind][ename])) {
			if (etype=="floatlist"||etype=="stringlist"||etype=="intlist") {
					r[ekind][ename] = new Array();
			} else {
					r[ekind][ename] = new Object();
			}
		}

// # 	"int":("d",lambda x:int(x)),			# 32-bit integer
// # 	"longint":("d",lambda x:int(x)),		# not indexed properly this way
// # 	"float":("f",lambda x:float(x)),		# double precision
// # 	"longfloat":("f",lambda x:float(x)),	# arbitrary precision, limited index precision
// # 	"choice":("s",lambda x:str(x)),			# string from a fixed enumerated list, eg "yes","no","maybe"
// # 	"string":("s",lambda x:str(x)),			# a string indexed as a whole, may have an extensible enumerated list or be arbitrary
// # 	"text":("s",lambda x:str(x)),			# freeform text, fulltext (word) indexing
// # 	"time":("s",lambda x:str(x)),			# HH:MM:SS
// # 	"date":("s",lambda x:str(x)),			# yyyy/mm/dd
// # 	"datetime":("s",lambda x:str(x)),		# yyyy/mm/dd HH:MM:SS
// # 	"intlist":(None,lambda y:map(lambda x:int(x),y)),		# list of integers
// # 	"floatlist":(None,lambda y:map(lambda x:float(x),y)),	# list of floats
// # 	"stringlist":(None,lambda y:map(lambda x:str(x),y)),	# list of enumerated strings
// # 	"url":("s",lambda x:str(x)),			# link to a generic url
// # 	"hdf":("s",lambda x:str(x)),			# url points to an HDF file
// # 	"image":("s",lambda x:str(x)),			# url points to a browser-compatible image
// # 	"binary":("s",lambda y:map(lambda x:str(x),y)),				# url points to an arbitrary binary... ['bdo:....','bdo:....','bdo:....']
// # 	"binaryimage":("s",lambda x:str(x)),		# non browser-compatible image requiring extra 'help' to display... 'bdo:....'
// # 	"child":("child",lambda y:map(lambda x:int(x),y)),	# link to dbid/recid of a child record
// # 	"link":("link",lambda y:map(lambda x:int(x),y)),		# lateral link to related record dbid/recid
// # 	"boolean":("d",lambda x:int(x)),
// # 	"dict":(None, lambda x:x)

/*
		console.log("----");
		console.log(e);
		console.log(ekind);
		console.log(ename);
		console.log(etype);
		console.log(elist);
		console.log(epos);
*/

		value=formelementgetvalue(e);
		if (value!=null) {
			if (etype=="int"||etype=="longint"||etype=="intlist") {
				try{value=validate_int(value)} catch(error) {alerts.push(ename+": invalid integer.")}
			}	else if (etype=="float"||etype=="longfloat"||etype=="floatlist") {
				try{value=validate_float(value)} catch(error) {alerts.push(ename+": invalid float.")}
			}	else if (etype == "choice") {

			} else if (etype=="string"||etype=="text") {

			} else if (etype=="boolean") {
				try{value=validate_bool(value)} catch(error) {alerts.push(ename+": invalid choice.")}

			} else if (etype == "dict") {

			} else if (etype == "datetime"||etype=="time"||etype=="date") {
				try{value=validate_date(value)} catch(error) {alerts.push(ename+": invalid date format.")}
			} else {
				// url, hdf, image, binary, binaryimage, child, link
			}
		
			if (elist&&epos!=null) {
				if (etype=="floatlist"||etype=="stringlist"||etype=="intlist") {
					r[ekind][ename].push(value);
				} else {
					r[ekind][ename][epos] = value;
				}
			} else {
					r[ekind][ename] = value;
			}
		}
		
	}

	if (alerts.length > 0) {
		topalert(alerts);
		return 0
	} 
	return r
}

/*
function collectpubvalues(formobj) {
	newvalues = new Array();
	nv = new Array();

	for (var i=0;i<formobj.elements.length;i++) {

		e = formobj.elements[i];
		exp = formobj.elements[i].name.split("___")
		epub = exp[0];
		ename = exp[1];
		etype = exp[2];
		eext = exp[3];
		epos = exp[4];

		if ( (epub != "r") || (e.disabled) ) {continue;}

		// first let's handle simple, single-element parameters
		// skip extend elements
		if ((e.type == "text" || e.type == "textarea") && eext != "etext") {
			nv[ename] = convertvartype(etype,e.value);
		}
		
		if (e.type == "select-one") {
			// is other checked?
			try {
				if (formobj.elements["r___" + ename + "___" + etype + "___e___0"].checked) {
					nv[ename] = convertvartype(etype,formobj.elements["r___" + ename + "___" + etype + "___etext___0"].value);
				} else {
					nv[ename] = convertvartype(etype,e.value);
				}
			} catch(error) {	
				nv[ename] = convertvartype(etype,e.value);
			}
		}
		
		// now multiple-select types
		// check if not single-select
		if (e.type == "checkbox") {
		// FIXME
			try {
				 if (formobj.elements["r___" + ename + "___" + etype].type != "select-one") {break}
				} catch(error) {

			if (!nv[ename]) {nv[ename] = new Array()}

			if (e.checked && eext != "e") {
				nv[ename].push(convertvartype(etype,e.value));
			}
			if (e.checked && eext == "e") {
				nv[ename].push(convertvartype(etype,formobj.elements["r___" + ename + "___" + etype + "___etext___" + epos].value));
			}
		}
		}	
	}

	for (k in nv) {
		if (k != "toXmlRpc") {
			newvalues.push([k,nv[k]]);
		}
	}

	return newvalues;
}

function convertvartype(vartype,value) {
	if (value) {
		r = value;
//		r = "<![CDATA[" + value + "]]>";
	} else { r = null }
	return r;
}

*/

callbacks["putrecord"] = new CallbackManager();
// go to new record
callbacks["putrecord"].end = function(r) {
	if (!isNaN(parseInt(r))) {
		window.location = window.location.protocol + "//" + window.location.host + "/db/record/" + r + "?notify=" + 5;
	} else {
		topalert(r);
	}
}




/***********************************************/

function xmlrpc_findparamname() {
	msg = XMLRPCMessage("findparamname",[document.xmlrpc_findparamname_form.q.value]);
	xmlrpcrequest("findparamname",[document.xmlrpc_findparamname_form.q.value]);
}
function xmlrpc_findparamname_cb(r) {

}

/***********************************************/



function form_secrecordadduser(formobj) {
	if (formobj.recurse.checked) { recurse = 20; } else { recurse = 0; }
	user = formobj.user.value;
	level = formobj.level.value;

	recid = parseInt(document.form_record_generaloptions.recid.value);
	
	usertuple = [[],[],[],[]];
	usertuple[level] = user;
	xmlrpcrequest("secrecordadduser",[usertuple,recid,ctxid,recurse]);	
}
function xmlrpc_secrecordadduser_cb(r) {
	recid = parseInt(document.form_record_generaloptions.recid.value);
	makeRequest("/db/permissions/" + recid + "?edit=1&recurse=" + recurse,"sidebar_permissions");
}


/***********************************************/

function form_showpermissions() {
	// full javascript replacement for permissions mini-page. may not happen.
}

function form_secrecorddeluser(formobj, user) {
	if (document.form_secrecordadduser_form.recurse.checked) { recurse = 20; } else { recurse = 0; }
	recid = parseInt(document.form_record_generaloptions.recid.value);
	xmlrpcrequest("secrecorddeluser",[user,recid,ctxid,recurse]);		
}
function xmlrpc_secrecorddeluser_cb(r) {
	recid = parseInt(document.form_record_generaloptions.recid.value);
	makeRequest("/db/permissions/" + recid + "?edit=1&recurse=" + recurse,"sidebar_permissions");
}



/***********************************************/




function makeRequest(url,zone,callback) {
    var http_request = false;

    if (window.XMLHttpRequest) { // Mozilla, Safari, ...
        http_request = new XMLHttpRequest();
        if (http_request.overrideMimeType) {
            http_request.overrideMimeType('text/html');
            // See note below about this line
        }
    } else if (window.ActiveXObject) { // IE
        try {
            http_request = new ActiveXObject("Msxml2.XMLHTTP");
        } catch (e) {
            try {
                http_request = new ActiveXObject("Microsoft.XMLHTTP");
            } catch (e) {}
        }
    }

    if (!http_request) {
        alert('Giving up :( Cannot create an XMLHTTP instance');
        return false;
    }
    http_request.onreadystatechange = function() { alertContents(http_request,zone); eval(callback);};
    http_request.open('GET', url, true);
    http_request.send(null);
}

function alertContents(http_request,zone) {
    if (http_request.readyState == 4) {
        if (http_request.status == 200) {
						document.getElementById(zone).innerHTML  = http_request.responseText;
        } else {
            alert('Error with request: network');
        }
    }
}


// raw xmlrpc request
function xmlrpcrequest(method,args,async) {
	
	if (typeof(async)=="undefined") {async=1} else {async=0};
	
	command = XMLRPCMessage(method,args);

   var http_request = false;
   if (window.XMLHttpRequest) { // Mozilla, Safari, ...
       http_request = new XMLHttpRequest();
   } else if (window.ActiveXObject) { // IE
       try {
           http_request = new ActiveXObject("Msxml2.XMLHTTP");
       } catch (e) {
           try {
               http_request = new ActiveXObject("Microsoft.XMLHTTP");
           } catch (e) {}
       }
   }
   if (!http_request) {
       alert('Error with request: Giving up :( Cannot create an XMLHTTP instance');
       return false;
   }
	//end
	
	if (async) {
		http_request.onreadystatechange=function() {		
			if (http_request.readyState==4) {
	  		if (http_request.status==200)	{	
					document.body.style.cursor = "default";
	
					// use callback system
					if (callbacks[method]) {

						try { 
							callbacks[method].callback(unmarshallDoc(http_request.responseXML,http_request.responseText)); 
						}	catch(error) {
							if (errbacks[method]) {errbacks[method].callback(error.faultString)}
							else {topalert("Error: " +error.faultString)}
						}
					
					// try old callback system	
					} else {						

						try {	eval("cb = xmlrpc_" + method + "_cb");} catch(error) {cb=function(r){}}
						try {	eval("eb = xmlrpc_" + method + "_eb");} catch(error) {eb=function(faultCode,faultString){alert("Error with request: "+faultCode+", "+faultString)}}

						try {
							cb(unmarshallDoc(http_request.responseXML,http_request.responseText));
						} catch(error) {
							eb(error.faultCode,error.faultString);
						}

					}

				}	else {
						alert("Error with request: network");
	  		}
	  	}
		}
		
		document.body.style.cursor = "wait";
		http_request.open("POST",url,true);
		http_request.send(command);
	} else {
		document.body.style.cursor = "wait";
		http_request.open("POST",url,false);
		http_request.send(command);
		document.body.style.cursor = "default";
		try {return unmarshallDoc(http_request.responseXML,http_request.responseText);}
		catch(error) {topalert("Error: " +error.faultString)}
	}


}