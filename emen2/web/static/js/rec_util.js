function displaypermissions() {



	

	return



}


function newrecord_getoptionsandcommit(values) {

	values[NaN]["permissions"]=permissionscontrol.getpermissions();
	var parents=permissionscontrol.getparents();
	console.log(parents);
	console.log(values);

	// commit
	commit_newrecord(
		values,
		parents,
		function(recid){
			window.location='/db/record/'+recid
		}
	);
	
}


function commit_putrecords(records,cb) {
	if (cb==null) {cb=function(){}}

	$.jsonRPC("putrecordsvalues",[records,ctxid],
 		function(json){
//			setrecords(json);
 			cb(json);
//			notify("Changes saved");
//			self.revert();
 		},
		function(xhr){
			$("#alert").append("<li>Error: "+xhr.responseText+"</li>");
		}
	);	
}
	
	
function commit_newrecord(values,parents,cb) {
	if (cb==null) {cb=function(){}}
	var rec_update=getrecord(null);

	$.each(values[NaN], function(i,value) {
		if ((value!=null) || (getvalue(recid,i)!=null)) {
			rec_update[i]=value;
		}
	});
	
	$.jsonRPC("putrecord", [rec_update,ctxid, parents],
		function(json){
			cb(json);
		},
		function(xhr){
			$("#alert").append("<li>Error: "+this.param+", "+xhr.responseText+"</li>");				
		}
	);
}



function record_updatecomments() {
	elem=$("#page_comments_commentstext");
}



function record_pageedit(elem, key) {
	new multiwidget(
		elem, {
			'commitcallback':function(values){commit_putrecords(values,function(){window.location.reload()})},
			'now':1,
			'ext_edit_button':1,
			'root': '#page_recordview_'+key
		}
	);
}



// remove
function record_reloadview(view) {
	if (!view) {view="defaultview"}
	$("#page_recordview_"+view).remove(".controls");
	$("#page_recordview_"+view+" .view").load("/db/recordview/"+recid+"/"+view,{},	function(data){editelem_makeeditable();});
}


function record_form_newrecord(elem) {
	val=elem.form.addchild.value;
	window.location='/db/newrecord/'+recid+'/'+val+'/';
}
