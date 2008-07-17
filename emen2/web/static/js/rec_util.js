function displaypermissions() {



	

	return



}


function newrecord_getoptionsandcommit(values) {

	values[NaN]["permissions"]=permissionscontrol.list;
	console.log(values);
	
	// commit
	commit_newrecord(
		values,
		function(recid){
			window.location='/db/record/'+recid
		}
	);
	
}



function record_updatecomments() {
	elem=$("#page_comments_commentstext");
}



function record_pageedit(elem, key) {
	new multiwidget(
		elem, {
			'commitcallback':function(values){commit_putrecords(value,alert("ok"))},
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



