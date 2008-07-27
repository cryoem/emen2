paramdefs={};
recs={};
rec={};
recid=null;
displaynames={};


/////////// autocomplete callbacks ////////////

function autocomplete_parse_finduser(data) {
	console.log("using autocomplete parse finduser");
	var parsed = [];
	console.log(data);
	for (var i=0; i<data.length; i++) {
		var a={
			"data": [data[i][1],data[i][0]],
			"value": data[i][0],
			"result": data[i][0]
		};
		parsed.push(a);
		// we'll also add to user display name cache
		displaynames[data[i][0]]=data[i][1];
	}
	return parsed;
};


function autocomplete_parse_findvalue(data) {
	var parsed = [];
	console.log(data);
	for (var i=0; i<data.length; i++) {
		var a={
			"data": [data[i][1],data[i][0]],
			"value": data[i][0],
			"result": data[i][0]
		};
		parsed.push(a);
	}
	return parsed;
};


///////// editing callbacks ///////////////////






///////// get data /////////////////////

function getrecords_paramdefs(recids,finalcallback) {
	// get data.
	
	$.jsonRPC(
		"getrecord",
		[recids,ctxid],
 		function(json){
			//console.log("got records");
			$.each(json, function() {
				setrecord(this["recid"],this);
			});			

			//
			$.jsonRPC(
				"getparamdefs",
				[recids,ctxid],
				function (json) {
					//console.log("got paramdefs");
					$.each(json, function(i) {
						//console.log(i,this);
						paramdefs[i]=this;
					});
					// calling final callback
					finalcallback();
				}
			);
			//

 		}
	);
}





////////////////  base ///////////////////




$.postJSON = function(uri,data,callback,errback) {
	if (!errback) {
		errback = function(xhr){
				$("#alert").append("<li>Error: "+xhr.responseText+"</li>");
			}
		}
	$.ajax({
    type: "POST",
    url: uri,
    data: {"args_json":$.toJSON(data)},
    success: callback,
    error: errback,
		dataType: "html"
    });
}

$.jsonRPC = function(method,data,callback,errback) {
	$.ajax({
    type: "POST",
    url: "/json/"+method,
    data: $.toJSON(data),
    success: callback,
    error: errback,
		dataType: "json"
    });
}