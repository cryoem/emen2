/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////



relationshipcontrol = (function($) { // Localise the $ function

function relationshipcontrol(elem, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, relationshipcontrol.DEFAULT_OPTS, opts);
  this.elem = $(elem);  
  this.init();
};

relationshipcontrol.DEFAULT_OPTS = {
		parents: [],
		children: [],
		recid: null
};

relationshipcontrol.prototype = {
	
	init: function() {

		var self=this;

		this.elem.bind("addparent", function(e,id){
			//console.log("adding parent");
			id=parseInt(id);
			self.addparent(id);
			self.build_controls();
			self.build_map();
			});
			
		this.elem.bind("addchild", function(e,id){
			id=parseInt(id);
			self.addchild(id);
			self.build_controls();
			self.build_map();
			});

		this.oparents=this.parents.slice();
		this.ochildren=this.children.slice();
		this.linkstate={};
		this.build();
	},
	
	build: function() {
		this.elem.empty();
		this.tablearea=$('<div/>');
		this.controlsarea=$('<div class="relationship_add" />');
		this.elem.append(this.controlsarea,this.tablearea);
		this.build_controls();
		this.build_map();
	},
	
	build_controls: function() {
		this.controlsarea.empty();
		var self=this;

//		var src=[this.addc, this.addp, this.removedc, this.removedp]
//		var srctxt=["Children to add","Parents to add", "Children to remove", "Parents to remove"];

// 		for (var i=0;i<src.length;i++) {
// 			if (src[i].length > 0) {
// 				var carea=$('<div class="relationshipcontrol_controls_title">'+srctxt[i]+' ('+src[i].length+' items)</div>');
// 				var carea2=$('<div class="relationshipcontrol_controls_box clearfix"/>');
// 				$.each(src[i], function(k,v) {
// 					carea2.append('<div class="relationshipcontrol_controls_box_item floatleft">'+getrecname(v)+'</div>');
// 				});
// 				this.controlsarea.append(carea,carea2);
// 			}
// 		}

		this.controlsarea.append($('<input type="button" value="Add Parent" />').click(function(){self.addparentpopup(this)}));
		this.controlsarea.append($('<input type="button" value="Add Child" />').click(function(){self.addchildpopup(this)}));
		this.controlsarea.append($('<input type="button" value="Reset" />').click(function(){self.reset();self.build_controls();self.build_map();}));
		this.controlsarea.append($('<input type="button" value="Apply Changes" />').click(function(){self.save_links()}));
		//this.controlsarea.append();
	},
	
  build_map: function() {
		this.tablearea.empty();
		
		this.table = $('<table class="map" cellpadding="0" cellspacing="0" />');
		var len=parents.length;
		if (children.length > len) len=children.length;		

		var self=this;

		var header=$('<tr />');
		header.append($('<td><h6>Parents</h6></td>').append(
			$(' <span> [X]</span>').click(function(){self.removeallparents();self.build_controls();self.build_map();})
			));
		header.append('<td />');
		header.append('<td><h6>This Record</h6></td><td />');
		header.append($('<td><h6>Children</h6></td>').append(
			$(' <span> [X]</span>').click(function(){self.removeallchildren();self.build_controls();self.build_map();})
			));
		this.table.append(header);
		
		
		for (var i=0;i<len;i++) {
			var row=$('<tr></tr>');
			
			if (this.parents[i]!=null) {

				var img="next";
				if (this.parents.length > 1 && i==0) {img="branch_next"}
				if (this.parents.length > 1 && i>0) {img="branch_both"}
				if (this.parents.length > 1 && i==this.parents.length-1) {img="branch_up"}				

				var button=$('<td class="'+img+' editablelink"> </td>');
				button.data("recid",this.parents[i]);
				button.click(function(){
					self.removeparent($(this).data("recid"))
					self.build_map();
					self.build_controls();
					});
				var item=$('<td class="relationshipcontrol_pc"><span class="action"></span><span class="name"><a href="/db/record/'+this.parents[i]+'">'+getrecname(this.parents[i])+'</a></span></td>');
				item.data("recid",this.parents[i]);
				var tag=this.getstatetag(this.parents[i])
				item.addClass(tag);		
				if (tag=="removed") {
					item.children(".action").html("U");
					item.children(".action").click(function(){
						//console.log("test");
						self.addparent($(this).parent().data("recid"));
						self.build();
					});
				} else if (tag=="changed") {
					item.children(".action").html("U");
					item.children(".action").click(function(){
						self.nullparent($(this).parent().data("recid"));
						self.build();
					});
				}

				row.append(item, button);


			} else {
				row.append('<td /><td />');
			}
			
			if (i==0) {
				row.append('<td>'+getrecname(this.recid)+'</td><td />')
			}	else {
				row.append('<td /><td />');
			}
			
			if (this.children[i]!=null) {

				var img="next_reverse";
				if (this.children.length > 1 && i==0) {img="branch_next_reverse"}
				if (this.children.length > 1 && i>0) {img="branch_both_reverse"}
				if (this.children.length > 1 && i==this.children.length-1) {img="branch_up_reverse"}

				var button=$('<td class="'+img+' editablelink"> </td>');
				button.data("recid",this.children[i]);
				button.click(function(){
					self.removechild($(this).data("recid"))
					self.build_map();
					self.build_controls();
					});
				var item=$('<td class="relationshipcontrol_pc"><span class="action"></span><span class="name"><a href="/db/record/'+this.children[i]+'">'+getrecname(this.children[i])+'</a></span></td>');
				item.data("recid",this.children[i]);
				var tag=this.getstatetag(this.children[i])
				item.addClass(tag);		
				if (tag=="removed") {
					item.children(".action").html("U");
					item.children(".action").click(function(){
						//console.log("test");
						self.addchild($(this).parent().data("recid"));
						self.build();
					});
				} else if (tag=="changed") {
					item.children(".action").html("U");
					item.children(".action").click(function(){
						self.nullchild($(this).parent().data("recid"));
						self.build();
					});
				}				
				row.append(button, item);
				
			} else {
				row.append('<td /><td />');
			}
			
			this.table.append(row);
		}
		
		this.tablearea.append(this.table);

	},
	
	getstatetag: function(precid) {
		var state=this.linkstate[precid];
		if (state == "removeparent" || state == "removechild") {return "removed"};
		if (state == "addparent" || state == "addchild") {return "changed"};
		return ""
	},
	
	addparentpopup: function(el) {
		new relationshipbrowser(el, {recid:recid, parentobj:this.elem, parentevent:"addparent"});
	},
	
	addchildpopup: function(el) {
		new relationshipbrowser(el, {recid:recid, parentobj:this.elem, parentevent:"addchild"});		
	},
	
	reset: function() {
		this.linkstate={};
		this.children=this.ochildren.slice();
		this.parents=this.oparents.slice();
	},
	addparent: function(id) {
		if (this.parents.indexOf(id) == -1) {this.parents.push(id)};
		if (this.linkstate[id]=="removeparent") {this.linkstate[id]=""}
		else {this.linkstate[id]="addparent"}
	},
	addchild: function(id) {
		if (this.children.indexOf(id) == -1) {this.children.push(id)};
		if (this.linkstate[id]=="removechild") {this.linkstate[id]=""}
		else {this.linkstate[id]="addchild"}
	},
	removeparent: function(parentid) {
		if (this.parents.indexOf(parentid) == -1) return	
		this.linkstate[parentid]="removeparent";
	},
	removechild: function(childid) {
		if (this.children.indexOf(childid) == -1) return	
		this.linkstate[childid]="removechild";
	},
	
	nullchild: function(precid) {
		if (this.children.indexOf(precid) > -1) {this.children.splice(this.children.indexOf(precid),1)}
		this.linkstate[precid]="";
	},
	
	nullparent: function(precid) {
		if (this.parents.indexOf(precid) > -1) {this.parents.splice(this.parents.indexOf(precid),1)}
		this.linkstate[precid]="";
	},
	
	removeallparents: function() {
		for (var i=0;i<this.parents.length;i++) {
			this.linkstate[this.parents[i]]="removed";
		}
		this.parents=[];
	},
	
	removeallchildren: function() {
		for (var i=0;i<this.children.length;i++) {
			this.linkstate[this.children[i]]="removed";
		}		
		this.children=[];
	}, 
	
	save_links: function() {
	
		var self=this;
		var actions={};
		var all=this.parents.concat(this.children);
		for (var i=0;i<all.length;i++) {
			var state=this.linkstate[all[i]];
			if (actions[state]==null) {actions[state]=[]};
			actions[state].push(all[i]);
		}
	
		//console.log(actions);
		this.rpcqueue = 0;
		
		if (actions["removeparent"]!=null) {
			for (var i=0;i<actions["removeparent"].length;i++) {
				this.rpc("pcunlink",[actions["removeparent"][i],this.recid]);
			}
		}


		if (actions["removechild"]!=null) {
			for (var i=0;i<actions["removechild"].length;i++) {
				this.rpc("pcunlink",[this.recid, actions["removechild"][i]]);				
			}
		}
		
		if (actions["addparent"]!=null) {
			for (var i=0;i<actions["addparent"].length;i++) {
				this.rpc("pclink",[actions["addparent"][i], this.recid]);
			}
		}
		
		if (actions["addchild"]!=null) {
			for (var i=0;i<actions["addchild"].length;i++) {
				this.rpc("pclink",[this.recid, actions["addchild"][i]]);				
			}
		}						
		
	},
	
	rpc: function(method, args) {
		this.rpcqueue++;
		var self=this;
		$.jsonRPC(method,[args[0], args[1], ctxid, "record"], function(result) {
			self.checkqueue();
		});					
		
	},
	
	checkqueue: function() {
		//console.log(this.rpcqueue);
		this.rpcqueue--;
		if (this.rpcqueue==0) {
			notify_post(window.location.pathname, ["Relationships Saved"]);
		}
	},
	
	postnotify: function(message) {
		var addr=window.location.pathname;
		var f=$("<form>")
		f.attr("action",addr);
		f.attr("method","POST");
		var fin=$('<input type="hidden" name="notify___json" value="" />');
		fin.val($.toJSON([message]));
		f.append(fin);
		$(document.body).append(f);
		f.submit();		
	}
	
}

$.fn.relationshipcontrol = function(opts) {
    return this.each(function() {
			var z=new relationshipcontrol(this, opts);
			//console.log(this);
	});
};

return relationshipcontrol;

})(jQuery); // End localisation of the $ function



