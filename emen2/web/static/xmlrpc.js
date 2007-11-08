var url = "/RPC2"; 

function getxmlhttprequest() {
	var request = window.XMLHttpRequest ? new XMLHttpRequest() : new ActiveXObject("Microsoft.XMLHTTP");
	return request
}

/***********************************************/


function makeRequest(url,zone) {
	var http_request = getxmlhttprequest();
	http_request.onreadystatechange = function() {
		if (http_request.readyState == 4) {
			if (http_request.status == 200) {
				document.getElementById(zone).innerHTML  = http_request.responseText;
 			} else {
				alert('Error with request: network');
			}
		}
	};
	http_request.open('GET', url, true);
	http_request.send(null);
}



/***********************************************
*********** Callback Manager *******************
***********************************************/

function CallbackManager() {

	var f = new Array();
	var cbargs = null;
	var end = function (r) {};
	var e = function(r) {topalert("Error: " +r.faultString)};
	var xmlhttprequest=getxmlhttprequest();
	
	
	this.register = function(callbackFunction) {
		f.push(callbackFunction);
	}
	this.setcbargs = function(r) {
		cbargs=r;
	}
	this.setend = function(r) {
		end=r;
	}
	this.seterror = function (r) {
		error=r;
	}
	this.req = function(method,args) {
		command = XMLRPCMessage(method,args);
		xmlhttprequest.open("POST",url,true);
		xmlhttprequest.send(command);
	}

	callback = function(r) {
		if (xmlhttprequest.readyState==4) {
			if (xmlhttprequest.status==200)	{
				try {
					r=unmarshallDoc(xmlhttprequest.responseXML,xmlhttprequest.responseText);
				} catch(error) {
					//console.log(error);
					topalert("Error: "+error.faultString);
					return
				}

 				try {
 					for (var i=0;i<f.length;i++) {
 						f[i](r,cbargs);
 					}
 					end(r);
 				} catch(error) {
					//console.log(error);
 				}				
			}
		}
	}
	xmlhttprequest.onreadystatechange=callback;

}

/***** end callback manager *****/


/********************************************/


function XMLRPCMessage(methodName,args) {
 	        var data='<?xml version="1.0"?><methodCall><methodName>' + methodName + '</methodName>';
 	        if(args.length>0){
 	            data += "<params>";
 	            for(var i=0;i<args.length;i++){
 	                data += '<param><value>' + marshall(args[i]) + '</value></param>';
 	            }
 	            data += '</params>';
 	        }
 	        data += '</methodCall>';
 	        return data;
 	   
}

/******************************************/



/**
    Thrown if a  server did not respond with response status 200 (OK).
*/
function InvalidServerResponse(status){
};

/**
    Thrown if an XML-RPC response is not well formed.
*/
function MalformedXmlRpc(msg, xml, trace){
};
/**
    Thrown if the RPC response is a Fault.
*/
function Fault(faultCode, faultString){
//	alert("faultcode: " + faultCode);
//	alert("faultstring: " + faultString);
	this.faultCode = faultCode;
	this.faultString = faultString;
//	return faultCode, faultstring;
};

/**
    Marshalls an object to XML-RPC.(Converts an object into XML-RPC conforming xml.)
    It just calls the toXmlRpc function of the objcect.
    So, to customize serialization of objects one just needs to specify/override the toXmlRpc method
    which should return an xml string conforming with XML-RPC spec.
    @param obj    The object to marshall
    @return         An xml representation of the object.
*/
function marshall(obj){
		if (obj == null) {
				return "<nil/>";
		}
    if(obj.toXmlRpc!=null){
        return obj.toXmlRpc();
    }else{
        var s = "<struct>";
        for(var attr in obj){
            if(typeof obj[attr] != "function"){
                s += "<member><name>" + attr + "</name><value>" + marshall(obj[attr]) + "</value></member>";
            }
        }
        s += "</struct>";
        return s;
    }
};


function unmarshall(xml){
/*    try {//try to parse xml ... this will throw an Exception if failed
        var doc = parseXML(xml);
    }catch(e){
        throw new MalformedXmlRpc("The server's response could not be parsed.", xml, e);
    }
    var rslt = unmarshallDoc(doc, xml);
    doc=null;
    return rslt;
*/
	alert("Unimplemted");
	return "Unimplemented";
};


