var url = "/RPC2"; 
var currentparam = "root_recorddef";
var target = "";
var ctxid = "";
var name = "";
var pclink = "";
var newrecid;
/***********************************************/

function selecttarget() {
	write = document.getElementById(target);
	write.value = write.value + " $$" + currentparam + "=";
}

function ctxid_init_start(cookieName) {
	var sessiondid;
	var labelLen = cookieName.length;
	var cookieData = document.cookie;
	var cLen = cookieData.length;
	//alert ('cLen = length of document.cookie = ' + cLen);
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

function parambrowserinit(init,inittarget) {
	param = init || "root_parameter";
	target = inittarget || "";
	display(param,"paramdef");
}
 
function protobrowserinit(init,inittarget) {
	param = init || "root_protocol";
	target = inittarget || "";
	display(param,"recorddef");
}

function display(param,type)
{
	currentparam = param;
	browsertype = type;

	if (browsertype == "paramdef") {xmlrpcrequest("getparamdef", [param])}
	if (browsertype == "recorddef"){
		xmlrpcrequest("getrecorddef",[param]);
		makeRequest("/db/recorddefsimple/"+param,"recorddefsimple","switchin('param','mainview')");
	}

	xmlrpcrequest("getchildrenofparents",[param,type,ctxid]);
	xmlrpcrequest("getchildren",[param,type,ctxid]);
	xmlrpcrequest("getcousins",[param,type,ctxid]);
}

/***********************************************/


function xmlrpc_getchildrenofparents_cb(r) {
	p = document.getElementById('getchildrenofparents');
	while (p.firstChild) {p.removeChild(p.firstChild)};
	
	for (var i=0;i<r.length;i++) {
		var x = document.createElement('div');
		x.className = "parent";
		x.id = "asdasd";

		var xn = document.createElement('a');
		xn.href = "javascript:display('" + r[i][0] + "','" + browsertype + "')";
		xn.innerHTML = r[i][0];
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
	while (p.firstChild) {p.removeChild(p.firstChild)};	
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
//	console.log("getrecorddef: ");
//	console.log(r);
//	console.log(r[1][1]["onelineview"]);
//	console.log(r[1][1]["defaultview"]);

	f = document.getElementById("focus");
	f.innerHTML = currentparam;
	d = document.getElementById("getrecorddef");
	while (d.firstChild) {d.removeChild(d.firstChild)};	

	for (var i=0;i<r.length;i++) {
		if (r[i][0] == "creator" || r[i][0] == "creationtime") {
			k = document.createElement('span');
			k.innerHTML = r[i][0] + ": ";
			v = document.createElement('span');
			v.innerHTML = r[i][1];
			br = document.createElement('br');
			d.appendChild(k);
			d.appendChild(v);
			d.appendChild(br);
		}
	}
}


function xmlrpc_getcousins_cb(r) {
//	console.log("getcousins: " + r);
}

function xmlrpc_getparamdef_cb(r) {
//	console.log("getparamdef: "+r);
	f = document.getElementById("focus");
	f.innerHTML = currentparam;

	d = document.getElementById("getparamdef");
	while (d.firstChild) {d.removeChild(d.firstChild)};	

	for (var i=0;i<r.length;i++) {
		k = document.createElement('span');
		k.innerHTML = r[i][0] + ": ";
		v = document.createElement('span');
		v.innerHTML = r[i][1];
		br = document.createElement('br');
		d.appendChild(k);
		d.appendChild(v);
		d.appendChild(br);
	}
	
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
	alert("callback");
	document.getElementById("xmlrpc_output").value = a;
}
function xmlrpc_echo_eb(faultCode,faultString) {
	alert("error callback: " + faultCode);
}


/***********************************************/

function form_makeedits(classname) {
	toggle("form_makeedits_commit_" + classname);
	toggle("form_makeedits_clear_" + classname);
	toggle("form_makeedits_cancel_" + classname);
	hideclass('param_value_display_' + classname);
	showclass('param_value_edit_' + classname);
}
function form_makeedits_cancel(classname) {
	toggle("form_makeedits_commit_" + classname);
	toggle("form_makeedits_clear_" + classname);
	toggle("form_makeedits_cancel_" + classname);
	hideclass('param_value_edit_' + classname);
	showclass('param_value_display_' + classname);
}
function xmlrpc_putrecord(classname) {
	newvalues = new Array(["rectype",rectype]);
	if (name) {newvalues.push(["recid",name])};
	nv = new Array();
	formobj = document.forms["form_makeedits_" + classname];

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
		// this is horribly broken/ugly FIXME
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

	xmlrpcrequest("putrecord",[newvalues,ctxid]);
}
function xmlrpc_putrecord_cb(r) {
	newrecid = r;
	if (!isNaN(parseInt(pclink))) {
		xmlrpcrequest("pclink",[pclink,r,"record",ctxid]);
		return;
	}	else {
		gotorecord(r);
	}
}
function gotorecord(r) {
	if (!isNaN(parseInt(r))) {
		window.location = window.location.protocol + "//" + window.location.host + "/db/record/" + r + "?notify=2";
	} else {
		window.location = window.location.protocol + "//" + window.location.host + window.location.pathname + "?notify=" + r;
	}	
}
function convertvartype(vartype,value) {
	if (value) {
		r = value;
//		r = "<![CDATA[" + value + "]]>";
	} else { r = null }
	return r;
}

function xmlrpc_pclink_cb(r) {
	gotorecord(newrecid);
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
		makeRequest("/db/permissions/" + name + "?edit=1&recurse=" + recurse,"comments_permissions");
}

/***********************************************/

function xmlrpc_secrecorddeluser(user, recid) {
	if (document.xmlrpc_secrecordadduser_form.recurse.checked) { recurse = 5; } else { recurse = 0; }
//	try {	user = parseInt(user); } catch(error) {}
	recid = parseInt(recid);

	xmlrpcrequest("secrecorddeluser",[user,recid,ctxid,recurse]);		
}
function xmlrpc_secrecorddeluser_cb(r) {
	alert(r);
	makeRequest("/db/permissions/" + name + "?edit=1&recurse=" + recurse,"comments_permissions");
}

/***********************************************/


/***********************************************/


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
            alert('There was a problem with the request.');
        }
    }

}


