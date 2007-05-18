var url = "/RPC2"; 
currentparam = "root";
target = "";
ctxid = "";
name = "";

function selecttarget() {
//	alert(target);
	write = document.getElementById(target);
	write.value = write.value + " $$" + currentparam + "=";
//	alert("writing " + currentparam + " to " + target);
}

function ctxid_init_start(cookieName) 
{
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
//				alert("Setting ctxid:" + ctxid);
			}
		i++;
	}
}

function parambrowserinit(init,inittarget) {
	param = init || "root";
	target = inittarget || "";
//	ctxid_init_start('TWISTED_SESSION_ctxid')
	display(param,"paramdef");
}
 
function protobrowserinit(init,inittarget) {
	param = init || "folder";
	target = inittarget || "";
//	ctxid_init_start('TWISTED_SESSION_ctxid')
	display(param,"recorddef");
}

function display(param,type)
{
	currentparam = param;
	if (type == "paramdef") {
		var commands=new Array("getchildrenofparents","getchildren","getparamdef2", "getcousins")
	} 
	if (type == "recorddef") { 
		var commands=new Array("getchildrenofparents","getchildren", "getrecorddef2", "getcousins")
	}
	for (var i=0;i<commands.length;i++) { dbxmlrpcrequest(commands[i],param,type); }
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


// raw xmlrpc request
function dbxmlrpcrequestraw(command,callback) {

	try {
		input = document.getElementById("xmlrpc_input");
		input.value = command;
	} catch(error) {
	}

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
		http_request.onreadystatechange=function()
 		{		
			if (http_request.readyState==4)
	  		{
	  			if (http_request.status==200)
	  			{	
						try {
							output = document.getElementById("xmlrpc_output");
							output.value = http_request.responseText;
						} catch(errror) {}
						eval(callback);
//						window.location.reload();
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


// fixme cleanup
function statechange(http_request,command,param,type) {

    if (http_request.readyState == 4) {
        if (http_request.status == 200) {
						b = document.getElementById(command);
						response = http_request.responseXML;
						responsetext = http_request.responseText;
						c = document.getElementById("focus");
						c.innerHTML = param;
						d = document.getElementById("viewfull");
						if (type != "None") {d.setAttribute("href","/db/" + type + "?name=" + param);}
						
						if (command == "getchildrenofparents") {
							var array = new Array();
							var parents = response.getElementsByTagName('array');
							for(var j = 1; j < parents.length; j = j + 1) {
								parent = parents[j].childNodes[0].getElementsByTagName('string');
								parentname = parent[0].firstChild.nodeValue;
								itemsarray = new Array();
								for(var k = 1; k < parent.length;  k = k + 1) {
									itemsarray.push(parent[k].firstChild.nodeValue);
								}
								array[parentname] = itemsarray;
							}
							string = "";
							string_parentfield = "";

							parentfield = document.getElementById("parent_of_new_parameter")
														
							for(i in array) {
//							string_parentfield = i + " " + string_parentfield
							string_parentfield = i
							string = string + '<div class="parent"><a onClick="display(\'' + i + '\',\'' + type + '\')">' + i + '</a></div><div class="parents">';
								for(z in array[i]) {
									string = string + '<span class="child"><a onClick="display(\'' + array[i][z] + '\',\'' + type + '\')">' + array[i][z] + '</a></span> ';
								}
							string = string + "</div>";
							}
							b.innerHTML = string;	
							try {parentfield.value = string_parentfield;} catch(error) {}
						}

						if (command == "getchildren" || command == "getcousins") {
							if (command == "getchildren") {z="children"} else {z="cousins"}
							var x = response.getElementsByTagName('string');
							if (x.length ==0) {
								b.innerHTML = ''; return;
							}
							string = '<div class="parent">' + z + '</div><div class="parents">';
							for(var ii = 0; ii < x.length; ii= ii + 1) {
        				var e = x[ii];
								var param = e.firstChild.nodeValue;
								string = string + '<span class="child"><a onClick="display(\'' + param + '\',\'' + type + '\')">' + param + '</a></span> ';
							}
							string = string + "</div>";
							b.innerHTML = string;				
						}
										

						if (command == "getparamdef2") {
							var parents = response.getElementsByTagName('array');
							string = ""
							for(var j = 1; j < parents.length; j=j+1) {
								z = parents[j].getElementsByTagName('string')
								try { v = z[1].firstChild.nodeValue } catch(e) {v = ""}
								try { string = string + z[0].firstChild.nodeValue + ": "  + v + "<br />"; } catch(e) {string = ""}
							}
							b.innerHTML = string;
						}


					if (command == "getrecorddef2") {
						string = ""
						var parents = response.getElementsByTagName('string');
						for (var j = 0; j < parents.length; j = j+1) {
							val = parents[j].firstChild.nodeValue
							if (val == "creator=") {
								string = string + "Creator: " + parents[j+1].firstChild.nodeValue + "<br />";
							}
							if (val == "creationtime=") {
								string = string + "Created: " + parents[j+1].firstChild.nodeValue + "<br />";
							}
							if (val == "owner=") {
								string = string + "Owner: " + parents[j+1].firstChild.nodeValue  + "<br />";
							}
							if (val == "private=") {
								string = string + "Private: " + parents[j+1].firstChild.nodeValue  + "<br />";
							}
						}
						b.innerHTML = string;
						dbgetrequest("/db/recorddefsimple?name=" + param, "recorddefsimple", param)
					}
					
					if (command == "recorddefsimple") {
						b.innerHTML = responsetext;
						try {switchin("param","mainview");} catch(error) {}
					}


        } else {
          alert('There was a problem with the request.');
					response = "";
        }
    }
}



function make_param() { 
	var name = document.getElementById('name_of_new_parameter').value;
	var parent = document.getElementById('parent_new').value;
	var choices = document.getElementById('choices_of_new_parameter').value;
	var defaultunits = document.getElementById('default_units_of_new_parameter').value;
	var vartype = document.getElementById('vartype_of_new_parameter').value;
	var property = document.getElementById('property_of_new_parameter').value;
	var desc_short = document.getElementById('short_description_of_new_parameter').value;
	var desc_long = document.getElementById('long_description_of_new_parameter').value;

	var xmlhttp = new XMLHttpRequest();  //add for other browsers; make a function that returns these objects
	xmlhttp.onreadystatechange = function() 
		{		
			if (xmlhttp.readyState==4)
	  		{
	  			if (xmlhttp.status==200)
	  			{	
					alert("Parameter added successfully");
				}
	  			else
	  			{
					alert("Problem retrieving data:" + xmlhttp.statusText);
					alert("xmlhttp3.status is  " + xmlhttp.status)
	  			}
					
	  		}
		}
	xmlhttp.open("POST",url,true);
	var request = "<methodCall> <methodName>addparamdef2</methodName> <params> <param> <value> <string>" + name + "</string> </value> </param> <param> <value> <string>" + ctxid + "</string></value></param><param> <value> <string>" + parent + "</string> </value> </param><param> <value> <string>" + vartype + "</string> </value> </param><param> <value> <string>" + desc_short + "</string> </value> </param><param> <value> <string>" + desc_long + "</string> </value> </param><param> <value> <string>" + property + "</string> </value> </param><param> <value> <string>" + defaultunits + "</string> </value> </param><param> <value> <string>" + choices + "</string> </value> </param></params></methodCall>";

	xmlhttp.send(request);
}



function xmlrpc_makeedits() {
//	t = document.getElementById("xmlrpc_makeedit");
//	t.innerHTML = "<span class=\"jslink\" onclick=\"javascript:makeedits_commit()\">Update</span> : <span  class=\"jslink\" id=\"makeedit_edit\" onclick=\"javascript:makeedits()\">Clear Form</span> : <span class=\"jslink\"  onclick=\"javascript:makeedits_cancel()\">Cancel</span>"
//#xmlrpc_makeedits_commit, #xmlrpc_makeedits_cancel
	toggle("xmlrpc_makeedits_commit");
	toggle("xmlrpc_makeedits_clear");
	toggle("xmlrpc_makeedits_cancel");
	
	hideclass('page_recordview');
	qshow('page_recordview_dicttable');

	list = getElementByClass("viewparam_value");
	for (var i=0;i<list.length;i=i+1) {

		value = document.getElementById(list[i] + "_2").innerHTML;
		if (typeof oldvalues[list[i]] == 'undefined') {oldvalues[list[i]] = value;}
		
		if (value.length > 80) {
			var newinput = document.createElement("textarea");
			newinput.cols = 70;
			newinput.rows = 8;
			newinput.value = value;
			newinput.id = list[i] + "_2";
		} else {
			var newinput = document.createElement("input");
			newinput.type = "text";
			newinput.value = value;
			if (value.length > 0) {newinput.size = value.length;} else {newinput.size = 60;}
			newinput.id = list[i] + "_2";
		}

    var para = document.getElementById(list[i]);
    var spanElm = document.getElementById(list[i] + "_2");
    var replaced = para.replaceChild(newinput,spanElm);
	}
}

function xmlrpc_makeedits_cancel() {

	toggle("xmlrpc_makeedits_commit");
	toggle("xmlrpc_makeedits_clear");
	toggle("xmlrpc_makeedits_cancel");
	
	list = getElementByClass("viewparam_value");
		
	for (var i=0;i<list.length;i=i+1){
		value = oldvalues[list[i]];
		var element = document.createElement("span");
		element.id = list[i] + "_2";
		element.innerHTML = value;
		
		var para = document.getElementById(list[i]);
		var old = document.getElementById(list[i] + "_2");
		var replaced = para.replaceChild(element,old);
	}

//	t = document.getElementById("xmlrpc_makeedit");
//	t.innerHTML = "<span  class=\"jslink\"  onclick=\"javascript:makeedits()\">Edit</span>";
	
}


// fixme: switch to xmlrpc.js
function xmlrpc_makeedits_commit() {
//	ctxid_init_start('TWISTED_SESSION_ctxid');
// 	recordid = document.getElementById('recordid').value;

	list = getElementByClass("viewparam_value");

	xmlcommand1 = "<methodCall><methodName>putrecord</methodName><params><param><value><int>" + name + "</int></value></param><param><value><array>";
	xmlcommand2 = "";
//	xmlcommand3 = "<param><value><string>" + ctxid + "</string></value></param></params></methodCall>";
	xmlcommand3 = "</array></value></param><param><value><string>" + ctxid + "</string></value></param></params></methodCall>";

	for (var i=0;i<list.length;i=i+1){
		value = document.getElementById(list[i] + "_2").value;
		xmlcommand2 = xmlcommand2 + "<param><value><array><param><value><string>" + list[i] + "</string></value></param><param><value><string><![CDATA[" + value + "]]></string></value></param></array></value></param>";
	}
//	output = document.getElementById("output");
//	output.innerHTML = xmlcommand1 + xmlcommand2 + xmlcommand3;
	dbxmlrpcrequestraw(xmlcommand1 + xmlcommand2 + xmlcommand3,"window.location=window.location + '&notify=5*6'");

}





function makeRequest(url,zone) {
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
    http_request.onreadystatechange = function() { alertContents(http_request,zone); };
    http_request.open('GET', url, true);
    http_request.send(null);
}

function alertContents(http_request,zone) {

    if (http_request.readyState == 4) {
        if (http_request.status == 200) {
						document.getElementById(zone).innerHTML  = http_request.responseText;
//                alert(http_request.responseText);
        } else {
//window.location.reload()
            alert('There was a problem with the request.');
        }
    }

}


function xmlrpc_findparamname() {
	var msg = new XMLRPCMessage("findparamname");
	msg.addParameter(document.xmlrpc_findparamname_form.q.value);
	dbxmlrpcrequestraw(msg.xml(),"findparamname_refresh(http_request.responseXML);");
}

function findparamname_refresh(response) {
	root = response.documentElement;
	params = root.firstChild;
	param = params.firstChild;
	alert(param.length);
//	alert(array.length);
//	alert(params)
//	alert(arrays.length);
	
}


function xmlrpc_secrecordadduser() {
	if (document.xmlrpc_secrecordadduser_form.recurse.checked) { recurse = 5; } else { recurse = 0; }
	user = document.xmlrpc_secrecordadduser_form.user.value;
	level = document.xmlrpc_secrecordadduser_form.level.value;
	
	usertuple = [[],[],[],[]];
	usertuple[level] = user;
	var msg = new XMLRPCMessage("secrecordadduser"); 
	msg.addParameter(usertuple);
	msg.addParameter(name);
	msg.addParameter(ctxid);
	msg.addParameter(recurse);
	dbxmlrpcrequestraw(msg.xml(),null);
	
	makeRequest("/db/permissions?name=" + name + "&edit=1&recurse=" + recurse,"comments_permissions");
	
}

function xmlrpc_secrecorddeluser(user, recid) {
	if (document.xmlrpc_secrecordadduser_form.recurse.checked) { recurse = 5; } else { recurse = 0; }
//	try {	user = parseInt(user); } catch(error) {}
	recid = parseInt(recid);

	var msg = new XMLRPCMessage("secrecorddeluser"); 
	msg.addParameter(user);
	msg.addParameter(recid);
	msg.addParameter(ctxid);
	msg.addParameter(recurse);

	dbxmlrpcrequestraw(msg.xml(),null);
	
	makeRequest("/db/permissions?name=" + name + "&edit=1&recurse=" + recurse,"comments_permissions");
	
}