function unmarshallDoc(doc, xml){
    try{
        var node = doc.documentElement;
        if(node==null){//just in case parse xml didn't throw an Exception but returned nothing usefull.
            throw new MalformedXmlRpc("No documentElement found.", xml);
        }
        switch(node.tagName){
            case "methodResponse":
                return parseMethodResponse(node);
            case "methodCall":
                return parseMethodCall(node);
            default://nothing usefull returned by parseXML.
                throw new MalformedXmlRpc("'methodCall' or 'methodResponse' element expected.\nFound: '" + node.tagName + "'", xml);
        }
    }catch(e){
        if(e.constructor == Fault){//just rethrow the fault.
            throw e;
        }else {
            throw new MalformedXmlRpc("Unmarshalling of XML failed.", xml, e);
        }
    }
};

/**
    Parses a methodeResponse element.
    @param node  The methodResponse element.
    @return          The return value of the XML-RPC.
*/
var parseMethodResponse=function(node){
    try{
        for(var i=0;i<node.childNodes.length;i++){
            var child = node.childNodes.item(i);
            if(child.nodeType == 1){
                switch(child.tagName){
                    case "fault": //a fault is thrown as an Exception
                        throw parseFault(child);
                    case "params":
                        var params = parseParams(child);
                        if(params.length == 1){//params should only have one param
                            return params[0];
                        }else{
                            throw new MalformedXmlRpc("'params' element inside 'methodResponse' must have exactly ONE 'param' child element.\nFound: " + params.length);
                        }
                    default:
                        throw new MalformedXmlRpc("'fault' or 'params' element expected.\nFound: '" + child.tagName + "'");
                }
            }
        }
        //no child elements found
        throw new MalformedXmlRpc("No child elements found.");
    }catch(e){
        if(e.constructor == Fault){
            throw e;
        }else{
            throw new MalformedXmlRpc("'methodResponse' element could not be parsed.",null,e);
        }
    }
};
/**
    Parses a methodCall element.
    @param node  The methodCall element.
    @return          Array [methodName,params].
*/
var parseMethodCall = function(node){
    try{
        var methodName = null;
        var params = new Array();//default is no parameters
        for(var i=0;i<node.childNodes.length;i++){
            var child = node.childNodes.item(i);
            if(child.nodeType == 1){
                switch(child.tagName){
                    case "methodName":
                        methodName = new String(child.firstChild.nodeValue);
                        break;
                    case "params":
                        params = parseParams(child);
                        break;
                    default:
                        throw new MalformedXmlRpc("'methodName' or 'params' element expected.\nFound: '" + child.tagName + "'");
                }
            }
        }
        if(methodName==null){
            throw new MalformedXmlRpc("'methodName' element expected.");
        }else{
            return new Array(methodName, params);
        }
    }catch(e){
        throw new MalformedXmlRpc("'methodCall' element could not be parsed.",null,e);
    }
};
/**
    Parses a params element.
    @param node  The params element.
    @return          Array of params values.
*/
var parseParams = function(node){
    try{
        var params=new Array();
        for(var i=0;i<node.childNodes.length;i++){
            var child = node.childNodes.item(i);
            if(child.nodeType == 1){
                switch(child.tagName){
                    case "param":
                        params.push(parseParam(child));
                        break;
                    default:
                        throw new MalformedXmlRpc("'param' element expected.\nFound: '" + child.tagName + "'");
                }
            }
        }
        //the specs say a 'params' element can contain any number of 'param' elements. That includes 0 ?!
        return params;
    }catch(e){
        throw new MalformedXmlRpc("'params' element could not be parsed.",null,e);
    }
};
/**
    Parses a param element.
    @param node  The param node.
    @return          The value of the param.
*/
var parseParam = function(node){
    try{
        for(var i=0;i<node.childNodes.length;i++){
            var child = node.childNodes.item(i);
            if(child.nodeType == 1){
                switch(child.tagName){
                    case "value":
                        return parseValue(child);
                    default:
                        throw new MalformedXmlRpc("'value' element expected.\nFound: '" + child.tagName + "'");
                }
            }
        }
        //no child elements found, that's an error
        throw new MalformedXmlRpc("'value' element expected.But none found.");
    }catch(e){
        throw new MalformedXmlRpc("'param' element could not be parsed.",null,e);
    }
};
/**
    Parses a value element.
    @param node  The value element.
    @return         The value.
*/
var parseValue = function(node){
    try{
        for(var i=0;i<node.childNodes.length;i++){
            var child = node.childNodes.item(i);
            if(child.nodeType == 1){
                switch(child.tagName){
                    case "string":
                        var s="";
                        //Mozilla has many textnodes with a size of 4096 chars each instead of one large one.
                        //They all need to be concatenated.
                        for(var j=0;j<child.childNodes.length;j++){
                            s+=new String(child.childNodes.item(j).nodeValue);
                        }
                        return s;
                    case "int":
                    case "i4":
                    case "double":
                        return (child.firstChild) ? Number(child.firstChild.nodeValue) : 0;
                    case "boolean":
                        return Boolean(isNaN(parseInt(child.firstChild.nodeValue)) ? (child.firstChild.nodeValue == "true") : parseInt(child.firstChild.nodeValue));
                    case "base64":
                        return parseBase64(child);
                    case "dateTime.iso8601":
                        return parseDateTime(child);
                    case "array":
                        return parseArray(child);
                    case "struct":
                        return parseStruct(child);
                    case "nil": //for python None todo: ??? is this valid XML-RPC
                        return null;
                    default:
                        throw new MalformedXmlRpc("'string','int','i4','double','boolean','base64','dateTime.iso8601','array' or 'struct' element expected.\nFound: '" + child.tagName + "'");
                }
            }
        }
        if(node.firstChild){
            var s="";
            //Mozilla has many textnodes with a size of 4096 chars each instead of one large one.
            //They all need to be concatenated.
            for(var j=0;j<node.childNodes.length;j++){
                s+=new String(node.childNodes.item(j).nodeValue);
            }
            return s;
        }else{
            return "";
        }
    }catch(e){
        throw new MalformedXmlRpc("'value' element could not be parsed.",null,e);
    }
};
/**
    Parses a base64 element.
    @param node   The base64 element.
    @return          A string with the decoded base64.
*/
var parseBase64=function(node){
    try{
        var s = node.firstChild.nodeValue;
        return s.decode("base64");
    }catch(e){
        throw new MalformedXmlRpc("'base64' element could not be parsed.",null,e);
    }
};
/**
    Parses a dateTime.iso8601 element.
    @param node   The dateTime.iso8601 element.
    @return           A JavaScript date.
*/
var parseDateTime=function(node){
    try{
        if(/^(\d{4})-?(\d{2})-?(\d{2})T(\d{2}):?(\d{2}):?(\d{2})/.test(node.firstChild.nodeValue)){
            return new Date(Date.UTC(RegExp.$1, RegExp.$2-1, RegExp.$3, RegExp.$4, RegExp.$5, RegExp.$6));
        }else{ //todo error message
            throw new MalformedXmlRpc("Could not convert the given date.");
        }
    }catch(e){
        throw new MalformedXmlRpc("'dateTime.iso8601' element could not be parsed.",null,e);
    }
};
/**
    Parses an array element.
    @param node   The array element.
    @return           An Array.
*/
var parseArray=function(node){
    try{
        for(var i=0;i<node.childNodes.length;i++){
            var child = node.childNodes.item(i);
            if(child.nodeType == 1){
                switch(child.tagName){
                    case "data":
                        return parseData(child);
                    default:
                        throw new MalformedXmlRpc("'data' element expected.\nFound: '" + child.tagName + "'");
                }
            }
        }
        throw new MalformedXmlRpc("'data' element expected. But not found.");
    }catch(e){
        throw new MalformedXmlRpc("'array' element could not be parsed.",null,e);
    }
};
/**
    Parses a data element.
    @param node   The data element.
    @return           The value of a data element.
*/
var parseData=function(node){
    try{
        var rslt = new Array();
        for(var i=0;i<node.childNodes.length;i++){
            var child = node.childNodes.item(i);
            if(child.nodeType == 1){
                switch(child.tagName){
                    case "value":
                        rslt.push(parseValue(child));
                        break;
                    default:
                        throw new MalformedXmlRpc("'value' element expected.\nFound: '" + child.tagName + "'");
                }
            }
        }
        return rslt;
    }catch(e){
        throw new MalformedXmlRpc("'data' element could not be parsed.",null,e);
    }
};
/**
    Parses a struct element.
    @param node   The struct element.
    @return           A JavaScript object. Struct memembers are properties of the object.
*/
var parseStruct=function(node){
    try{
        var struct = new Object();
        for(var i=0;i<node.childNodes.length;i++){
            var child = node.childNodes.item(i);
            if(child.nodeType == 1){
                switch(child.tagName){
                    case "member":
                        var member = parseMember(child); //returns [name, value]
                        if(member[0] != ""){
                            struct[member[0]] = member[1];
                        }
                        break;
                    default:
                        throw new MalformedXmlRpc("'data' element expected.\nFound: '" + child.tagName + "'");
                }
            }
        }
        return struct;
    }catch(e){
        throw new MalformedXmlRpc("'struct' element could not be parsed.",null,e);
    }
};
/**
    Parses a member element.
    @param node  The member element.
    @return          Array containing [memberName, value].
*/
var parseMember=function(node){
    try{
        var name="";
        var value=null;
        for(var i=0;i<node.childNodes.length;i++){
            var child = node.childNodes.item(i);
            if(child.nodeType == 1){
                switch(child.tagName){
                    case "value":
                        value = parseValue(child);
                        break;
                    case "name":
                        if(child.hasChildNodes()){
                            name = new String(child.firstChild.nodeValue);
                        }
                        break;
                    default:
                        throw new MalformedXmlRpc("'value' or 'name' element expected.\nFound: '" + child.tagName + "'");
                }
            }
        }
        /*if(name == ""){
            throw new MalformedXmlRpc("Name for member not found/convertable.");
        }else{
            return new Array(name, value);
        }*/
        return [name, value];
    }catch(e){
        throw new MalformedXmlRpc("'member' element could not be parsed.",null,e);
    }
};
/**
    Parses a fault element.
    @param node  The fault element.
    @return          A Fault Exception object.
*/
var parseFault = function(node){
    try{
        for(var i=0;i<node.childNodes.length;i++){
            var child = node.childNodes.item(i);
            if(child.nodeType == 1){
                switch(child.tagName){
                    case "value":
                        var flt = parseValue(child);
                        return new Fault(flt.faultCode, flt.faultString);
                    default:
                        throw new MalformedXmlRpc("'value' element expected.\nFound: '" + child.tagName + "'");
                }
            }
        }
        throw new MalformedXmlRpc("'value' element expected. But not found.");
    }catch(e){
        throw new MalformedXmlRpc("'fault' element could not be parsed.",null,e);
    }
};