function dbgetrequest(url,command,param) {
	//standard
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
        alert('Giving up :( Cannot create an XMLHTTP instance');
        return false;
    }
		//end
		http_request.onreadystatechange=function() { statechange(http_request,command,param,"None"); };
		http_request.open("GET",url,true);	
		http_request.send(null);
}


// simple xmlrpc request

function dbxmlrpcrequest(command,param,type) {
	//standard
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
        alert('Giving up: Cannot create an XMLHTTP instance');
        return false;
    }
		//end
		
		http_request.onreadystatechange=function() { statechange(http_request,command,param,type); };
		http_request.open("POST",url,true);
		if (command == "getparamdef2") {
			var request = '<methodCall><methodName>getparamdef2</methodName><params><param><value><string>' + param + '</string></value></param></params></methodCall>';
		} else {
//			alert("req: " + command + " .. ctxid: " + ctxid);
			var request = '<methodCall><methodName>'+ command +'</methodName><params><param><value><string>'+param+'</string></value> </param><param><value><string>' + type + '</string> </value> </param> <param><value><string>' + ctxid + '</string></value> </param></params></methodCall>';	
		}
		http_request.send(request);
}


function xmlrpcmultirequest(methods) {	
}

// raw xmlrpc request
function xmlrpcrequest(method,args) {

		command = XMLRPCMessage(method,args);

//		try {	eval("cb = xmlrpc_" + method + "_cb");alert(method);} catch(error) {cb=function(a){}}
//		try {	eval("eb = xmlrpc_" + method + "_eb");} catch(error) {eb=function(faultCode,faultString){alert("Error code "+faultCode+", "+faultString)}}
		
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
        alert('Giving up :( Cannot create an XMLHTTP instance');
        return false;
    }
		//end
		http_request.onreadystatechange=function()
 		{		
			if (http_request.readyState==4)
	  		{
	  			if (http_request.status==200)
	  			{	

					try {
//						cb;
//							try {	eval("cb = xmlrpc_" + method + "_cb(unmarshallDoc(http_request.responseXML,http_request.responseText))");alert(method);} catch(error) {cb=function(unmarshallDoc(http_request.responseXML,http_request.responseText)){}}
							eval("cb = xmlrpc_" + method + "_cb(unmarshallDoc(http_request.responseXML,http_request.responseText))")

					} catch(error) {
//						eb(error.faultCode,error.faultString);
//							try {	eval("eb = xmlrpc_" + method + "_eb");} catch(error) {eb=function(faultCode,faultString){alert("Error code "+faultCode+", "+faultString)}}
							alert("Error code "+error.faultCode+", "+error.faultString)
					}

					}
	  			else
	  			{
						alert("Error with request.");
	  			}
	  		}
		}
		http_request.open("POST",url,true);
		http_request.send(command);
}