// rewrite properly and get rid of this global..
var tmp_table_keys_menu_init=0;
var tmp_table_tablekeys=[];

function table_keys_menu_toggle(elem) {
	var menu=$(elem).siblings(".table_keys_menu");
	menu.toggle();
	
	if (tmp_table_keys_menu_init==1) {return}
	
	menu.empty();
	tmp_table_tablekeys=tablestate["tablekeys"].slice();
	var f=$("<form/>");
	var ul=$("<ul />");
	for (var i=0;i<tablestate["tablekeys"].length;i++) {
		//<li><input type="checkbox" name="${i}" id="${i}" checked="checked" /><label for="${i}">${i}</label></li>
		var li=$('<li />');
		var inp=$('<input type="checkbox" name="'+tablestate["tablekeys"][i]+'" />');
		if (tmp_table_tablekeys.indexOf(tablestate["tablekeys"][i]) > -1) {inp.attr("checked","checked")}
		li.append(inp,$("<span>"+tablestate["tablekeys"][i]+"</span>"));
		ul.append(li);
	}
	f.append(ul);
	f.append( $('<input type="button" value="Apply" />').click(function(){table_keys_menu_apply(this)}) );
	menu.append(f);
	tmp_table_keys_menu_init=1;
}

function table_keys_menu_apply(elem) {
	var form=$(elem.form);

	tmp_table_tablekeys=[];
	$("input:checkbox",form).each( function() {
			if ($(this).attr("checked")){
				tmp_table_tablekeys.push($(this).attr("name"));
			}
		});
	console.log(tmp_table_tablekeys);
	//if (tablestate["macros"][key]!=null) {
	//	console.log("macro");
	//}
	
	table_generate_viewdef(tmp_table_tablekeys);
	
}

function table_generate_viewdef(tk) {
	var viewdef="";
	for (var i=0;i<tk.length;i++) {
		if (tablestate["macros"][tk[i]]!=null) {
			console.log("macro");
			console.log(tk[i]);
			viewdef+=" $@"+tk[i]+"()";
		} else {
			viewdef+=" $$"+tk[i];
		}
	}
	console.log(viewdef);
	tablestate["viewdef"]=viewdef;
	table_reload();
}

function table_editcolumn(elem,key) {

	new multiwidget(
			elem, {
				'commitcallback':function(self,values){commit_putrecords(self,values,table_reload)},
				'now':1,
				'ext_edit_button':1,
				'rootless':1,
				'restrictparams':[key]
				});	

}	



function table_reload() {
	var ns={};
	ns["sortkey"]=tablestate["sortkey"];
	ns["reverse"]=tablestate["reverse"];
	ns["pos"]=tablestate["pos"];
	ns["reset"]=1;
	ns["viewdef"]=tablestate["viewdef"];
	ns["recids"]=tablestate["recids"];
	
	var uri='/db/table/'+tablestate["mode"]+'/'
	if (tablestate["args"]){uri+=tablestate["args"].join('/')+'/'}
	
	$.postJSON(
		uri,
		ns,
		function(data) {
			$(tablestate['id']).html(data);
			}
		);
}

function table_setpos(pos) {
	var ns={};
	//def table_children(recid,group,recids=None,pos=0,count=100,reccount=None,sortkey=None,reverse=0,ctxid=None,db=None,rctx=0,reset=1,host=None):
	//ns["pos"]=pos;
	//ns["count"]=tablestate["count"];

	//console.log(tablestate["id_inner"]);

	ns["recids"]=tablestate["recids"].slice(pos,pos+tablestate["count"]);

	ns["sortkey"]=tablestate["sortkey"];
	ns["reverse"]=tablestate["reverse"];
	ns["reccount"]=tablestate["reccount"];
	ns["pos"]=pos;
	ns["reset"]=0;
	ns["viewdef"]=tablestate["viewdef"];

	var uri='/db/table/'+tablestate["mode"]+'/'
	if (tablestate["args"]){uri+=tablestate["args"].join('/')+'/'}

	$.postJSON(
		uri,
		ns,
		function(data) {
			$(tablestate['id_inner']).html(data);
		}
		);
}

function table_sort(key) {
	var ns={};
	ns["sortkey"]=key;
	ns["viewdef"]=tablestate["viewdef"];

	//console.log("TABLE SORT");

	// these events reset position to zero
	if (tablestate["sortkey"] == key) {
		ns["reverse"] = tablestate["reverse"] ? 0 : 1
	} 
	if (tablestate["mode"] == "list") {
		ns["recids"] = tablestate["recids"];
	}
	

	var uri='/db/table/'+tablestate["mode"]+'/'
	if (tablestate["args"]){uri+=tablestate["args"].join('/')+'/'}

	$.postJSON(
		uri,
		ns,
		function(data) {
			$(tablestate['id']).html(data);
			}
		);
	
}