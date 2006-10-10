var url = "/RPC2"; 
currentparam = "folder";
target = "";

function selecttarget() {
	write = document.getElementById("form_comment");
	write.value = write.value + " $$" + currentparam + "=";
//	alert("writing " + currentparam + " to " + target);
}

function get_ctxid_from_cookie(cookieName) 
{
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
			return unescape(cookieData.substring(j+1,cEnd));
			}
		i++;
	}
	return "";
}

function protobrowserinit(init,inittarget) {
	param = init || "117";
	target = inittarget || "";
	ctxid = get_ctxid_from_cookie('TWISTED_SESSION')
//	toggle("parambrowser");
	display(param);
}
 
function display(param)
{
	currentparam = param;
	var commands=new Array("getchildrenofparents","getchildren", "getcousins", "getrecorddef2")
	for (var i=0;i<commands.length;i++) { dbxmlrpcrequest(commands[i],param); }
}

function dbxmlrpcrequest(command,param) {
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
		http_request.onreadystatechange=function() { statechange(http_request,command,param); };
		http_request.open("POST",url,true);
//		if (command == "getrecorddef2") {
//			var request = '<methodCall><methodName>' + command + '</methodName><params><param><value><string>' + param + //'</string></value></param></params></methodCall>';
//		} else {
			var request = '<methodCall><methodName>'+ command +'</methodName><params><param><value><string>'+param+'</string></value> </param><param><value><string>recorddef</string> </value> </param> <param><value><string>ctxid=' + ctxid + '</string></value> </param></params></methodCall>';	
//		}
		http_request.send(request);
}

function statechange(http_request,command,param) {

    if (http_request.readyState == 4) {
        if (http_request.status == 200) {
						b = document.getElementById(command);
						response = http_request.responseXML;
						responsetext = http_request.responseText;
//						alert(responsetext)
						c = document.getElementById("focus");
						c.innerHTML = param;
						d = document.getElementById("viewfull");
						d.setAttribute("href","/db/paramdef?name=" + param);
						e = document.getElementById('form_comment');
						estr = e.value;
						e.value = estr + "\n\n" + command + "\n" + responsetext;
						
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
							for(i in array) {
							string = string + '<div class="parent"><a onClick="display(\'' + i + '\')">' + i + '</a></div><div class="parents">';
								for(z in array[i]) {
									string = string + '<span class="child"><a onClick="display(\'' + array[i][z] + '\')">' + array[i][z] + '</a></span> ';
								}
							string = string + "</div>";
							}
							b.innerHTML = string;	
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
								string = string + '<span class="child"><a onClick="display(\'' + param + '\')">' + param + '</a></span> ';
							}
							string = string + "</div>";
							b.innerHTML = string;				
						}
										

						if (command == "getrecorddef2") {
							
							regex = new RegExp(">;<","g");
							responsetext = responsetext.replace(regex,"><br /><br /><");
							
							b = document.getElementById("getrecorddef2");
							b.innerHTML = responsetext;
//							var parents = response.getElementsByTagName('array');						
//							string = ""
//							for(var j = 1; j < parents.length; j=j+1) {
//								z = parents[j].getElementsByTagName('string')
//								try { v = z[1].firstChild.nodeValue } catch(e) {v = ""}
//								string = string + z[0].firstChild.nodeValue + ": "  + v + "<br />";
//							}
//							b.innerHTML = string;
						}



        } else {
          alert('There was a problem with the request.');
					response = "";
        }
    }
}



function make_param() { 
	var name = document.getElementById('name_of_new_parameter').value;
	var parent = document.getElementById('parent_of_new_parameter').value;
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
					alert("Problem retrieving data:" + xmlhttp3.statusText);
					alert("xmlhttp3.status is  " + xmlhttp3.status)
	  			}
					
	  		}
		}
	xmlhttp.open("POST",url,true);
	var request = "<methodCall> <methodName>addparamdef2</methodName> <params> <param> <value> <string>" + name + "</string> </value> </param> <param> <value> <string>" + ctxid + "</string></value></param><param> <value> <string>" + parent + "</string> </value> </param><param> <value> <string>" + vartype + "</string> </value> </param><param> <value> <string>" + desc_short + "</string> </value> </param><param> <value> <string>" + desc_long + "</string> </value> </param><param> <value> <string>" + property + "</string> </value> </param><param> <value> <string>" + defaultunits + "</string> </value> </param><param> <value> <string>" + choices + "</string> </value> </param></params></methodCall>";

	xmlhttp.send(request);
}
