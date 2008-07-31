valid_properties = {"angle":["degree",["mrad","radian","degree"]],"area":["m^2",["cm^2","m^2"]],"bfactor":["A^2",["A^2"]],"concentration":["mg/ml",["p/ml","mg/ml","pfu"]],"count":["count",["count","K","pixels"]],"currency":["dollars",["dollars"]],"current":["amp",["amp"]],"currentdensity":["Pi Amp/cm2",["Pi Amp/cm2"]],"dose":["e/A2/sec",["e/A2/sec"]],"energy":["J",["J"]],"exposure":["e/A2",["e/A2"]],"filesize":["bytes",["kB","MB","MiB","bytes","GB","KiB","GiB"]],"force":["N",["N"]],"inductance":["henry",["H"]],"length":["m",["A","nm","cm","mm","m","km","um"]],"mass":["gram",["mg","MDa","KDa","g","Da"]],"momentum":["kg m/s",["kg m/s"]],"pH":["pH",["pH"]],"percentage":["%",["%"]],"pressure":["Pa",["torr","psi","Pa","bar","atm"]],"relative_humidity":["%RH",["%RH"]],"resistance":["ohm",["ohm"]],"resolution":["A/pix",["A/pix"]],"temperature":["K",["K","C","F"]],"time":["s",["hour","min","us","s","ms","ns","day"]],"transmittance":["%T",["%T"]],"unitless":["unitless",["unitless"]],"velocity":["m/s",["m/s"]],"voltage":["volt",["mv","kv","V"]],"volume":["m^3",["ml","m^3","l","ul"]]}



function record_view_makeeditable(recid,viewtype) {
	$('#page_recordview_'+viewtype+' .editable').bind("click",function(){
		var self=this;
		getparamdefs([recid],function(){
			new widget(self);
		});
	});
}


function record_view_reload(recid,viewtype) {
	$('#page_recordview_'+viewtype+' .view').load("/db/recordview/"+recid+"/"+viewtype+"/",null,function() {
		record_view_makeeditable(recid,viewtype);
	});
}


function newrecord_getoptionsandcommit(self, values) {
	values[NaN]["permissions"]=permissionscontrol.getpermissions();
	var parents=permissionscontrol.getparents();
	console.log(parents);
	console.log(values);

	// commit
	commit_newrecord(
		self,
		values,
		parents,
		function(recid){
			window.location='/db/record/'+recid
		}
	);
	
}


function commit_putrecords(self, records, cb) {
	if (cb==null) {cb=function(json){}}

	$.jsonRPC("putrecordsvalues",[records,ctxid],
 		function(json){
 			cb(json);
//			notify("Changes saved");
 		},
		function(xhr){
			$("#alert").append("<li>Error: "+xhr.responseText+"</li>");
			self.savebutton.val("Retry Save");
		}
	);	
}
	
	
function commit_newrecord(self, values,parents,cb,self) {
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
			self.savebutton.val("Retry Commit");		
		}
	);
}



function record_updatecomments() {
	elem=$("#page_comments_commentstext");
}



function record_pageedit(elem, key) {
	new multiwidget(
		elem, {
			'commitcallback':function(self, values){commit_putrecords(self, values,function(){window.location.reload()})},
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
