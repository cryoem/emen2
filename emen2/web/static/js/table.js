function table_editcolumn(elem,key) {

	new multiwidget(
			elem, {
				'commitcallback':function(values){commit_putrecords(values,table_reload())},
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
	
	$.postJSON(
		'/db/table/'+tablestate["mode"]+'/'+tablestate["args"].join('/')+'/',
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

	ns["recids"]=tablestate["recids"].slice(pos,pos+tablestate["count"]);

	ns["sortkey"]=tablestate["sortkey"];
	ns["reverse"]=tablestate["reverse"];
	ns["reccount"]=tablestate["reccount"];
	ns["pos"]=pos;
	ns["reset"]=0;

	$.postJSON(
		'/db/table/'+tablestate["mode"]+'/'+tablestate["args"].join('/')+'/',
		ns,
		function(data) {
			$(tablestate['id_inner']).html(data);
		}
		);
}

function table_sort(key) {
	var ns={};
	ns["sortkey"]=key;

	// these events reset position to zero
	if (tablestate["sortkey"] == key) {
		ns["reverse"] = tablestate["reverse"] ? 0 : 1
	} 

	$.postJSON(
		'/db/table/'+tablestate["mode"]+'/'+tablestate["args"].join('/')+'/',
		ns,
		function(data) {
			$(tablestate['id']).html(data);
			}
		);
	
}