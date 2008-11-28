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
	console.log(document.cookie);
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
	//console.log("Switching in "+classname+" "+id);
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

function getrecname(name) {
	return recnames[name]
}
function setrecname(name,value) {
	recnames[name]=value;
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


function notify(msg,fade) {
	//$("#alert").empty();
	var msg=$('<li>'+msg+'</li>');
	msg.click(function(){$(this).fadeOut()});
	$("#alert").append(msg).fadeIn();
	if (!fade) {
		setTimeout(function(){msg.fadeOut()},3000)
	}
	if (fade > 0) {
		setTimeout(function(){msg.fadeOut()},fade*1000)
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



/////////////////////////////////////////


function record_action_delete(drecid) {
	var test=confirm("Are you sure you want to delete this record?");
	if (test) {
		$.jsonRPC("deleterecord",[drecid,ctxid], function() {
			//$.post("/db/record/"+recid,{"notify_0":"This record has been marked for deletion and removed from hierarchy"});
			notify_post(window.location,["This record has been marked for deletion and removed from the hierarchy"]);
			//window.location.reload();
		}, function() {
			notify("Error deleting record!");
		});
	}
}




function toggle_record_menu(elem) {
	
	var elem=$(elem);
	var state=elem.data("active");
	if (state == null || state == 0) {state=1} else {state=0}

	// reset state
	$(".record_editbar_hidden").hide();
	$(".record_editbar_item").removeClass("record_editbar_no_border_bottom");	
	$(".record_editbar_item").addClass("record_editbar_border_bottom");	
	$(".record_editbar_item").children("span").data("active",0);
	elem.data("active",state);
	
	//elem.data("active",elem.data("active") ? 0 : 1);

	if (state) {
		//console.log("show");
		elem.parent().addClass("record_editbar_no_border_bottom");	
		elem.parent().removeClass("record_editbar_border_bottom");	
		elem.siblings(".record_editbar_hidden").show();
	}

}

function record_permissions_toggle(elem) {
	toggle_record_menu(elem);
	//var target=$("#record_editbar_menu_permissions");	
	var target=$(elem).siblings(".record_editbar_hidden");				

	if (permissionscontrol==null) {
	
		target.empty();
	
		$.jsonRPC("getuserdisplayname",[recid,ctxid], function(result) {
			$.each(result, function(k,v) {
				setdisplayname(k,v);
			});
			permissionscontrol = new permissions(target, {
				'list':getvalue(recid,"permissions")
				}
			)
					
		});
	}

	return false

}

function record_form_newrecord_toggle(elem) {
	toggle_record_menu(elem);
}


function record_upload_toggle(elem) {
	toggle_record_menu(elem);
}


function record_relationships_toggle(elem) {
	toggle_record_menu(elem);
	var target=$(elem).siblings(".record_editbar_hidden");
	
	if (relationships==null) {
		
		target.empty();
		
		$.jsonRPC("getrecordrecname",[parents.concat(children).concat([recid]), ctxid], function(result) {
			$.each(result, function(k,v) {
					setrecname(k,v);
					//recnames[v[0]]=v[1];
			});
			relationships = new relationshipcontrol(target, {
				'parents':parents,
				'children':children,
				'recid':recid
			});
			
		});

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
	$('#page_recordview_'+viewtype).load("/db/recordview/"+recid+"/"+viewtype+"/",null,function() {
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
			//window.location='/db/record/'+recid
			notify_post('/db/record/'+recid,["Record Saved"]);
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
			//$("#alert").append("<li>Error: "+xhr.responseText+"</li>");
			notify("Error: "+xhr.responseText);
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
	
	$.jsonRPC("putrecord", [rec_update, ctxid, parents],
		function(json){
			cb(json);
		},
		function(xhr){
			//$("#alert").append("<li>Error: "+this.param+", "+xhr.responseText+"</li>");
			notify("Error: "+this.param+", "+xhr.responseText);
			self.savebutton.val("Retry Commit");		
		}
	);
}



function record_updatecomments() {
	elem=$("#page_comments_commentstext");
}



function record_pageedit(elem, key) {
	//console.log("editing "+key);
	new multiwidget(
		elem, {
			'commitcallback':function(self, values){commit_putrecords(self, values,function(){
				notify_post(window.location.pathname, ["Changes Saved"]);
				//window.location.reload()
				})},
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
	$("#page_recordview_"+view).load("/db/recordview/"+recid+"/"+view,{},	function(data){editelem_makeeditable();});
}










