////////////////  base ///////////////////


function default_errback(e, cb) {
	var error = $('<div class="error" title="'+e.statusText+'" />');
	//<span class="ui-icon ui-icon-alert" style="float:left; margin:0 7px 20px 0;"></span>
	error.append('<p>'+e.responseText+'</p>');
		
	var debug = $('<div class="debug shadow_top hide"/>');
	debug.append('<p><strong>JSON-RPC Method:</strong></p><p>'+this.jsonRPCMethod+'</p>');
	debug.append('<p><strong>Data:</strong></p><p>'+this.data+'</p>');
	error.append(debug);

	error.dialog({
		width:400,
		height:300,
		modal:true,
		buttons: {
			'OK':function() {
				$(this).dialog('close')
			},
			'More Info': function() {
				$('.debug', this).toggle();
				//$(this).dialog('option', 'width', 600); //.width(600);
			}
		}
	});
	
	if (cb) {
		cb();
	}
	
}

$.postJSON = function(url, data, callback ) {
	return 1;
	//return jQuery.post(url, data, callback, "json")
}


$.jsonRPC = function(method,data,callback,errback) {
	if (errback==null) {
		errback = default_errback;
	}

	$.ajax({
		jsonRPCMethod:method,
	    type: "POST",
	    url: EMEN2WEBROOT+"/json/"+method,
	    data: $.toJSON(data),
	    success: callback,
	    error: errback,
		dataType: "json"
    });
}
