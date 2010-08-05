(function($) {
    $.widget("ui.MultiEditControl", {
		options: {
			show: false,
			recid: null
		},
				
		_create: function() {
			this.options.recid = this.options.recid || parseInt(this.element.attr("data-recid"));
			this.built = 0;
			this.bind_edit();
			this.selector = '.editable[data-recid='+this.options.recid+']';
			this.backup = this.element.html();
			if (this.options.show) {
				this.event_click();
			}
		},
		
		bind_edit: function() {
			var self = this;
			$(".label", this.element).click(function(e){self.event_click(e)});
		},
	
		bind_save: function() {
		},

		event_click: function(e) {
			var self=this;
			if (this.options.recid == "None") {
				var toget = $.makeArray($(this.selector).map(function(){return $(this).attr("data-param")}));
			} else {
				var toget = [this.options.recid];
			}
			
			$.jsonRPC("getparamdef", [toget], function(paramdefs) {
				$.each(paramdefs, function(k,v) {
					caches["paramdefs"][v.name] = v;
				});
				self.show();
			});


		},

		build: function() {
			var self = this;
			if (this.built) {
				return
			}
			this.built = 1;
			
			this.controls = $('<div class="controls"></div>')		
			
			var save = $('<input type="submit" name="save" value="Save" />');
			save.click(function(e) {self.save()});
			this.controls.append(save);
			
			if (this.options.recid!="None") {
				var cancel = $('<input type="button" value="Cancel" />').bind("click", function(e) {e.stopPropagation();self.hide()});
				this.controls.append(cancel);
			}
			this.element.append(this.controls);
		},
		
		rebind_save: function() {
			var self = this;
			var t = $('input[name=save]', this.controls);
			t.val("Retry...");
			t.one(function(e) {self.save()});
		},
	
		show: function() {
			this.build();
			$(this.selector).EditControl('hide');
			$(this.selector).EditControl('show', 0);			
			$(".label", this.element).hide();
			this.controls.show();
		},
	
		hide: function() {
			$(this.selector).EditControl('hide');
			this.controls.hide();
			$(".label", this.element).show();
		},
		
		save: function() {
			var changed = {};
			var self = this;

			var t = $('input[name=save]', this.controls);
			t.val("Saving...");

			$(this.selector).each(function() {
				var t = $(this);
				var recid = t.EditControl('getrecid');
				var value = t.EditControl('getval');
				var param = t.EditControl('getparam');				
				if (!changed[recid]) {changed[recid]={}}
				changed[recid][param] = value;
			})

			if (this.options.recid == "None") {
				return this.save_newrecord(changed["None"]);
			}

			$.jsonRPC("putrecordsvalues", [changed], function(recs) {
				$.each(recs, function() {
					record_update(this);
				});
				self.hide();
			});

		},

		save_newrecord: function(newrec) {
			var self = this;
			var updrec = caches["recs"]["None"];

			$.each(newrec, function(k,v) {
				updrec[k] = v;
			});
			
			updrec['permissions'] = $('#newrecord_permissions').PermissionControl('getusers');
			updrec['groups'] = $('#newrecord_permissions').PermissionControl('getgroups');
			updrec['recid'] = null;

			$.jsonRPC("putrecord", [updrec], 
				function(rec) {
					notify_post(EMEN2WEBROOT+'/db/record/'+rec.recid+'/', ["New record created"]);
				},
				function(e) {
					default_errback(e, function(){self.rebind_save()})
				}
			);
			
		},
	
		compare: function(a,b) {
			if (a instanceof Array && b instanceof Array) {
	  		// array comparator
				if (a.length != b.length) return false
				for (var i=0;i<a.length;i++) {
					if (a[i] != b[i]) return false
				}
				return true
			} else {
				return a==b
			}
		}
	});
})(jQuery);







