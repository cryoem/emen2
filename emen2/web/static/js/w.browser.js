function Browser(elem, opts) {
  if (typeof(opts) != "object") opts = {};
  $.extend(this, Browser.DEFAULT_OPTS, opts);
  this.root = elem;
  this.init();
};

Browser.DEFAULT_OPTS = {
		parents: null,
		children: null,
		recid: null,
		parentobj: null,
		parentevent: null,
		cb: null,
		keytype: "record",
		rel: "children",
		mode: "browse"
};

Browser.prototype = {
	
	init: function() {
		this.currentid=this.recid;
		this.container = $('<div class="modalbrowser_container clearfix" />');
		this.elem = $('<div class="modalbrowser_container_inner clearfix" />');
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
		this.statusimg=$('<img src="'+EMEN2WEBROOT+'/images/blank.png" class="floatleft">');
		
		
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

		var title=$('<div class="modalbrowser_title clearfix"><span class="floatleft">Record Chooser</span></div>').append(
			this.statusimg, 
			$('<span class="floatright"></span>').append(
				this.gotorecord,
				gotorecordbutton,
				'<span class="modalbrowser_spacer"></span>',
				'Bookmarks:',
				bookmarks,
				'<span class="modalbrowser_spacer"></span>',
				//$('<input type="button" value="Select" />').click(function(){
				//	self.ok();
				//}), 
				$('<input type="button" value="Close" />').click(function(){
					self.close();
				})
			)
		);

		this.elem.append(title);
		this.tablearea=$('<div class="modalbrowser_tablearea clearfix" />');
		this.elem.append(this.tablearea);

	},
	
	build_map: function() {
		// build a map-style browser
		this.tablearea.empty();
		this.statusimg.attr("src",EMEN2WEBROOT+"/images/blank.png");
		this.tablearea.load(EMEN2WEBROOT+'/db/map/'+this.keytype+'/'+this.currentid+'/'+this.rel+'/');

	},
	
	build_browser: function() {
		// build a column-style browser
		
		this.children = this.sortbyrecname(this.children);
		this.parents = this.sortbyrecname(this.parents);
		
		this.statusimg.attr("src",EMEN2WEBROOT+"/images/blank.png");

		this.tablearea.empty();
		var self=this;
		var len=this.parents.length;
		if (this.children.length >= len) len=this.children.length;	

		var ptable = $('<table class="map modalbrowser_table floatleft" cellpadding="0" cellspacing="0" />');
		var ctable = $('<table class="map modalbrowser_table floatleft" cellpadding="0" cellspacing="0" />');		

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
				var item=$('<td class="jslink">'+caches["recnames"][this.parents[i]]+'</td>');
				item.data("recid",this.parents[i]);
				item.click(function() {self.select($(this).data("recid"));});
				prow.append(item, '<td class="'+pimg+'"></td>');
			} else {
				prow.append('<td/><td/>');
			}
			if (this.children[i]!=null) {
				var item=$('<td class="jslink">'+caches["recnames"][this.children[i]]+'</td>');
				item.data("recid",this.children[i]);
				item.click(function() {self.select($(this).data("recid"));});
				crow.append('<td class="'+cimg+'"></td>', item);				
			} else {
				crow.append('<td/><td/>');
			}
			ptable.append(prow);
			ctable.append(crow);
		}
		
		this.infoc = $('<div class="modalbrowser_info floatleft" />');
		this.infoc.append('<div class="modalbrowser_info_name">'+caches["recnames"][this.currentid]+'</div>');
		this.infoc.append(
			$('<input type="button" value="Select" />').click(function(){
					self.ok();
				})
			);
		this.info_view = $('<div class="modalbrowser_info_view"></div>');
		this.infoc.append(this.info_view);
		
		this.tablearea.append(ptable, this.infoc, ctable);
		

	},
	
	close: function() {
		this.container.remove();
	},
	
	getchildren: function() {
		this.children=null;
		var self=this;
		$.jsonRPC("getchildren",[this.currentid], function(result) {
			self.children=result;
			self.checklocalindex();
		});
	},
	
	getparents: function() {
		this.parents=null;
		var self=this;
		$.jsonRPC("getparents",[this.currentid], function(result) {
			self.parents=result;
			self.checklocalindex();
		});
	},
	
	getrecnames: function(recids, cb) {
		var self=this;
		$.jsonRPC("getrecordrecname",[recids], function(result) {
			$.each(result, function(k,v) {
					caches["recnames"][k]=v;
			});
		
			self.checklocalindex();
			self.build_browser();
		});		
	},
	
	getrecord: function(irecid) {
		var self=this;
		$.get(EMEN2WEBROOT+"/db/recordview/"+irecid+"/dicttable/", {}, function(data) {
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
			if (caches["recnames"][getnames_needed[i]] == null) {
				getnames.push(getnames_needed[i]);
			}
		}
		if (getnames.length > 0) {
			this.getrecnames(getnames, this.build_browser);
			
			for (var i=0;i<getnames.length;i++) {
				caches["recnames"][getnames[i]] = "Record "+getnames[i];
			}
			
		} else {
			this.build_browser();
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
	
	get_map: function() {
		this.build_map();
	},
	
	select: function(newid) {
		this.statusimg.attr("src",EMEN2WEBROOT+"/images/spinner2.gif");
		this.parents=null;
		this.children=null;
		this.currentid=newid;
		if (this.mode=="map") {
			this.get_map();
		} else {
			this.getchildren();
			this.getparents();
		}
	},
	
	sortbyrecname: function(list) {
		var reversenames={};
		var sortnames=[];
		var retnames=[];

		if (list==null) {return []}
		
		for (var i=0;i<list.length;i++) {
		    reversenames[caches["recnames"][list[i]]]=list[i];
		    sortnames.push(caches["recnames"][list[i]]);
		}
		sortnames.sort();
		for (var i=0;i<sortnames.length;i++) {
			retnames.push(reversenames[sortnames[i]]);
		}
		return retnames
	}
	
}
