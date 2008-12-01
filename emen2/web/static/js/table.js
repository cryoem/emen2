// rewrite properly and get rid of this global..
var tmp_table_keys_menu_init=0;
var tmp_table_tablekeys=[];

function table_keys_menu_toggle(elem) {
	var menu=$(elem).siblings(".table_keys_menu");
	menu.toggle();
	
	if (tmp_table_keys_menu_init==1) {
		return
		}
	
	menu.empty();
	//tmp_table_tablekeys=tablestate["tablekeys"].slice();
	var f=$("<form/>");
	var ul=$("<ul />");

	for (var i=0;i<tablestate["paramsK"].length;i++) {
			var li=$('<li />');
			var inp=$('<input type="checkbox" name="'+tablestate["paramsK"][i]+'" />');
			if (tablestate["tablekeys"].indexOf(tablestate["paramsK"][i]) > -1) {inp.attr("checked","checked")}
			li.append(inp,$("<span>"+tablestate["paramsK"][i]+"</span>"));
			ul.append(li);
	}
	
	// get macros
	//for (var i=0;i<tablestate["tablekeys"].length;i++) {
	//	var li=$('<li />');
	//	var inp=$('<input type="checkbox" name="'+tablestate["tablekeys"][i]+'" />');
	//	if (tmp_table_tablekeys.indexOf(tablestate["tablekeys"][i]) > -1) {inp.attr("checked","checked")}
	//	li.append(inp,$("<span>"+tablestate["tablekeys"][i]+"</span>"));
	//	ul.append(li);
	//}	
	
	f.append(ul);
	
	f.append (
		$('<span class="jslink">Check All</span>').click(function(){
			$(this).parent().find("input:checkbox").each(function(){
				$(this).attr("checked","checked");
			})
		})
	);
	f.append("<span> | </span>");
	f.append (
		$('<span class="jslink">Uncheck All</span>').click(function(){
			$(this).parent().find("input:checkbox").each(function(){
				$(this).attr("checked","");
			})
		})
	);	
	
	f.append( $('<input type="button" value="Apply" />').click(function(){table_keys_menu_apply(this)}) );
	menu.append(f);
	tmp_table_keys_menu_init=1;
}

function table_keys_menu_apply(elem) {
	var form=$(elem.form);
	tablestate["tablekeys"]=[];

	$("input:checkbox",form).each( function() {
			if ($(this).attr("checked")){
				tablestate["tablekeys"].push($(this).attr("name"));
			}
		});

	//if (tablestate["macros"][key]!=null) {
	//	console.log("macro");
	//}
	
	table_generate_viewdef(tablestate["tablekeys"]);	
}

function table_generate_viewdef(tk) {
	var viewdef="";
	for (var i=0;i<tk.length;i++) {
		if (tablestate["macros"][tk[i]]!=null) {
			//console.log("macro");
			//console.log(tk[i]);
			viewdef+=" $@"+tk[i]+"()";
		} else {
			viewdef+=" $$"+tk[i];
		}
	}

	tablestate["viewdef"]=viewdef;
	tmp_table_keys_menu_init=0;
	table_refresh(0);
}

function table_editcolumn(elem,key) {

	new multiwidget(
			elem, {
				'commitcallback':function(self,values){commit_putrecords(self,values,table_reinit())},
				'now':1,
				'ext_edit_button':1,
				'rootless':1,
				'restrictparams':[key]
				});	

}	



function table_setcount(count) {
	
	if (count < 0) {return}
	if (count == 0) {
		tablestate["count"]=tablestate["recids"].length;
	} else {
		tablestate["count"]=count;
	}
	table_refresh(0);
	
}

function table_reinit() {
	table_refresh(1);
}

function table_refresh(reset) {
	var ns={};
	ns["sortkey"]=tablestate["sortkey"];
	ns["reverse"]=tablestate["reverse"];
	ns["pos"]=tablestate["pos"];
	ns["reset"]=reset;
	
	ns["viewdef"]=tablestate["viewdef"];
	ns["recids"]=tablestate["recids"].slice(tablestate["pos"],tablestate["pos"]+tablestate["count"]);
	ns["reccount"]=tablestate["reccount"];
	ns["count"]=tablestate["count"];
	
	if (tablestate["rectype"]!=null) {ns["rectype"]=tablestate["rectype"]}
	
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

function table_setpos(pos) {
	var ns={};

	ns["recids"]=tablestate["recids"].slice(pos,pos+tablestate["count"]);
	ns["sortkey"]=tablestate["sortkey"];
	ns["reverse"]=tablestate["reverse"];
	ns["reccount"]=tablestate["reccount"];
	tablestate["pos"]=pos;
	ns["pos"]=pos;
	ns["count"]=tablestate["count"];
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
	ns["count"] = tablestate["count"];

	// these events reset position to zero
	if (tablestate["sortkey"] == key) {
		ns["reverse"] = tablestate["reverse"] ? 0 : 1
	} 

	if (tablestate["mode"] == "list") {
		ns["recids"] = tablestate["recids"];
		ns["reccount"] = tablestate["reccount"];
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