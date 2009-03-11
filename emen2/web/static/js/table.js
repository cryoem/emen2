
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
		//$(".table_properties",this.elem).TableColumnControl({tablekeys:this.ts.tablekeys, macros:this.ts.macros, rectype:this.ts.rectype, table:this});
		this.tablecontrol = new TableColumnControl($(".table_properties",this.elem),{tablekeys:this.ts.tablekeys, macros:this.ts.macros, rectype:this.ts.rectype, table:this});
		//$(".table_properties",this.elem).click(function(e){self.tablecolumncontrol.event_toggleprop(e)});
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
		this.tablecontrol.hide();
		this.ts.showtablestate=0;
		$.postJSON("/db/table/list/",this.ts,function(data){self.replace(data)});
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





/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////



TableColumnControl = (function($) { // Localise the $ function

function TableColumnControl(elem, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, TableColumnControl.DEFAULT_OPTS, opts);
  this.elem = $(elem);  
  this.init();
	//console.log(opts.tablekeys);
};

TableColumnControl.DEFAULT_OPTS = {
};

TableColumnControl.prototype = {
	
	init: function() {
		var self=this;
		var pos=this.elem.position();
		var th=$(".table_header",this.table.elem);
		
		//console.log(this.elem.offset());

		this.built=0;
		this.p=$('<div class="table_keys_menu" />');
		this.p.css({position:"absolute", width:400, top:th.offset().top+th.outerHeight(),left:pos.left-250});

		//this.elem.css({background:"white",border:"2px solid #ccc", padding:4});


		$("body").append(this.p);
		this.elem.click(function(e){self.event_toggleprop(e)});

	},
	
	event_toggleprop: function(e) {

		// show the chooser, get paramdefs if necessary
		var self=this;
				
		if (this.built==0) {
			$.jsonRPC("getrecorddef",[this.rectype],function(recdef) {
				self.allparams = recdef.paramsK;
				$.jsonRPC("getparamdefs",[recdef.paramsK],function(paramdefs) {
					self.paramdefs=paramdefs
					self.build();
					self.show();
				})
			});
			
		} else {

			if (this.disp==1) {
				self.hide();
			} else {
				self.show();
			}

		}
	},
	
	build: function() {
		
		this.built = 1;
		this.p.empty();
		this.viewdeftable=$('<table cellspacing="0" cellpadding="0" />');

		this.viewdeftable.append("<thead><th></th><th>Name</th><th>Desc / Args</th></thead>");

		var self=this;
		var nonmacro=[];

		$.each(this.tablekeys, function(i,j,k){
			if (!self.macros[j]){nonmacro.push(j)}
		});
		
		for (var i=0;i<this.tablekeys.length;i++) {
			
			var ismacro=0;
			j=this.tablekeys[i];
			//if (!this.macros[j]) {
			if (!this.paramdefs[j]) {
				ismacro=1;
			};

			var row=$('<tr />');
			var x=$('<img src="/images/remove_small.png" alt="remove" />').click(function(e){self.event_removetablekey(e)});
			var up=$('<img src="/images/sort_0.png" alt="up" />').click(function(e){self.event_tablekey_move(e,1)});
			var down=$('<img src="/images/sort_1.png" alt="down" />').click(function(e){self.event_tablekey_move(e,-1)});
			var b=$("<td/>");
			b.append(x,up,down);
			row.append(b);
			
			row.attr("data-pos",i);
			row.attr("data-macro",ismacro);
						
			if (!ismacro) {
				row.attr("data-name",j);
				row.attr("data-args","");
				row.append('<td>'+j+'</td>');
				row.append('<td>'+this.paramdefs[j].desc_short+'</td>');
			} else {
				row.attr("data-name",this.macros[j][0]);
				row.attr("data-args",this.macros[j][1]);
				row.append('<td><input name="name" type="text" value="'+this.macros[j][0]+'" /></td>');
				row.append('<td><input name="args" type="text" value="'+this.macros[j][1]+'" /></td></tr>');
			}
			this.viewdeftable.append(row);

		}
		
		var sel=$("<select />");
		sel.append('<option value="">Add Parameter</option>');
		sel.append('<option value="">----------</option>');
		
		$.each(this.allparams, function(i,j,k) {
			if (self.tablekeys.indexOf(j) == -1) {
				sel.append('<option value="'+j+'">'+j+' -- '+self.paramdefs[j].desc_short+'</option>');
			}
		});
		
		var example_macros = {childcount:"Count Children of *arg type",parentvalue:"Values of parent records for parameter *arg",recname:"Generated record title"}
		
		var selm=$("<select />");
		selm.append('<option value="">Add Macro</option>');
		selm.append('<option value="">----------</option>');		
		$.each(example_macros, function(i,j,k) {
			console.log(i);
			selm.append('<option value="'+i+'">'+i+' -- '+j+'</option>');
		});		
		selm.change(function(){self.build_addmacro($(this).val())});

		// submit/close
		var s=$('<input type="button" value="Submit" />').click(function(e){self.build_viewdef();self.set_viewdef();self.table.refresh();});
		var c=$('<input type="button" value="Close" />').click(function(e){self.hide()});
		
		this.p.append(this.viewdeftable,sel,selm,"<br/>",s,c);
		
	},
	
	show: function() {
		//this.p.fadeIn();
		this.disp=1;
		this.elem.addClass("table_properties_active");
		this.p.show();
	},
	
	hide: function() {
		//this.p.fadeOut();
		this.disp=0;
		this.elem.removeClass("table_properties_active");		
		this.p.hide();
	},
	
	event_tablekey_move: function(e,i) {
		
		// clone w/ events
		var tp=$(e.target).parent().parent();//.attr("data-param");
		var tpn=tp.clone(true);
		var t;
		if (i==1) {
			t=tp.prev();
		} else {
			t=tp.next();
		}

		// move the element
		if (t.length>0) {
			tp.remove();
			if (i==1) {
				t.before(tpn);
			} else {
				t.after(tpn);
			}
		}

	},
	
	event_removetablekey: function(e) {
		$(e.target).parent().parent().remove();;
	},
	
	build_addparam: function(param) {
		if (!param){return}
		this.tablekeys.push(param);
		this.build();
	},
	
	build_addmacro: function(macro) {
		if (!macro){return}
		this.tablekeys.push(macro+"()");
		this.macros[macro+"()"]=[macro,""];
		this.build();
	},
	
	build_viewdef: function() {
		
		// generate viewdef from table
		var viewdef=[];
		var tablekeys=[];
		var macros=[];

		$("tr",this.viewdeftable).each(function(i,j,k) {
			e=$(this)
			if (parseInt(e.attr("data-macro"))) {
				var name=$("input[name='name']",e).val();
				var args=$("input[name='args']",e).val();
				viewdef.push("$@"+name+"("+args+")");
				tablekeys.push(name+"("+args+")");
				macros[name+"("+args+")"]=[name,args];
			} else {
				viewdef.push("$$"+e.attr("data-name"));
				tablekeys.push(e.attr("data-name"));
			}
		});
		
		this.viewdef=viewdef.join(" ");
		this.tablekeys=tablekeys;
		this.macros=macros;

	},
	
	set_viewdef: function() {
		// set the parent state before refresh
		this.table.ts.viewdef=this.viewdef;
		this.table.ts.tablekeys=this.tablekeys;
		this.table.ts.macros=this.macros;
	}
	
}

$.fn.TableColumnControl = function(opts) {
    return this.each(function() {
		new TableColumnControl(this, opts);
	});
};

return TableColumnControl;

})(jQuery); // End localisation of the $ function
