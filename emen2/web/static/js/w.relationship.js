(function($) {
    $.widget("ui.RelationshipControl", {
		options: {
			recid:null,
			modal: false
		},
				
		_create: function() {
			// this.elem.bind("addparent", function(e,id){
			// 	id=parseInt(id);
			// 	self.addparent(id);
			// 	self.build_controls();
			// 	self.build_browser();
			// 	});
			// 
			// this.elem.bind("addchild", function(e,id){
			// 	id=parseInt(id);
			// 	self.addchild(id);
			// 	self.build_controls();
			// 	self.build_browser();
			// 	});
			
			// this.oparents=this.parents.slice();
			// this.ochildren=this.children.slice();
			// this.linkstate={};
			// this.build();
			
			var self=this;
			this.element.click(function() {
				self.event_click();
			});
			
		},
	
		event_click: function() {
			this.build();
		},
	
		build: function() {
			var self=this;
			this.dialog = $('<div title="Relationships" />');
			this.tablearea=$('<div/>');
			this.controlsarea=$('<div/>');
			this.dialog.append(this.controlsarea,this.tablearea);
		
			this.build_controls();
			
			var pos = this.element.offset();
			
			this.dialog.dialog({
				width:600,
				height:600,
				modal: this.options.modal,
				position: [pos.left, pos.top+this.element.outerHeight()]
			})
		
			$.jsonRPC("getchildren", [this.options.recid], function(children) {
				caches["children"][self.options.recid] = children;
				self.build_browser();
			});
			$.jsonRPC("getparents", [this.options.recid], function(parents) {
				caches["parents"][self.options.recid] = parents;
				self.build_browser();
			});
		
		},

		build_controls: function() {
			
		},
		
		build_browser: function() {
			var self=this;
			
			var p = caches["parents"][this.options.recid];
			var c = caches["children"][this.options.recid];
			if (p == null || c == null) {
				this.tablearea.html("Loading...");
				return
			}
			
			this.tablearea.empty();
			var t = $('<table style="width:100%"/>');
			var l = p.length;
			if (c.length > l) {l = c.length}
			
			for (var i=0;i<l;i++) {
				var row = $('<tr />');
				var td_p = $('<td /');
				var td_r = $('<td />');
				var td_c = $('<td />');
				
				if (i==0) {
					td_r.html('')
				}
				
				
				row.append(td_p, td_r, td_c);
			}
			this.tablearea.append(t);
			
			


		},


		// 	
		// build_controls: function() {
		// 	this.controlsarea.empty();
		// 	var self=this;
		// 	this.controlsarea.append($('<input type="button" value="Add Parent" />').click(function(){self.addparentpopup(this)}));
		// 	this.controlsarea.append($('<input type="button" value="Add Child" />').click(function(){self.addchildpopup(this)}));
		// 	this.controlsarea.append($('<input type="button" value="Reset" />').click(function(){self.reset();self.build_controls();self.build_browser();}));
		// 	this.controlsarea.append($('<input type="button" value="Apply Changes" />').click(function(){self.save_links()}));
		// },
		// 	
		// build_browser: function() {
		// 	this.tablearea.empty();
		// 
		// 	this.table = $('<table class="map" cellpadding="0" cellspacing="0" />');
		// 	var len=parents.length;
		// 	if (children.length > len) len=children.length;		
		// 
		// 	var self=this;
		// 
		// 	var header=$('<tr />');
		// 	header.append($('<td><h6>Parents</h6></td>').append(
		// 		$(' <span> [X]</span>').click(function(){self.removeallparents();self.build_controls();self.build_browser();})
		// 		));
		// 	header.append('<td />');
		// 	header.append('<td><h6>This Record</h6></td><td />');
		// 	header.append($('<td><h6>Children</h6></td>').append(
		// 		$(' <span> [X]</span>').click(function(){self.removeallchildren();self.build_controls();self.build_browser();})
		// 		));
		// 	this.table.append(header);
		// 
		// 
		// 	for (var i=0;i<len;i++) {
		// 		var row=$('<tr></tr>');
		// 	
		// 	
		// 		if (this.parents[i]!=null) {
		// 	
		// 			var img="next";
		// 			if (this.parents.length > 1 && i==0) {img="branch_next"}
		// 			if (this.parents.length > 1 && i>0) {img="branch_both"}
		// 			if (this.parents.length > 1 && i==this.parents.length-1) {img="branch_up"}				
		// 
		// 			var button=$('<td class="'+img+' editablelink"> </td>');
		// 			button.data("recid",this.parents[i]);
		// 			button.click(function(){
		// 				self.removeparent($(this).data("recid"))
		// 				self.build_browser();
		// 				self.build_controls();
		// 				});
		// 			var item=$('<td class="relationshipcontrol_pc"><span class="action"></span><span class="name"><a href="'+EMEN2WEBROOT+'/db/record/'+this.parents[i]+'/">'+caches["recnames"][this.parents[i]]+'</a></span></td>');
		// 			item.data("recid",this.parents[i]);
		// 			var tag=this.getstatetag(this.parents[i])
		// 			item.addClass(tag);		
		// 			if (tag=="removed") {
		// 				item.children(".action").html("U");
		// 				item.children(".action").click(function(){
		// 					//console.log("test");
		// 					self.addparent($(this).parent().data("recid"));
		// 					self.build();
		// 				});
		// 			} else if (tag=="changed") {
		// 				item.children(".action").html("U");
		// 				item.children(".action").click(function(){
		// 					self.nullparent($(this).parent().data("recid"));
		// 					self.build();
		// 				});
		// 			}
		// 
		// 			row.append(item, button);
		// 
		// 
		// 		} else {
		// 			row.append('<td /><td />');
		// 		}
		// 	
		// 		if (i==0) {
		// 			row.append('<td>'+caches["recnames"][this.recid]+'</td><td />'); //cache_getrecname(this.recid)
		// 		}	else {
		// 			row.append('<td /><td />');
		// 		}
		// 	
		// 		if (this.children[i]!=null) {
		// 
		// 			var img="next_reverse";
		// 			if (this.children.length > 1 && i==0) {img="branch_next_reverse"}
		// 			if (this.children.length > 1 && i>0) {img="branch_both_reverse"}
		// 			if (this.children.length > 1 && i==this.children.length-1) {img="branch_up_reverse"}
		// 
		// 			var button=$('<td class="'+img+' editablelink"> </td>');
		// 			button.data("recid",this.children[i]);
		// 			button.click(function(){
		// 				self.removechild($(this).data("recid"))
		// 				self.build_browser();
		// 				self.build_controls();
		// 				});
		// 			var item=$('<td class="relationshipcontrol_pc"><span class="action"></span><span class="name"><a href="'+EMEN2WEBROOT+'/db/record/'+this.children[i]+'/">'+caches["recnames"][this.children[i]]+'</a></span></td>');//cache_getrecname(this.children[i])
		// 			item.data("recid",this.children[i]);
		// 			var tag=this.getstatetag(this.children[i])
		// 			item.addClass(tag);		
		// 			if (tag=="removed") {
		// 				item.children(".action").html("U");
		// 				item.children(".action").click(function(){
		// 					//console.log("test");
		// 					self.addchild($(this).parent().data("recid"));
		// 					self.build();
		// 				});
		// 			} else if (tag=="changed") {
		// 				item.children(".action").html("U");
		// 				item.children(".action").click(function(){
		// 					self.nullchild($(this).parent().data("recid"));
		// 					self.build();
		// 				});
		// 			}				
		// 			row.append(button, item);
		// 		
		// 		} else {
		// 			row.append('<td /><td />');
		// 		}
		// 	
		// 		this.table.append(row);
		// 	}
		// 
		// 	this.tablearea.append(this.table);
		// 
		// },
		// 	
		// getstatetag: function(precid) {
		// 	var state=this.linkstate[precid];
		// 	if (state == "removeparent" || state == "removechild") {return "removed"};
		// 	if (state == "addparent" || state == "addchild") {return "changed"};
		// 	return ""
		// },
		// 	
		// addparentpopup: function(el) {
		// 	new Browser(el, {recid:recid, parentobj:this.elem, parentevent:"addparent"});
		// },
		// 	
		// addchildpopup: function(el) {
		// 	new Browser(el, {recid:recid, parentobj:this.elem, parentevent:"addchild"});		
		// },
		// 	
		// reset: function() {
		// 	this.linkstate={};
		// 	this.children=this.ochildren.slice();
		// 	this.parents=this.oparents.slice();
		// },
		// addparent: function(id) {
		// 	if (this.parents.indexOf(id) == -1) {this.parents.push(id)};
		// 	if (this.linkstate[id]=="removeparent") {this.linkstate[id]=""}
		// 	else {this.linkstate[id]="addparent"}
		// },
		// addchild: function(id) {
		// 	if (this.children.indexOf(id) == -1) {this.children.push(id)};
		// 	if (this.linkstate[id]=="removechild") {this.linkstate[id]=""}
		// 	else {this.linkstate[id]="addchild"}
		// },
		// removeparent: function(parentid) {
		// 	if (this.parents.indexOf(parentid) == -1) return	
		// 	this.linkstate[parentid]="removeparent";
		// },
		// removechild: function(childid) {
		// 	if (this.children.indexOf(childid) == -1) return	
		// 	this.linkstate[childid]="removechild";
		// },
		// 	
		// nullchild: function(precid) {
		// 	if (this.children.indexOf(precid) > -1) {this.children.splice(this.children.indexOf(precid),1)}
		// 	this.linkstate[precid]="";
		// },
		// 	
		// nullparent: function(precid) {
		// 	if (this.parents.indexOf(precid) > -1) {this.parents.splice(this.parents.indexOf(precid),1)}
		// 	this.linkstate[precid]="";
		// },
		// 	
		// removeallparents: function() {
		// 	for (var i=0;i<this.parents.length;i++) {
		// 		this.linkstate[this.parents[i]]="removed";
		// 	}
		// 	this.parents=[];
		// },
		// 	
		// removeallchildren: function() {
		// 	for (var i=0;i<this.children.length;i++) {
		// 		this.linkstate[this.children[i]]="removed";
		// 	}		
		// 	this.children=[];
		// }, 
		// 	
		// save_links: function() {
		// 	
		// 	var self=this;
		// 	var actions={};
		// 	var all=this.parents.concat(this.children);
		// 	for (var i=0;i<all.length;i++) {
		// 		var state=this.linkstate[all[i]];
		// 		if (actions[state]==null) {actions[state]=[]};
		// 		actions[state].push(all[i]);
		// 	}
		// 	
		// 	//console.log(actions);
		// 	this.rpcqueue = 0;
		// 
		// 	if (actions["removeparent"]!=null) {
		// 		for (var i=0;i<actions["removeparent"].length;i++) {
		// 			this.rpc("pcunlink",[actions["removeparent"][i],this.recid]);
		// 		}
		// 	}
		// 
		// 
		// 	if (actions["removechild"]!=null) {
		// 		for (var i=0;i<actions["removechild"].length;i++) {
		// 			this.rpc("pcunlink",[this.recid, actions["removechild"][i]]);				
		// 		}
		// 	}
		// 
		// 	if (actions["addparent"]!=null) {
		// 		for (var i=0;i<actions["addparent"].length;i++) {
		// 			this.rpc("pclink",[actions["addparent"][i], this.recid]);
		// 		}
		// 	}
		// 
		// 	if (actions["addchild"]!=null) {
		// 		for (var i=0;i<actions["addchild"].length;i++) {
		// 			this.rpc("pclink",[this.recid, actions["addchild"][i]]);				
		// 		}
		// 	}						
		// 
		// },
		// 	
		// rpc: function(method, args) {
		// 	this.rpcqueue++;
		// 	var self=this;
		// 	$.jsonRPC(method,[args[0], args[1]], function(result) {
		// 		self.checkqueue();
		// 	});					
		// 
		// },
		// 	
		// checkqueue: function() {
		// 	//console.log(this.rpcqueue);
		// 	this.rpcqueue--;
		// 	if (this.rpcqueue==0) {
		// 		notify_post(window.location.pathname, ["Relationships Saved"]);
		// 	}
		// },
		// 	
		// postnotify: function(message) {
		// 	var addr=window.location.pathname;
		// 	var f=$("<form>")
		// 	f.attr("action",addr);
		// 	f.attr("method","POST");
		// 	var fin=$('<input type="hidden" name="notify___json" value="" />');
		// 	fin.val($.toJSON([message]));
		// 	f.append(fin);
		// 	$(document.body).append(f);
		// 	f.submit();		
		// },
				
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);	