/**
    XML-RPC representation of a string.
    All '&' and '<' are replaced with the '&amp;'  and  '&lt'.
    @return  A string containing the String's representation in XML.
*/

String.prototype.toXmlRpc = function(){
		if (this == "null") { return "<nil/>" }
    return "<string>" + this.replace(/&/g, "&amp;").replace(/</g, "&lt;") + "</string>";
};
/**
    XML-RPC representation of a number.
    @return A string containing the Number's representation in XML.
*/
Number.prototype.toXmlRpc = function(){
    if(this == parseInt(this)){
        return "<int>" + this + "</int>";
    }else if(this == parseFloat(this)){
        return "<double>" + this + "</double>";
    }else{
        return false.toXmlRpc();
    }
};
/**
    XML-RPC representation of a boolean.
    @return A string containing the Boolean's representation in XML.
*/
Boolean.prototype.toXmlRpc = function(){
    if(this == true) {
        return "<boolean>1</boolean>";
    }else{
        return "<boolean>0</boolean>";
    }
};
/**
    XML-RPC representation of a date(iso 8601).
    @return A string containing the Date's representation in XML.
*/
Date.prototype.toXmlRpc = function(){
    var padd=function(s, p){
        s=p+s;
        return s.substring(s.length - p.length);
    };
    var y = padd(this.getUTCFullYear(), "0000");
    var m = padd(this.getUTCMonth() + 1, "00");
    var d = padd(this.getUTCDate(), "00");
    var h = padd(this.getUTCHours(), "00");
    var min = padd(this.getUTCMinutes(), "00");
    var s = padd(this.getUTCSeconds(), "00");
    //Alex suggested to add milliseconds support and send me a patch
    //Thanks for the great effort, Alex.
    var ms = padd(this.getUTCMilliseconds(), "000");

    var isodate = y +  m  + d + "T" + h +  ":" + min + ":" + s + ":" + ms;

    return "<dateTime.iso8601>" + isodate + "</dateTime.iso8601>";
};
/**
    XML-RPC representation of an array.
    Each entry in the array is a value in the XML-RPC.
    @return A string containing the Array's representation in XML.
*/
Array.prototype.toXmlRpc = function(){
    var retstr = "<array><data>";
    for(var i=0;i<this.length;i++){
        retstr += "<value>" + marshall(this[i]) + "</value>";
    }
    return retstr + "</data></array>";
};