(function($) {
    $.widget("ui.EditControl", {
		options: {
			show: false,
			recid: null,
			param: null
		},
				
		_create: function() {
			this.options.param = this.options.param || this.element.attr("data-param");
			this.options.recid = this.options.recid || parseInt(this.element.attr("data-recid"));
			if (isNaN(this.options.recid)) this.options.recid = "None";

			this.built = 0;
			this.rec_value = caches["recs"][this.options.recid][this.options.param];
			this.bind_edit();
			this.trygetparams = 0;
			this.element.addClass("editcontrol");
			
			if (this.options.show) {
				this.show();
			}
			
		},
	
		event_click: function(e) {
			this.show();
		},
	
		bind_edit: function() {
			var self = this;
			$(".label", this.element).click(function(e) {self.event_click(e)});
		},
		
		build: function() {
			if (this.built){
				return
			}
			this.built = 1;
				
			if (this.rec_value == null) {
				this.rec_value = "";
			}
		
			// container
			this.w = $('<span class="editcontrol"></span>');
			var self = this;
			var pd = caches["paramdefs"][this.options.param];
			var vt = pd.vartype;
			controls = true;

			// Delegate to different edit widgets
			if (vt=="html" || vt=="text") {
			
				this.editw=$('<textarea class="value" cols="80" rows="20">'+this.rec_value+'</textarea>');
				this.w.append(this.editw);			

			} else if (vt=="choice") {
			
				this.editw=$('<select></select>');
				var pdc = caches["paramdefs"][this.options.param]["choices"];
				pdc.unshift("");
			
				for (var i=0;i<pdc.length;i++) {
					var selected="";
					if (this.rec_value == pdc[i]) { selected = 'selected="selected"'; }
					this.editw.append('<option val="'+pdc[i]+'" '+selected+'>'+pdc[i]+'</option>');
				}
				this.w.append(this.editw);				
							
			} else if (vt=="datetime") {
		
				this.editw = $('<input class="value" size="18" type="text" value="'+this.rec_value+'" />');
				this.w.append(this.editw);				

			} else if (vt=="boolean") {
		
				this.editw = $("<select><option>True</option><option>False</option></select>");
				this.w.append(this.editw);				
		
			} else if (["intlist","floatlist","stringlist","userlist","urilist"].indexOf(vt) > -1) {
		
				this.editw = $('<div />');
				this.editw.ListControl({values:this.rec_value, param:this.options.param});
				this.w.append(this.editw);
				// set a different getval function..
				this.getval = function(){return self.editw.ListControl('getval')}
		
			}  else if (vt=="user") {

					this.editw = $('<input class="value" size="30" type="text" value="'+this.rec_value+'" />');
					this.editw.FindUserControl({recid:this.options.recid});
					this.w.append(this.editw);
		
			} else if (vt=="comments") {
				
					this.editw = $('<input class="value" size="30" type="text" value="" />');
						
			} else {

				this.editw = $('<input class="value" size="30" type="text" value="'+this.rec_value+'" />');
			
				if (vt=="string" || pd["choices"]) {			
					//autocomplete
				}

				this.w.append(this.editw);			
				var property = pd["property"];
				var units = pd["defaultunits"];

				if (property != null) {
					this.editw_units=$('<select></select>');
					for (var i=0;i < valid_properties[property][1].length;i++) {
						var sel = "";
						if (units == valid_properties[property][1][i]) sel = "selected";
						this.editw_units.append('<option '+sel+'>'+valid_properties[property][1][i]+'</option>');
					}
					this.w.append(this.editw_units);
				}
			}

			this.controls = $('<div class="controls"></div>')		
			this.controls.append(
				$('<input type="submit" value="Save" />').one("click", function(e) {self.save()}),
				$('<input type="button" value="Cancel" />').bind("click", function(e) {self.hide()}));
			this.w.append(this.controls);
			this.element.after(this.w);
		},
	
		show: function(showcontrols) {
			if (showcontrols==null) {showcontrols=1}
			var self = this;
		
			if (!caches["paramdefs"][this.options.param]) {
				if (this.trygetparams) {return}
				$.jsonRPC("getparamdef", [this.options.param], function(paramdef){
					caches["paramdefs"][paramdef.name]=paramdef;
					self.trygetparams = 1;
					self.show(showcontrols);
				});
				return
			}
		
			self.build();
			this.element.hide();
			this.w.show();
			if (showcontrols) {
				this.controls.show();
			}

		},
	
		hide: function() {
			if (!this.built) {
				return
			}
			this.controls.hide();
			this.w.hide();
			this.element.show();
		},
		
		getrecid: function() {
			return this.options.recid
		},
	
		getval: function() {
			
			var ret = this.editw.val();

			if (ret == "" || ret == []) {
				return null;
			}

			if (this.editw_units) {
				ret = ret + this.editw_units.val();
			}

			return ret
		},
		
		getparam: function() {
			return this.options.param
		},

		save: function() {
			var self = this;
			$.jsonRPC("putrecordvalue", [this.options.recid, this.options.param, this.getval()], function(rec) {
				record_update(rec);
				self.hide();
			});

		},	
				
		destroy: function() {			
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);







(function($) {
    $.widget("ui.ListControl", {
		options: {
			values: [],
			param: null
		},
				
		_create: function() {
			this.items = $('<ul></ul>');
			this.element.append(this.items);
			this.build();
		},
	
		build: function() {
			var self = this;

			if (this.options.values.length == 0) {
				this.options.values = [""];
			}
			this.items.empty();

			$.each(this.options.values, function(k,v) {
				var item = $('<li></li>');
				var edit = $('<input type="text" value="'+v+'" />');
						
				// if (self.paramdef["vartype"]=="userlist") {
				// 
				// 	// autocomplete
				// 
				// } else if (self.paramdef["vartype"]=="stringlist") {
				//  // autocomplete
				//  
				// }
			
				var add=$('<span><img src="'+EMEN2WEBROOT+'/images/add_small.png" class="listcontrol_add" /></span>').click(function() {
					self.addoption(k+1);
					self.build();
				});
			
				var remove=$('<span><img src="'+EMEN2WEBROOT+'/images/remove_small.png" class="listcontrol_remove" /></span>').click(function() {
					self.removeoption(k);
					self.build();
				});

				item.append(edit,add,remove);
				self.items.append(item);
			});
		},

		addoption: function(pos) {
			// add another option to list
			// save current state so rebuilding does not erase changes
			this.options.values = this.val_withblank();
			this.options.values.splice(pos,0,"");
		},
	
		removeoption: function(pos) {
			// remove an option from the list
			this.options.values = this.val_withblank();
			this.options.values.splice(pos,1);
		},
	
		getval: function() {
			// return the values
			var ret=[];
			$("input:text",this.element).each(function(){
				if (this.value != "") ret.push(this.value);
			});
			return ret
		},
	
		val_withblank: function() {
			var ret=[];
			$("input:text",this.element).each(function(){
				ret.push(this.value);
			});
			return ret		
		},
				
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
	
})(jQuery);

















(function($) {
    $.widget("ui.NewRecordSelect", {
		options: {
			open: 0,
			recid: null,
			rectype: null,
			modal: false
		},
				
		_create: function() {
			this.typicalchld = [];
			this.built = 0;
			var self=this;
			this.element.click(function(e) {
				self.event_click(e);
			});
			if (this.options.open) {
				this.event_click();
			}
		},
		
		event_click: function(e) {
			this.show();
		},
	
		build: function() {
			if (this.built) {
				return
			}
			this.built = 1;
			this.dialog = $('<div title="New Record" />');

			this.typicalchld = $('<div>Loading</div>')
			this.dialog.append('<h4>Suggested Protocols</h4>', this.typicalchld);
			
			this.others = $('<div>Loading</div>')
			this.dialog.append('<br /><br /><h4>Other Protocols</h4>', this.others);
			

			var pos = this.element.offset();
			this.dialog.dialog({
				width: 300,
				height: 400,
				position: [pos.left, pos.top+this.element.outerHeight()],
				autoOpen: true
			});
			
		},
		
		build_typicalchld: function() {
			this.typicalchld.empty();
			var self = this;
			var t = caches["recorddefs"][this.rectype].typicalchld;
			t.sort();
			$.each(t, function() {
				try {
					self.typicalchld.append('<div><a href="'+EMEN2WEBROOT+'/db/record/'+self.options.recid+'/new/'+this+'/">'+caches["recorddefs"][this].desc_short+' ('+this+')</a></div>');
				} catch(e) {
					//self.dialog.append('<div><a href="/db/record/'+self.options.recid+'/new/'+this+'/">('+this+')</a></div>');
				}
			});			
		},
		
		build_others: function() {
			this.others.empty();
			var self = this;
			var s = $('<select />');
			s.append('<option>');
			$.each(caches["recorddefnames"], function() {
				s.append('<option value="'+this+'">'+this+'</option>');
			});
			var b = $('<input type="button" value="New record" />');
			b.click(function() {
				var b = s.val();
				if (!b) {return}
				var ns = EMEN2WEBROOT+'/db/record/'+self.options.recid+'/new/'+b+'/';
				console.log(ns);
				notify_post(ns,[]);
			});
			this.others.append(s, b);
			
		},
		
		show: function() {
			this.build();
			this.dialog.dialog('open');
			var self = this;
			$.jsonRPC("getrecorddef", [this.options.recid], function(rd) {
				self.rectype = rd.name;
				caches["recorddefs"][rd.name] = rd;
				// console.log();

				$.jsonRPC("getrecorddef", [rd.typicalchld], function(rd2) {
					$.each(rd2, function() {
						caches["recorddefs"][this.name] = this;
					})
					self.build_typicalchld();
				})
				
				$.jsonRPC("getrecorddefnames", [], function(names) {
					names.sort();
					caches["recorddefnames"] = names;
					self.build_others();
				})
				
				
			})

		},
		
		hide: function() {
			this.build();
			this.dialog.dialog('close');
		},
		
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
	
})(jQuery);




