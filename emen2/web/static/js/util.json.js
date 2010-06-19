///////// get data /////////////////////

function json_getparamdef(recids,cb) {
	$.jsonRPC(
		"getparamdef",
		[recids],
		function (json) {
			$.each(json, function(i) {
				paramdefs[this.name]=this;
			});
			cb();
		}
	);
}



function json_getrecords(recids,cb) {
	$.jsonRPC(
		"getrecord",
		[recids],
		function (json) {
			$.each(json, function(i) {
				setrecord(this["recid"],this);
			});
			cb();
		}
	);	
}



////////////////  base ///////////////////




$.postJSON = function(uri,data,callback,errback,dataType) {
	if (!errback) {
		errback = function(xhr){
				notify("Error: "+xhr.responseText);
			}
		}
	$.ajax({
	    type: "POST",
	    url: uri,
	    data: {"args___json":$.toJSON(data)},
	    success: callback,
	    error: errback,
		dataType: dataType || "html"
    });
}


$.jsonRPC = function(method,data,callback,errback) {
	if (errback==null) {
		errback=function(error){notify("Error: "+error.responseText)};
	}

	$.ajax({
	    type: "POST",
	    url: EMEN2WEBROOT+"/json/"+method,
	    data: $.toJSON(data),
	    success: callback,
	    error: errback,
		dataType: "json"
    });
}
