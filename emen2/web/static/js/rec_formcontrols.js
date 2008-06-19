// js is stupid at sorting.
function sortNumber(a, b) {
	return a - b;
}

var edit=0;

$(document).ready(function() {
		$('.editable').click(function(e) {editelem(this)});
});


function editelem(elem) {
	
	//console.log("editing..");
	$(elem).toggleClass("editable");

	var classes = elem.className.split(" ");
	var prop = new Object();
	
	for (var i in classes) {
		var j = classes[i].split("___");
		if (j.length > 1) {
			prop[j[0]] = j[1];
		}
	}
		
	var key=prop["paramdef"];
	var pd=paramdefs[key];

	var editelem="";
	var vt=pd["vartype"];
	var edit = "";
		
	if (vt=="text") {

		edit="<textarea class=\"value\" cols=\"40\" rows=\"10\">"+$(elem).html()+"</textarea>";

	} else if (vt=="choice") {

		edit="<select>"

		for (var i=0;i<pd["choices"].length;i++) {
			edit = edit + "<option>"+pd["choices"][i]+"</option>";
		}
		
	} else if (vt=="datetime") {
		
		edit=$('<input class="value" size="18" type="text" value="'+rec[key]+'" />').date_input();

	} else if (vt=="boolean") {
		
		edit=$("<select><option>True</option><option>False</option></select>");
		
	} else {

		edit=$('<input class="value" size=\"20\" type="text" value="'+rec[key]+'" />').autocomplete("/db/findvalue/"+key, {
			width: 260,
			selectFirst: true,
		});

	}


	var save=$('<input type="button" value="Save" />').click(function(e){e.stopPropagation();editelem_save(this,key);});
	var cancel=$('<input type="button" value="Cancel" />').click(function(e){e.stopPropagation();editelem_revert(this,key);});
	var widget = $('<span class="widget"></span>').append(edit,save,cancel);


	$(elem).after(widget);
	$(elem).hide();

	//if (vt!="datetime") {
		edit.focus();
		edit.select();
	//}
	
}

function editelem_save(elem,key) {

	var value = $(elem).siblings(".value").val();
	//var args=$.toJSON([recid,key,value,ctxid]);
	//console.log(args);

	//$(elem).ajaxStart(function(){$(this).val("Saving...")});
	//$(elem).ajaxStop(function(){editelem_revert(elem,key)});
	$(elem).val("Saving...");
	$.jsonRPC("putrecordvalue",[recid,key,value,ctxid],
 		function(json){
 			rec[key]=json;
 			reload_record_view(switchedin["recordview"]);
			notify("Changes saved");
 		},
		function(xhr){
			console.log("error, "+xhr.responseText);
			//editelem_revert(elem,key);
			$("#alert").append("<li>Error: "+key+","+xhr.responseText+"</li>");
		}
	);
	
}

function notify(msg) {
	$("#alert").empty();
	$("#alert").append("<li>"+msg+"</li>");
}

function updatecomments() {
	elem=$("#page_comments_commentstext");
}

function jsonrpccallback(json){}
function jsonrpcerror(xhr){
	console.log("error, "+xhr.responseText);
	$("#alert").append("<li>Error: "+key+","+xhr.responseText+"</li>");
	}


function editelem_revert(elem,key,value) {
	
	if (!value) {
		value = rec[key];
	}

	var parent=$(elem).parent();

	parent.prev().html(value);
	parent.prev().show();
	$(elem).parent().empty();

}

function reload_record_view(view) {
	if (!view) {view="defaultview"}
	$("#page_recordview_"+view).load("/db/recordview/"+recid+"/"+view,{},	function(){editelem_makeeditable()});
}

function editelem_makeeditable() {
	$('.editable').click(function(e) {editelem(this)});
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


function bind(fn) {
    var self = this;
    return function() { return fn.apply(self, arguments) };
}