///////// get data /////////////////////

function json_getparamdefs(recids,cb) {
	$.jsonRPC(
		"getparamdefs",
		[recids],
		function (json) {
			$.each(json, function(i) {
				paramdefs[i]=this;
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
				recs[this.recid]=this;
			});
			cb();
		}
	);	
}



function json_getrecords_paramdefs(recids,cb) {
	// get data
	$.jsonRPC(
		"getrecord",
		[recids],
 		function(json){
			//console.log("got records");
			$.each(json, function() {
				setrecord(this["recid"],this);
			});			

			//
			$.jsonRPC(
				"getparamdefs",
				[recids],
				function (json) {
					//console.log("got paramdefs");
					$.each(json, function(i) {
						//console.log(i,this);
						paramdefs[i]=this;
					});
					// calling final callback
					cb();
				}
			);
			//

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
