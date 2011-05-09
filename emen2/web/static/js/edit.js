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
    $.widget("ui.NewRecord", {
		options: {
			rectype: null,
			parent: null,
			private: null,
			embed: false
		},
				
		_create: function() {
			var self = this;
			this.options.rectype = this.element.attr('data-rectype') || this.options.rectype;
			this.options.parent = this.element.attr('data-parent') || this.options.parent;
			this.options.private = this.element.attr('data-private') || this.options.private;
			this.options.embed = this.element.attr('data-embed') || this.options.embed;			
			//this.element.click(function(){self.build()});
			this.build();
		},
				
		build: function() {
			var self = this;
			this.dialog = $('<div>Loading...</div>');

			var name = 'None'
			var rec = {'rectype':this.options.rectype, 'name_first':'Ian'}
			caches["recs"][name] = rec;
			
			$.jsonRPC("renderview", [rec, null, 'defaultview', true], function(data) {
				self.dialog.empty();

				var content = $('<div></div>');
				content.append(data);
				self.dialog.append(content);

				var controls = $('<div><input id="newrecord_save" class="controls save" value="Save" /></div>');
				self.dialog.append(controls);
				
				$('.editable', content).EditControl({
					name:'None'
				});
				$('#newrecord_save', controls).MultiEditControl({
					name:'None',
					show:true
				});
				
			});

					
			this.element.append(this.dialog);
			this.dialog.attr("title", "New Record");			
			if (!this.options.embed) {
				this.dialog.dialog({
					width: 800,
					height: 800,
					modal: true,
					autoOpen: true
				});
			}
		},	
				
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);






(function($) {
    $.widget("ui.MultiEditControl", {
		options: {
			show: false,
			name: null,
			selector: null,
			cb_save: function(self){}
		},
				
		_create: function() {
			this.options.name = this.options.name || parseInt(this.element.attr("data-name"));
			this.built = 0;
			this.bind_edit();
			this.options.selector = this.options.selector || '.editable[data-name='+this.options.name+']';
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
			var names = [];
			var names_toget = $.makeArray($(this.options.selector).map(function(){return $(this).attr("data-name")}));
			for (var i=0;i < names_toget.length;i++) {
				if (caches['recs'][names_toget[i]] == null) {
					names.push(names_toget[i]);
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
			$.jsonRPC("getrecord", [names], function(recs) {

				$.each(recs, function(k,v) {
					caches["recs"][v.name] = v;
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

			var save = $('<input class="save" type="submit" name="save" value="Save" />');
			save.click(function(e) {self.save()});
			this.controls.append(save);
			
			if (this.options.name != "None") {
				var cancel = $('<input class="cancel" type="button" value="Cancel" />').bind("click", function(e) {e.stopPropagation();self.hide()});
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
				//try {
				t.EditControl({});
				t.EditControl('hide');
				t.EditControl('show', 0);
				// } catch(e) {
				// }
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
					var name = t.EditControl('getname');
					var value = t.EditControl('getval');
					var param = t.EditControl('getparam');				
					if (!changed[name]) {changed[name]={}}
					changed[name][param] = value;
					if (comment) {changed[name]['comments'] = comment}
				} catch(e) {
				}
			});
			
			if (this.options.name == "None") {
				return this.save_newrecord(changed["None"]);
			}

			$('input[name=save]', this.controls).val('Saving..');
			$('.spinner', this.controls).show();

			// process changed
			var updated = [];
			$.each(changed, function(k,v) {
				v['name'] = k;
				updated.push(v);
			})

			$.jsonRPC("putrecord", [updated], function(recs) {

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
			if (!newrec) {
				newrec = {};
			}
			$.each(newrec, function(k,v) {
				updrec[k] = v;
			});

			
			if ($('#newrecord_permissions').length) {
				//console.log("Applying users");
				updrec['permissions'] = $('#newrecord_permissions').PermissionControl('getusers');
			}
			if ($('#newrecord_permissions').length) {
				//console.log("Applying groups");
				updrec['groups'] = $('#newrecord_permissions').PermissionControl('getgroups');
			}

			$.jsonRPC("putrecord", [updrec], 
				function(rec) {
					notify_post(EMEN2WEBROOT+'/record/'+rec.name+'/', ["New record created"]);
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
			name: null,
			param: null
		},
				
		_create: function() {			
			this.options.param = this.options.param || this.element.attr("data-param");
			this.options.name = this.options.name || parseInt(this.element.attr("data-name"));
			if (isNaN(this.options.name)) this.options.name = "None";

			//if ($.inArray(this.options.param, ["name", "rectype", "comments", "creator", "creationtime", "permissions", "history", "groups"])) {return}

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
			this.rec_value = caches["recs"][this.options.name][this.options.param];
			
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
				this.editw=$('<textarea class="value" cols="80" rows="10">'+this.rec_value+'</textarea>');
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
		
				this.editw = $("<select><option></option><option>True</option><option>False</option></select>");
				if (this.rec_value == true) {
					this.editw.val("True");
				} else if (this.rec_value == false) {
					this.editw.val("False");
				}
				this.w.append(this.editw);				
		
			} else if ($.inArray(vt, ["intlist","floatlist","stringlist","userlist","urilist","choicelist"]) > -1) { //.indexOf(vt) > -1

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

			if (inline) {
				this.w.css('display','inline');
			}

			this.controls = $('<span class="controls" />')		
			this.controls.append(
				$('<input class="save" type="submit" value="Save" name="save" />').one("click", function(e) {self.save()}),
				$('<input class="cancel" type="button" value="Cancel" />').bind("click", function(e) {self.hide()}));
			this.w.append(this.controls);
			this.element.after(this.w);
			
			
		},
	
		show: function(showcontrols) {
			if (showcontrols==null) {showcontrols=1}
			var self = this;

			if (caches['recs'][this.options.name] == null) {
				$.jsonRPC("getrecord", [this.options.name], function(rec) {
					caches["recs"][rec.name] = rec;
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
		
		getname: function() {
			return this.options.name
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
			var p = {}
			p[this.options.param]=this.getval();
			$.jsonRPC("putrecordvalues", [this.options.name, p], function(rec) {
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

			var pd = caches['paramdefs'][self.options.param];
			var vt = pd.vartype;


			$.each(this.options.values, function(k,v) {
				var item = $('<li></li>');
				
				if (vt == "choicelist") {
					var edit = $('<select>');
					
					for (var i=0;i<pd.choices.length;i++) {
						edit.append('<option>'+pd.choices[i]+'</option>');
					}
					
				} else {					
					var edit = $('<input type="text" value="'+v+'" />');
					bind_autocomplete(edit, self.options.param);
				}
									
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
			$("input:text, select",this.element).each(function(){
				if (this.value != "") ret.push(this.value);
			});
			return ret
		},
	
		val_withblank: function() {
			var ret=[];
			$("input:text, select",this.element).each(function(){
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
			name: null,
			rectype: null,
			modal: false,
			embed: false,
			inherit: true,
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
			if($('input[name=private]', this.dialog).attr("checked")) {
				opts["inherit"] = false
			}
			if ($('input[name=copy]', this.dialog).attr("checked")) {
				opts["copy"] = true
			}			
			var link = EMEN2WEBROOT + '/record/'+this.options.name+'/new/'+rectype+'/';

			// infuriating that there is no object.length
			if (opts['inherit']!=null || opts['copy']!=null) {
				link += "?" + $.param(opts);
			}
			window.location = link;

		},
	
		build: function() {
			if (this.built) {
				return
			}
			this.built = 1;
			var self = this;
			
			this.dialog = $('<div />');

			this.typicalchld = $('<div>Loading</div>')
			this.dialog.append('<h4>New Record Protocol</h4>', this.typicalchld);
			
			this.others = $('<div>Loading</div>')
			this.dialog.append(this.others);
			ob = $('<div class="controls"><ul class="options nonlist"> \
				<li><input type="checkbox" name="private" id="private" /> <label for="private">Private</label></li> \
				<li><input type="checkbox" name="copy" id="copy" /> <label for="private">Copy values</label></li>  \
				</ul></div>');
			
			if (!this.options.inherit) {
				$("input[name=private]", ob).attr("checked", "checked");
			}
			if (this.options.copy) {
				$("input[name=copy]", ob).attr("checked", "checked");
			}

			var b = $('<input type="button" value="New record" />');
			
			b.click(function() {
				var b = $('input[name=newrecordselect]:checked', this.dialog);
				if (b.attr('data-other')) {
					b = $('input[name=newrecordselectother]').val();
				} else {
					b = b.val();
				}
				if (!b) {return}
				self.doit(b);
			});
			
			ob.append(b);			
			this.dialog.append(ob);

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
			// ian: leave the typicalchld list unsorted -- higher items might have preference!!
			// t.sort();
			$.each(t, function() {
				try {
					//self.typicalchld.append('<div><a href="'+EMEN2WEBROOT+'/record/'+self.options.name+'/new/'+this+'/">'+caches["recorddefs"][this].desc_short+'</a></div>'); // ('+this+')
					var i = $('<div><input type="radio" name="newrecordselect" value="'+this+'" id="newrecordselect_'+this+'"  /> <label class="clickable" for="newrecordselect_'+this+'">'+caches["recorddefs"][this].desc_short+'</label></div>');
					self.typicalchld.append(i);
				} catch(e) {
					//self.dialog.append('<div><a href="/record/'+self.options.name+'/new/'+this+'/">('+this+')</a></div>');
				}
			});
			var a = $('input[name=newrecordselect]:first', this.typicalchld).attr('checked', 'checked');
		},
		
		build_others: function() {
			this.others.empty();
			var o = $('<div><input type="radio" name="newrecordselect" data-other="1" id="newrecordselectother" /> Other: </div>')
			var self = this;
			var s = $('<input type="text" name="newrecordselectother" value="" style="font-size:10pt" size="8" />');
			s.FindControl({'keytype':'recorddef'});
			s.click(function() {
				$("#newrecordselectother").attr('checked', 'checked');
			});
			o.append(s);
			this.others.append(o);
			
		},
		
		show: function() {
			this.build();

			if (!this.options.embed) {this.dialog.dialog('open')}


			var self = this;
			$.jsonRPC("findrecorddef", {'record':[this.options.name]}, function(rd) {
				var typicalchld = [];
				$.each(rd, function() {
					self.rectype = this.name;
					caches["recorddefs"][this.name] = this;
					typicalchld = this.typicalchld;					
				});
				
				$.jsonRPC("getrecorddef", [typicalchld], function(rd2) {
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

