var url = "/RPC2"; 
var currentparam = "root_recorddef";
var ctxid = "";
var name;
var valuecache = new Array();

/***********************************************/

var callbacks = new Array();

/***********************************************/

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
  recdef = new dict();
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

	var views = new dict();
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
	r = xmlrpcrequest("addcomment",[name,comment,ctxid],0);
	window.location.reload();
}



/***********************************************/


/***********************/

function getselectchoice(obj) {
	r = new Array();
	for (var i=0;i<obj.length;i++) {
    if (obj.options[i].selected) {
			r.push(obj.options[i].text);
		}
  }
	return r;
}

function xmlrpc_putrecorddef(formobj) {
	r = xmlrpcrequest("getrecorddef",[currentparam,ctxid],0)
	recdef = new dict();
	// instead of .update()
	for (var i=0;i<r.length;i++) {
		recdef[r[i][0]] = r[i][1];
	}
//	console.log(recdef);
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
	
}

function xmlrpc_putrecorddef_cb(r) {
//	alert("Successfully updated view");
//	window.location.reload();
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

function xmlrpc_addparamdef() { 
	var nameparam = document.getElementById('name_of_new_parameter').value;
	var parent = document.getElementById('parent_new').value;
	var choices = document.getElementById('choices_of_new_parameter').value;
	var defaultunits = document.getElementById('default_units_of_new_parameter').value;
	var vartype = document.getElementById('vartype_of_new_parameter').value;
	var property = document.getElementById('property_of_new_parameter').value;
	var desc_short = document.getElementById('short_description_of_new_parameter').value;
	var desc_long = document.getElementById('long_description_of_new_parameter').value;
}
function xmlrpc_addparamdef_cb(r) {
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

	hideclass('param_value_display_' + formobj.viewtype.value);
	showclass('param_value_edit_' + formobj.viewtype.value);
	return false;
}

function form_makeedits_cancel(formobj) {
	formobj.commit.style.display = "none";
	formobj.cancel.style.display = "none";
	formobj.edit.style.display = "block";
	
	hideclass('param_value_edit_' + formobj.viewtype.value);
	showclass('param_value_display_' + formobj.viewtype.value);
	return false;
}

function form_makeedits_putrecord(formobj) {
	newvalues = form_makeedits_collectvalues(formobj);
	xmlrpcrequest("putrecord",[newvalues,ctxid]);	
}

function form_makeedits_putnewrecord(formobj) {
	newvalues = form_makeedits_collectvalues(formobj);

	if (document.form_newrecord_generaloptions.inheritpermissions.checked) {
		parentid = parseInt(document.form_newrecord_generaloptions.permissionsparent.value);
		p = xmlrpcrequest("getrecord",[parentid,ctxid],0);
		parent = new dict();
		for (var i=0;i<p.length;i++) {
			parent[p[i][0]] = p[i][1];
		}
		newvalues.push(["permissions",parent["permissions"]]);	
	}
	xmlrpcrequest("putrecord",[newvalues,ctxid]);
}

function form_makeedits_collectvalues(formobj) {

	newvalues = new Array(["rectype",rectype]);
	if (name) {newvalues.push(["recid",name])};
	nv = new Array();

	for (var i=0;i<formobj.elements.length;i++) {

		pname = formobj.elements[i].name.split("___")[0];
		vartype = formobj.elements[i].name.split("___")[1];
		ext = formobj.elements[i].name.split("___")[2];
		num = formobj.elements[i].name.split("___")[3];

		if (formobj.elements[i].type == "submit") {continue;}

		// first let's handle simple, single-element parameters
		// skip extend elements
		if ((formobj.elements[i].type == "text" || formobj.elements[i].type == "textarea") && ext != "extendtext") {
			nv[pname] = convertvartype(vartype,formobj.elements[i].value);
		}
		
		if (formobj.elements[i].type == "select-one") {
			// is other checked?
			try {
				if (formobj.elements[pname + "___" + vartype + "___extendcheckbox___0"].checked) {
					nv[pname] = convertvartype(vartype,formobj.elements[pname + "___" + vartype + "___extendtext___0"].value);
				} else {
					nv[pname] = convertvartype(vartype,formobj.elements[i].value);
				}
			} catch(error) {	
				nv[pname] = convertvartype(vartype,formobj.elements[i].value);
			}
		}
		
		// now multiple-select types
		// check if not single-select
		if (formobj.elements[i].type == "checkbox") {
		// FIXME
			try {
				 if (formobj.elements[pname + "___" + vartype].type != "select-one") {break}
				} catch(error) {

			if (!nv[pname]) {nv[pname] = new Array()}

			if (formobj.elements[i].checked && ext != "extendcheckbox") {
				nv[pname].push(convertvartype(vartype,formobj.elements[i].value));
			}
			if (formobj.elements[i].checked && ext == "extendcheckbox") {
				nv[pname].push(convertvartype(vartype,formobj.elements[pname + "___" + vartype + "___extendtext___" + num].value));
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

callbacks["putrecord"] = new CallbackManager();
// go to new record
callbacks["putrecord"].end = function(r) {
	window.location = window.location.protocol + "//" + window.location.host + "/db/record/" + r + "?notify=" + 5;
}

function convertvartype(vartype,value) {
	if (value) {
		r = value;
//		r = "<![CDATA[" + value + "]]>";
	} else { r = null }
	return r;
}


/***********************************************/

function xmlrpc_findparamname() {
	msg = XMLRPCMessage("findparamname",[document.xmlrpc_findparamname_form.q.value]);
	xmlrpcrequest("findparamname",[document.xmlrpc_findparamname_form.q.value]);
}
function xmlrpc_findparamname_cb(r) {

}

/***********************************************/



function xmlrpc_secrecordadduser() {
	if (document.xmlrpc_secrecordadduser_form.recurse.checked) { recurse = 5; } else { recurse = 0; }
	user = document.xmlrpc_secrecordadduser_form.user.value;
	level = document.xmlrpc_secrecordadduser_form.level.value;
	
	usertuple = [[],[],[],[]];
	usertuple[level] = user;
	xmlrpcrequest("secrecordadduser",[usertuple,name,ctxid,recurse]);	
}
function xmlrpc_secrecordadduser_cb(r) {
		makeRequest("/db/permissions/" + name + "?edit=1&recurse=" + recurse,"sidebar_permissions");
}

/***********************************************/

function form_showpermissions() {
}


function xmlrpc_getrecord_perm_cb(r) {
}


function xmlrpc_secrecorddeluser(user, recid) {
	if (document.xmlrpc_secrecordadduser_form.recurse.checked) { recurse = 5; } else { recurse = 0; }
//	try {	user = parseInt(user); } catch(error) {}
	recid = parseInt(recid);
	xmlrpcrequest("secrecorddeluser",[user,recid,ctxid,recurse]);		
}
function xmlrpc_secrecorddeluser_cb(r) {
	makeRequest("/db/permissions/" + name + "?edit=1&recurse=" + recurse,"sidebar_permissions");
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
	
					if (callbacks[method]) {

						try { callbacks[method].callback(unmarshallDoc(http_request.responseXML,http_request.responseText)); }
						catch(error) {alert("Error with request.");}
						
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
		return unmarshallDoc(http_request.responseXML,http_request.responseText);
	}


}