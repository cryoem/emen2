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





/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////


TableControl = (function($) { // Localise the $ function

function TableControl(elem, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, TableControl.DEFAULT_OPTS, opts);
	this.ed = elem;
  this.elem = $(elem);  
  this.init();
};

TableControl.DEFAULT_OPTS = {
};

TableControl.prototype = {
	
	init: function() {
		this.ts = ts;
		this.ts.showtablestate = 0;
		this.bindelems();
	},
	
	bindelems: function() {	
		var self=this;
		
		// controls
		$(".table_sortkey",this.elem).click(function(e){self.event_sortkey(e)});
		$(".table_setpos",this.elem).click(function(e){self.event_setpos(e)});
		$(".table_setcount",this.elem).change(function(e){self.event_setcount(e)});
		$(".table_query_submit",this.elem).click(function(e){self.event_query(e)});
		$(".table_query_clear",this.elem).click(function(e){self.event_clear(e)});
		$(".table_properties",this.elem).click(function(e){self.event_toggleprop(e)});
		//$(".table_editcol",this.elem).click(function(e){self.editcol(e)});
	},
	
	replace: function(data) {
		//this is quicker
		this.ed.innerHTML=data;
		this.bindelems();
	},
	
	reverse: function() {
		if (this.ts.reverse) {this.ts.reverse = 0} else {this.ts.reverse = 1}
	},
	
	refresh: function() {
		var self=this;
		this.ts.showtablestate=0;
		$.postJSON("/db/table/list/",this.ts,function(data){self.replace(data)});
	},	
	
	event_toggleprop: function(e) {
		var self=this;
		$.jsonRPC("getrecorddef",[this.ts.rectype],function(recdef) {
			self.allparams = recdef.paramsK;
			$.jsonRPC("getparamdefs",[recdef.paramsK],function(paramdefs) {
				self.paramdefs=paramdefs
				self.build_toggleprop();
			})
		});
	},
	
	build_toggleprop: function() {

		var self=this;
		var p=$(".table_keys_menu",this.elem);
		p.empty();
		
		this.viewdeftable=$('<table cellspacing="0" cellpadding="0" />');

		var nonmacro=[];
		$.each(this.ts.tablekeys, function(i,j,k){
			if (!self.ts.macros[j]){nonmacro.push(j)}
		});
		
		$.each(this.ts.tablekeys, function(i,j,k) {
			if (!self.ts.macros[j]) {
				var row=$('<tr data-param="'+j+'" data-macro="0" />');
				var x=$("<span>x</span>").click(function(e){self.event_removetablekey(e)});
				var up=$("<span>+</span>").click(function(){console.log("up"+this)});
				var down=$("<span>-</span>").click(function(){console.log("down"+this)});
				var b=$("<td/>");
				b.append(x,up,down);
				row.append(b);
				row.append('<td>'+j+'</td>');
				row.append('<td>'+self.paramdefs[j].desc_short+'</td>');
				self.viewdeftable.append(row);
			} else {
				self.viewdeftable.append(
					'<tr data-param="'+j+'" data-macro="1"><td>x + -</td><td><input name="name" type="text" value="'+self.ts.macros[j][0]+'" /></td><td><input name="args" type="text" value="'+self.ts.macros[j][1]+'" /></td></tr>'
					);
			}
		});
		
		var sel=$("<select />");
		sel.append('<option value="">Add Column</option>');
		sel.append('<option value="">----------</option>');
		
		$.each(this.allparams, function(i,j,k) {
			if (self.ts.tablekeys.indexOf(j) == -1) {
				sel.append('<option value="'+j+'">'+j+'--'+self.paramdefs[j].desc_short+'</option>');
			}

		});
		
		sel.change(function(){self.build_addparam($(this).val())});

		var s=$('<input type="button" value="Submit" />').click(function(e){self.build_viewdef()});
		
		p.append(this.viewdeftable,sel,"<br/>",s);
		p.show();
		
	},
	
	event_removetablekey: function(e) {
		$(e.target).parent().parent().remove();;
	},
	
	build_addparam: function(param) {
		if (!param){return}
		this.ts.tablekeys.push(param);
		this.build_toggleprop();
	},
	
	build_viewdef: function() {
		var viewdef=[];
		var tablekeys=[];
		var macros=[];

		$("tr",this.viewdeftable).each(function(i,j,k) {
			e=$(this)
			if (parseInt(e.attr("data-macro"))) {
				console.log("macro");
				var name=$("input[name='name']",e).val();
				var args=$("input[name='args']",e).val();
				viewdef.push("$@"+name+"("+args+")");
				tablekeys.push(name+"("+args+")");
				macros[name+"("+args+")"]=[name,args];
			} else {
				viewdef.push("$$"+e.attr("data-param"));
				tablekeys.push(e.attr("data-param"));
			}
		});
		
		this.ts.viewdef=viewdef.join(" ");
		this.ts.macros=macros;
		this.ts.tablekeys=tablekeys;
		this.refresh();
		
	},
	
	editcol: function(e) {
		var editkey=$(e.target).attr("data-editkey");
	},
	
	event_query: function(e) {
		var query=$(e.target).prev().val();
		this.ts.query=query;
		this.refresh();
	},
	
	event_clear: function(e) {
		this.ts.query=null;
		this.refresh();
	},
	
	event_setcount: function(e) {
		var count=parseInt($(e.target).val());
		this.setcount(count);
	},
	
	event_setpos: function(e) {
		var pos=parseInt($(e.target).attr("data-pos"));
		this.setpos(pos);
	},	
	
	event_sortkey: function(e) {
		var key=$(e.target).attr("data-sortkey");
		this.sortkey(key)
	},
	
	setcount: function(count) {
		this.ts.pos=0;
		this.ts.count = count;
		this.refresh();
	},
	
	setpos: function(pos) {
		this.ts.pos=pos;
		this.refresh();
	},
	
	sortkey: function(key) {
		if (this.ts["sortkey"] == key) {this.reverse()}
		this.ts.pos=0;
		this.ts.sortkey=key;
		this.refresh();
	},

	build: function() {
		//console.log("table control build");
	}
}

$.fn.TableControl = function(opts) {
  return this.each(function() {
		new TableControl(this, opts);
	});
};

return TableControl;

})(jQuery); // End localisation of the $ function




$(document).ready(function() {
	$(".recordtable").TableControl({});
});