/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////
/////////////////////////////////////////////

function relationshipbrowser(elem, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, relationshipbrowser.DEFAULT_OPTS, opts);
  this.root = elem;
  this.init();
};

relationshipbrowser.DEFAULT_OPTS = {
		parents: null,
		children: null,
		recid: null,
		parentobj: null,
		parentevent: null,
		cb: null
};

relationshipbrowser.prototype = {
	
	init: function() {
		this.currentid=this.recid;
		this.container = $('<div class="relationshipbrowser_container clearfix" />');
		this.elem = $('<div class="relationshipbrowser_container_inner clearfix" />');
		this.elem.css("left", ($(window).width()-896)/2);
		var toph=($(window).height()-730)/2;
		if (toph<=10) toph=10;
		this.elem.css("top", toph);
		$(document.body).append(this.container.append(this.elem));
		this.build();	
		this.select(recid);
		this.failgetnames=[];
	},
	
	build: function() {
		var self=this;
		
		this.elem.empty();
		this.statusimg=$('<img src="/images/blank.png" class="floatleft">');
		
		
		this.gotorecord=$('<input type="text" size="8" />');
		var gotorecordbutton=$('<input type="button" value="Go To Record" />').click(function() {
			//console.log(self.gotorecord.val());
			self.select(self.gotorecord.val());
			});
		
		var bookmarks=$('<select />').change(function() {
			self.select($(this).val());
		});
		var bm={
			"NCMI":136,
			"Microscopes":1,
		}
		bookmarks.append('<option value="0"></option>');
		$.each(bm, function(k,v) {
			bookmarks.append('<option value="'+v+'">'+k+'</option>');
		});

		var title=$('<div class="relationshipbrowser_title clearfix"><span class="floatleft">Record Chooser</span></div>').append(
			this.statusimg, 
			$('<span class="floatright"></span>').append(
				this.gotorecord,
				gotorecordbutton,
				'<span class="relationshipbrowser_spacer"></span>',
				'Bookmarks:',
				bookmarks,
				'<span class="relationshipbrowser_spacer"></span>',
				//$('<input type="button" value="Select" />').click(function(){
				//	self.ok();
				//}), 
				$('<input type="button" value="Close" />').click(function(){
					self.close();
				})
			)
		);

		this.elem.append(title);
		this.tablearea=$('<div class="relationshipbrowser_tablearea clearfix" />');
		this.elem.append(this.tablearea);

	},
	
  build_map: function() {
		this.children = this.sortbyrecname(this.children);
		this.parents = this.sortbyrecname(this.parents);
		
		this.statusimg.attr("src","/images/blank.png");

		this.tablearea.empty();
		var self=this;
		var len=this.parents.length;
		if (this.children.length >= len) len=this.children.length;	

		var ptable = $('<table class="map relationshipbrowser_table floatleft" cellpadding="0" cellspacing="0" />');
		var ctable = $('<table class="map relationshipbrowser_table floatleft" cellpadding="0" cellspacing="0" />');		

		for (var i=0;i<len;i++) {
			var prow=$('<tr></tr>');
			var crow=$('<tr></tr>');

			var pimg="next";
			if (this.parents.length > 1 && i==0) {pimg="branch_next"}
			if (this.parents.length > 1 && i>0) {pimg="branch_both"}
			if (this.parents.length > 1 && i==this.parents.length-1) {pimg="branch_up"}				
			var cimg="next";
			if (this.children.length > 1 && i==0) {cimg="branch_next_reverse"}
			if (this.children.length > 1 && i>0) {cimg="branch_both_reverse"}
			if (this.children.length > 1 && i==this.children.length-1) {cimg="branch_up_reverse"}		

			if (this.parents[i]!=null) {
				var item=$('<td class="jslink">'+getrecname(this.parents[i])+'</td>');
				item.data("recid",this.parents[i]);
				item.click(function() {self.select($(this).data("recid"));});
				prow.append(item, '<td class="'+pimg+'"></td>');
			} else {
				prow.append('<td/><td/>');
			}
			if (this.children[i]!=null) {
				var item=$('<td class="jslink">'+getrecname(this.children[i])+'</td>');
				item.data("recid",this.children[i]);
				item.click(function() {self.select($(this).data("recid"));});
				crow.append('<td class="'+cimg+'"></td>', item);				
			} else {
				crow.append('<td/><td/>');
			}
			ptable.append(prow);
			ctable.append(crow);
		}
		
		this.infoc = $('<div class="relationshipbrowser_info floatleft" />');
		this.infoc.append('<div class="relationshipbrowser_info_name">'+getrecname(this.currentid)+'</div>');
		this.infoc.append(
			$('<input type="button" value="Select" />').click(function(){
					self.ok();
				})
			);
		this.info_view = $('<div class="relationshipbrowser_info_view"></div>');
		this.infoc.append(this.info_view);
		
		this.tablearea.append(ptable, this.infoc, ctable);
		

	},
	
	close: function() {
		this.container.remove();
	},
	
	getchildren: function(recid,cb) {
		this.children=null;
		var self=this;
		$.jsonRPC("getchildren",[this.currentid, "record", 0, ctxid], function(result) {
			self.children=result;
			self.checklocalindex();
		});
	},
	
	getparents: function(cb) {
		this.parents=null;
		var self=this;
		$.jsonRPC("getparents",[this.currentid, "record", 0, ctxid], function(result) {
			self.parents=result;
			self.checklocalindex();
		});
	},
	
	getrecnames: function(recids, cb) {
		var self=this;
		$.jsonRPC("getrecordrecname",[recids, ctxid], function(result) {
			$.each(result, function(k,v) {
					setrecname(k,v);
			});
			
			// hack to prevent infinite loop
			//for (var i=0;i<recids.length;i++) {
			//	if (getrecname(recids[i])=="undefined") {
			//		console.log();
			//		setrecname(recids[i],"(permission denied)");
			//	}
			//}
			
			self.checklocalindex();
			self.build_map();
		});		
	},
	
	getrecord: function(irecid) {
		var self=this;
		$.get("/db/recordview/"+irecid+"/table/", {}, function(data) {
			if (irecid == self.currentid) {
				self.info_view.append(data);
			}
		});
	},
	
	checklocalindex: function(cb) {
		if (this.parents == null) return;
		if (this.children == null) return;
		var getnames=[];
		var getnames_needed=[].concat(this.children).concat(this.parents).concat([this.currentid]);
		for (var i=0;i<getnames_needed.length;i++) {
			if (getrecname(getnames_needed[i]) == null) {
				getnames.push(getnames_needed[i]);
			}
		}
		if (getnames.length > 0) {
			this.getrecnames(getnames, this.build_map);
			
			for (var i=0;i<getnames.length;i++) {
				setrecname(getnames[i],"Record "+getnames[i]);
			}
			
		} else {
			this.build_map();
			this.getrecord(this.currentid);
		}
	},
	
	ok: function() {
		//console.log("triggering parent event");
		//console.log(this.parentobj);
		//console.log(this.currentid);
		this.parentobj.trigger(this.parentevent, [this.currentid]);
		this.close();
	},
	
	select: function(newid) {
		this.statusimg.attr("src","/images/spinner2.gif");
		this.parents=null;
		this.children=null;
		this.currentid=newid;
		this.getchildren(recid);
		this.getparents(recid);
	},
	
	sortbyrecname: function(list) {
		var reversenames={};
		var sortnames=[];
		var retnames=[];

		if (list==null) {return []}
		
		for (var i=0;i<list.length;i++) {
		    reversenames[getrecname(list[i])]=list[i];
		    sortnames.push(getrecname(list[i]));
		}
		sortnames.sort();
		for (var i=0;i<sortnames.length;i++) {
			retnames.push(reversenames[sortnames[i]]);
		}
		return retnames
	}
	
}





/////////////////////////////////////////////