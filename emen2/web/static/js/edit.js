

// convenience function to bind a jquery autocompleter to an element
function bind_autocomplete(elem, param) {
	
	var pd = caches['paramdefs'][param];
	var vt = pd.vartype;
	
	if (vt == "string" || vt == "stringlist") {
	
		// jquery-ui autocompleter
		elem.autocomplete({
			minLength: 0,
			source: function(request, response) {
				// if (request.term in this._cache) {
				// 	response(this._cache[request.term]);
				// 	return;
				// }
				$.jsonRPC("findvalue", [param, request.term], function(ret) {
					var r = $.map(ret, function(item) {
						return {
							label: item[0] + " (" + item[1] + " records)",
							value: item[0]
						}
					});
					// this._cache[request.term] = r;
					response(r);			
				});
			}
		});
		elem.click(function() {
			$(this).autocomplete('search');
		});

	} else if (vt == "user" || vt == "userlist") {

		elem.FindControl({});
		
	} else if (vt == "datetime") {
		
		elem.datepicker({
			showButtonPanel: true,
			dateFormat: 'yy/mm/dd'
		});
		
	}

}







(function($) {
    $.widget("ui.MultiEditControl", {
		options: {
			show: false,
			recid: null,
			selector: null,
			cb_save: function(self){}
		},
				
		_create: function() {
			this.options.recid = this.options.recid || parseInt(this.element.attr("data-recid"));
			this.built = 0;
			this.bind_edit();
			this.options.selector = this.options.selector || '.editable[data-recid='+this.options.recid+']';
			this.backup = this.element.html();
			if (this.options.show) {
				this.event_click();
			}
		},
		
		bind_edit: function() {
			var self = this;
			this.element.click(function(e){self.event_click(e)});
		},
	
		bind_save: function() {
		},

		event_click: function(e) {
			var self=this;
			var recids = [];
			var recids_toget = $.makeArray($(this.options.selector).map(function(){return $(this).attr("data-recid")}));
			for (var i=0;i < recids_toget.length;i++) {
				if (caches['recs'][recids_toget[i]] == null) {
					recids.push(recids_toget[i]);
				}
			}

			var params = [];
			var params_toget = $.makeArray($(this.options.selector).map(function(){return $(this).attr("data-param")}));			
			for (var i=0;i < params_toget.length;i++) {
				if (caches['paramdefs'][params_toget[i]] == null) {
					params.push(params_toget[i]);
				}
			}

			// get records that we can edit
			$.jsonRPC("getrecord", [recids, 1, 1], function(recs) {

				$.each(recs, function(k,v) {
					caches["recs"][v.recid] = v;
				});

				$.jsonRPC("getparamdef", [params], function(paramdefs) {
					$.each(paramdefs, function(k,v) {
						caches["paramdefs"][v.name] = v;
					});
					self.show();
				});

			});

		},

		build: function() {
			var self = this;
			if (this.built) {
				return
			}
			this.built = 1;
			
			this.controls = $('<div class="controls" />')		

			var spinner = $('<img src="'+EMEN2WEBROOT+'/static/images/spinner.gif" class="spinner" alt="Loading" />');
			this.controls.append(spinner);

			var save = $('<input type="submit" name="save" value="Save" />');
			save.click(function(e) {self.save()});
			this.controls.append(save);
			
			if (this.options.recid != "None") {
				var cancel = $('<input type="button" value="Cancel" />').bind("click", function(e) {e.stopPropagation();self.hide()});
				this.controls.append(cancel);
			}			
			this.element.after(this.controls);
		},
		
		rebind_save: function() {
			var self = this;
			var t = $('input[name=save]', this.controls);
			t.val("Retry...");
			t.one(function(e) {self.save()});
		},
	
		show: function() {
			this.build();

			$(this.options.selector).each(function() {
				var t = $(this);
				try {
					t.EditControl({});
					t.EditControl('hide');
					t.EditControl('show', 0);
				} catch(e) {
					//console.log(e);
				}
			});

			this.element.hide();
			this.controls.show();
			this.element.EditbarHelper('show');
		},
	
		hide: function() {
			$(this.options.selector).EditControl('hide');
			this.controls.hide();
			this.element.show();
			this.element.EditbarHelper('hide');			
		},
		
		save: function() {
			var changed = {};
			var self = this;

			$('input[name=save]', this.controls).val('Saving..');

			var comment = $('input[name=editsummary]').val();

			$(this.options.selector).each(function() {
				var t = $(this);
				try {
					var recid = t.EditControl('getrecid');
					var value = t.EditControl('getval');
					var param = t.EditControl('getparam');				
					if (!changed[recid]) {changed[recid]={}}
					changed[recid][param] = value;
					if (comment) {changed[recid]['comments'] = comment}
				} catch(e) {
					//console.log(e);
				}
			});
			
			if (this.options.recid == "None") {
				return this.save_newrecord(changed["None"]);
			}

			$('input[name=save]', this.controls).val('Saving..');
			$('.spinner', this.controls).show();

			$.jsonRPC("putrecordsvalues", [changed], function(recs) {

				$('input[name=save]', self.controls).val('Save');
				$('.spinner', self.controls).hide();

				$.each(recs, function() {
					record_update(this);
				});
				self.hide();
				self.options.cb_save(self);

			}, function(e) {
				
				$('input[name=save]', self.controls).val('Retry');
				$('.spinner', self.controls).hide();
				default_errback(e, function(){})

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
					notify_post(EMEN2WEBROOT+'/record/'+rec.recid+'/', ["New record created"]);
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

			//if ($.inArray(this.options.param, ["recid", "rectype", "comments", "creator", "creationtime", "permissions", "history", "groups"])) {return}

			this.built = 0;
			this.bind_edit();
			this.trygetparams = 0;
			this.element.addClass("editcontrol");
			this.find_cache = {};

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
		
		// This is a BIG NASTY CASE SWITCH to build the input element... Be careful!
		build: function() {
			var self = this;
			this.rec_value = caches["recs"][this.options.recid][this.options.param];
			
			if (this.built){
				return
			}
			this.built = 1;
							
			if (this.rec_value == null) {
				this.rec_value = "";
			}

			// container
			this.w = $('<div class="editcontrol" style="display:inline" />');
			var inline = true;
			var pd = caches["paramdefs"][this.options.param];
			var vt = pd.vartype;
			var autocomplete = true;
					
			
			// Delegate to different edit widgets
			if (vt=="html" || vt=="text") {
			
				inline = false;
				this.editw=$('<textarea class="value" cols="80" rows="20">'+this.rec_value+'</textarea>');
				this.w.append(this.editw);			

			} else if (vt=="choice") {
			
				this.editw=$('<select></select>');
				var pdc = caches["paramdefs"][this.options.param]["choices"];
				pdc.unshift("");
			
				for (var i=0;i<pdc.length;i++) {
					var selected = "";
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
		
			} else if ($.inArray(vt, ["intlist","floatlist","stringlist","userlist","urilist"]) > -1) { //.indexOf(vt) > -1

				inline = false;
				this.editw = $('<div />');
				this.editw.ListControl({values:this.rec_value, param:this.options.param});
				this.w.append(this.editw);
				var autocomplete = false;
				// set a different getval function..
				this.getval = function(){return self.editw.ListControl('getval')}
		
			}  else if (vt=="user") {

				this.editw = $('<input class="value" size="30" type="text" value="'+this.rec_value+'" />');
				this.w.append(this.editw);
		
			} else if (vt=="comments") {

				inline = false;
				this.editw = $('<input class="value" size="30" type="text" value="" />');
						
			} else {

				this.editw = $('<input class="value" size="30" type="text" value="'+this.rec_value+'" />');
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

			// Use this helper function to attach autocompleters
			if (autocomplete) {
				bind_autocomplete(this.editw, this.options.param);
			}

			//console.log(inline);
			if (inline) {
				this.w.css('display','inline');
			}

			this.controls = $('<span class="controls" />')		
			this.controls.append(
				$('<input type="submit" value="Save" name="save" />').one("click", function(e) {self.save()}),
				$('<input type="button" value="Cancel" />').bind("click", function(e) {self.hide()}));
			this.w.append(this.controls);
			this.element.after(this.w);
			
			
		},
	
		show: function(showcontrols) {
			if (showcontrols==null) {showcontrols=1}
			var self = this;

			if (caches['recs'][this.options.recid] == null) {
				$.jsonRPC("getrecord", [this.options.recid], function(rec) {
					caches["recs"][rec.recid] = rec;
					self.show();
				});
				return
			}
			
		
			if (!caches["paramdefs"][this.options.param]) {
				if (this.trygetparams) {return}
				$.jsonRPC("getparamdef", [this.options.param], function(paramdef){
					caches["paramdefs"][paramdef.name]=paramdef;
					self.trygetparams = 1;
					self.show(showcontrols);
				});
				return
			}
		
			this.build();

			this.w.css('display', 'inline');
			if (showcontrols) {
				//this.element.addClass('whitehide');
				//this.w.css('top', this.element.position().top);
				this.element.hide();
				this.w.addClass('inplace');
			} else {
				this.element.hide();
			}
		},
	
		hide: function() {
			if (!this.built) {
				return
			}
			this.w.removeClass('inplace');
			//this.element.removeClass('whitehide');
			this.element.show();
			this.w.hide();			
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

		rebind_save: function() {
			var self = this;
			var t = $('input[name=save]', this.controls);
			t.val("Retry...");
			t.one("click", function() {self.save()});
		},

		save: function() {
			var self = this;
			$.jsonRPC("putrecordvalue", [this.options.recid, this.options.param, this.getval()], function(rec) {
				record_update(rec);
				self.hide();
			}, function(e) {
				error_dialog(e.statusText, e.getResponseHeader('X-Error'), this.jsonRPCMethod, this.data);
				self.rebind_save();
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
						
				bind_autocomplete(edit, self.options.param);
			
				var add=$('<span><img src="'+EMEN2WEBROOT+'/static/images/add_small.png" class="listcontrol_add" alt="Add" /></span>').click(function() {
					self.addoption(k+1);
					self.build();
				});
			
				var remove=$('<span><img src="'+EMEN2WEBROOT+'/static/images/remove_small.png" class="listcontrol_remove" alt="Remove" /></span>').click(function() {
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
			show: false,
			recid: null,
			rectype: null,
			modal: false,
			embed: false,
			inheritperms: true,
			copy: false
		},
				
		_create: function() {
			this.typicalchld = [];
			this.built = 0;
			var self=this;
			
			if (!this.options.embed) {
				this.element.click(function(e){self.event_click(e)});
			}
			
			if (this.options.show) {
				this.event_click();
			}
		},
		
		event_click: function(e) {
			this.show();
		},
		
		doit: function(rectype) {		
			// get some options..
			var opts = {};
			if(!$('input[name=inheritperms]', this.dialog).attr("checked")) {
				opts["inheritperms"] = false
			}
			if ($('input[name=copy]', this.dialog).attr("checked")) {
				opts["copy"] = true
			}			
			var link = EMEN2WEBROOT + '/record/'+this.options.recid+'/new/'+rectype+'/';

			// infuriating that there is no object.length
			if (opts['inheritperms']!=null || opts['copy']!=null) {
				link += "?" + $.param(opts);
			}
			window.location = link;

		},
	
		build: function() {
			if (this.built) {
				return
			}
			this.built = 1;
			
			this.dialog = $('<div />');

			this.typicalchld = $('<div>Loading</div>')
			this.dialog.append('<h4>Suggested Protocols</h4>', this.typicalchld);
			
			var inheritperms = $('<br /><h4>Options</h4><div><input type="checkbox" name="inheritperms" value="" /> Inherit Permissions <br /><input type="checkbox" name="copy" /> Copy values from this record</div>');
			
			if (this.options.inheritperms) {
				$("input[name=inheritperms]", inheritperms).attr("checked", "checked");
			}
			if (this.options.copy) {
				$("input[name=copy]", inheritperms).attr("checked", "checked");
			}

			
			this.dialog.append(inheritperms);
			
			this.others = $('<div>Loading</div>')
			this.dialog.append('<br /><h4>Other Protocols</h4>', this.others);

			if (this.options.embed) {
				this.element.append(this.dialog);
				return
			}
			
			var pos = this.element.offset();
			this.dialog.attr("title", "New Record");
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
					//self.typicalchld.append('<div><a href="'+EMEN2WEBROOT+'/record/'+self.options.recid+'/new/'+this+'/">'+caches["recorddefs"][this].desc_short+'</a></div>'); // ('+this+')
					var i = $('<div><span class="clickable" data-rectype="'+this+'">'+caches["recorddefs"][this].desc_short+'</span></div>');
					$('.clickable', i).click(function() {
						self.doit($(this).attr('data-rectype'));
					})
					self.typicalchld.append(i);
				} catch(e) {
					//self.dialog.append('<div><a href="/record/'+self.options.recid+'/new/'+this+'/">('+this+')</a></div>');
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
				self.doit(b);
				// var ns = EMEN2WEBROOT+'/record/'+self.options.recid+'/new/'+b+'/';
				// notify_post(ns,[]);
			});
			this.others.append(s, b);
			
		},
		
		show: function() {
			this.build();

			if (!this.options.embed) {this.dialog.dialog('open')}


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
			if (!this.options.embed) {this.dialog.dialog('close')}
		},
		
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
	
})(jQuery);



