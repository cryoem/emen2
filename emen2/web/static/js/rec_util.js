// globals

valid_properties = {"angle":["degree",["mrad","radian","degree"]],"area":["m^2",["cm^2","m^2"]],"bfactor":["A^2",["A^2"]],"concentration":["mg/ml",["p/ml","mg/ml","pfu"]],"count":["count",["count","K","pixels"]],"currency":["dollars",["dollars"]],"current":["amp",["amp"]],"currentdensity":["Pi Amp/cm2",["Pi Amp/cm2"]],"dose":["e/A2/sec",["e/A2/sec"]],"energy":["J",["J"]],"exposure":["e/A2",["e/A2"]],"filesize":["bytes",["kB","MB","MiB","bytes","GB","KiB","GiB"]],"force":["N",["N"]],"inductance":["henry",["H"]],"length":["m",["A","nm","cm","mm","m","km","um"]],"mass":["gram",["mg","MDa","KDa","g","Da"]],"momentum":["kg m/s",["kg m/s"]],"pH":["pH",["pH"]],"percentage":["%",["%"]],"pressure":["Pa",["torr","psi","Pa","bar","atm"]],"relative_humidity":["%RH",["%RH"]],"resistance":["ohm",["ohm"]],"resolution":["A/pix",["A/pix"]],"temperature":["K",["K","C","F"]],"time":["s",["hour","min","us","s","ms","ns","day"]],"transmittance":["%T",["%T"]],"unitless":["unitless",["unitless"]],"velocity":["m/s",["m/s"]],"voltage":["volt",["mv","kv","V"]],"volume":["m^3",["ml","m^3","l","ul"]]}


paramindex={};
paramdefs={};

recid=null;
rec={};
recs={};
parents=[];
children=[];

recnames={};
displaynames={};
groupnames={};
groupnames["-4"]="Anonymous Access";
groupnames["-3"]="Authenticated Users";
groupnames["-1"]="Administrators";

ajaxqueue={};


function getctxid() {
	name="ctxid";
	var nameEQ = name + "=";
	var ca = document.cookie.split(';');
	for(var i=0;i < ca.length;i++) {
		var c = ca[i];
		while (c.charAt(0)==' ') c = c.substring(1,c.length);
		if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
	}
	return null;
}

ctxid = getctxid();


// js is stupid at sorting.
function sortNumber(a, b) {
	return a - b;
}



/// switch.js


function switchbutton(type,id) {
	$(".button_"+type).each(function() {
		var elem=$(this);
		if (this.id != "button_"+type+"_"+id) {
			elem.removeClass("button_active");
			elem.removeClass("button_"+type+"_active");
		} else {
			elem.addClass("button_active");
			elem.addClass("button_"+type+"_active");
		}
	});
}


switchedin=new Array();
switchedin["recordview"]="defaultview";
// hide class members, show one, switch the button
function switchin(classname, id) {
	switchedin[classname]=id;
	switchbutton(classname,id);
	$(".page_"+classname).css("display","none");
	document.getElementById("page_" + classname + "_" + id).style.display = 'block';	
}



//////////////////////////////////////////

// access values from correct sources



function getdisplayname(name) {
	if (displaynames[name]!=null) return displaynames[name];
	if (groupnames[name]!=null) return "Group: "+groupnames[name]; 
}

function setdisplayname(name,value) {
	if (isNaN(parseInt(name))) {
		displaynames[name]=value;
	} else {
		groupnames[name]=value;
	}
}

function getvalue(recid,param) {
	//if (rec["recid"]==recid || recid==null) {return rec[param]}
	if (paramindex[param]) {
		if (paramindex[param][recid]) {return paramindex[param][recid]}
		}
	if (recs[recid]) {
		return recs[recid][param]
	}
	return null
}
function setvalue(recid,param,value) {
	if (rec["recid"]==recid || recid==null) {rec[param]=value}
	if (paramindex[param]) {
		if (paramindex[param][recid]) {
			paramindex[param][recid]=value
			}
	}
	if (recs[recid]) {
		if (recs[recid][param]) {
			recs[recid][param]=value
			}
	}
}
function setrecord(recid,record) {
	recs[recid]=record;
}
function setrecords(records) {
	$.each(records,function(i){
		recs[i]=this;
	});
}
function getrecord(recid) {
	if (recid==null) { return rec }
	if (recs[recid]) {
		return recs[recid];
	}
}



//////////////////////////////////////////


function notify(msg,nofade) {
	//$("#alert").empty();
	var msg=$('<li>'+msg+'</li>');
	msg.click(function(){$(this).fadeOut()});
	$("#alert").append(msg).fadeIn();
	if (!nofade) {
		setTimeout(function(){msg.fadeOut()},3000)
	}
}


function notify_post(uri,msgs) {
  var postform = document.createElement("form");
  postform.method="post" ;
  postform.action = uri;
	for (var i=0;i<msgs.length;i++) {
		var note = document.createElement("input") ;
		note.setAttribute("name", "notify_"+i) ;
		note.setAttribute("value", msgs[i]);
		postform.appendChild(note) ;
	}
	document.body.appendChild(postform);
  postform.submit();	
}

//////////////////////////////////////////


function record_action_delete(drecid) {
	var test=confirm("Are you sure you want to delete this record?");
	if (test) {
		$.jsonRPC("deleterecord",[drecid,ctxid], function() {
			//$.post("/db/record/"+recid,{"notify_0":"This record has been marked for deletion and removed from hierarchy"});
			//notify_post(window.location,["This record has been marked for deletion and removed from the hierarchy"]);
			window.location.reload();
		}, function() {
			notify("Error deleting record!");
		});
	}
}

function record_upload_show() {
		$("#page_comments_upload").empty();
		$("#page_comments_upload").append(
		'<embed width="600px" height="600px" name="plugin" src="http://localhost:8080/flash/multipleUpload.swf" type="application/x-shockwave-flash" flashvars="uploaduri=http%3A%2F%2Flocalhost%3A8080%2Fupload%2F136" />');
		switchin('comments','upload');
}


function record_relationships_show() {
	if (relationships==null) {
		
		$("#page_comments_relationships").empty();
		
		$.jsonRPC("getrecordrecname",[parents.concat(children).concat([recid]), ctxid], function(result) {
			$.each(result, function(k,v) {
					recnames[k]=v;
			});
			relationships = new relationshipcontrol($("#page_comments_relationships"), {
				'parents':parents,
				'children':children,
				'recid':recid
			});
			
			switchin('comments','relationships');

		});

	} else {

		switchin('comments','relationships');
		
	}
}


function record_permissions_show() {
	// setup permissions controls
	//console.log(permissionscontrol);
	if (permissionscontrol==null) {
	
		$("#page_comments_permissions").empty();
	
		$.jsonRPC("getuserdisplayname",[recid,ctxid], function(result) {
			$.each(result, function(k,v) {
				setdisplayname(k,v);
			});
			permissionscontrol = new permissions($("#page_comments_permissions"), {
				'list':getvalue(recid,"permissions"),
				}
			);
			
			switchin('comments','permissions');		
		
		});
	
	} else {
		switchin('comments','permissions');		
	}
	
}

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
	//console.log(parents);
	//console.log(values);

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
	//console.log(records);
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
	t=document.getElementById("record_editbar_addchild_select");
	val=t.value;
	window.location='/db/newrecord/'+recid+'/'+val+'/';
}