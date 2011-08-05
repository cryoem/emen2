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
				$.jsonRPC.call("findvalue", [param, request.term], function(ret) {
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
			name: null,
			selector: null,
			reload: false,
			newrecordpage: false,
			cb_save: function(recs){}
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
			$.jsonRPC.call("getrecord", [names], function(recs) {

				$.each(recs, function(k,v) {
					caches["recs"][v.name] = v;
				});

				$.jsonRPC.call("getparamdef", [params], function(paramdefs) {
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

			var spinner = $('<img src="'+EMEN2WEBROOT+'/static/images/spinner.gif" class="spinner hide" alt="Loading" />');
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
			
			//if (this.options.name == "None") {
			//	return this.save_newrecord(changed["None"]);
			//}

			$('input[name=save]', this.controls).val('Saving..');
			$('.spinner', this.controls).show();

			// process changed
			var updated = [];
			$.each(changed, function(k,v) {
				if (k == 'None') {
					v = self.applynew(v);
				}
				v['name'] = k;
				updated.push(v);
			});

			$.jsonRPC.call("putrecord", [updated], function(recs) {
				if (self.options.reload) {
					window.location = window.location
					return
				} else if (self.options.newrecordpage) {
					window.location = EMEN2WEBROOT + '/record/' + recs[0].name + '/';
					return
				}
				$('.spinner', self.controls).hide();
				$('input[name=save]', self.controls).val('Save');
				$.each(recs, function() {
					record_update(this);
				});
				self.hide();
				self.options.cb_save(recs);
			}, function(e) {
				$('input[name=save]', self.controls).val('Retry');
				$('.spinner', self.controls).hide();
				default_errback(e, function(){})
			});
		},

		applynew: function(newrec) {
			var rec = caches['recs']['None'];
			var newrec2 = {};
			$.each(rec, function(k,v) {newrec2[k] = v});
			$.each(newrec, function(k,v) {newrec2[k] = v});

			if ($('#newrecord_permissions').length) {
				newrec2['permissions'] = $('#newrecord_permissions').PermissionControl('getusers');
			}
			if ($('#newrecord_permissions').length) {
				newrec2['groups'] = $('#newrecord_permissions').PermissionControl('getgroups');
			}
			return newrec2
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
			this.w = $('<div class="e2-layout-edit"/>');
			var inline = true;
			var pd = caches["paramdefs"][this.options.param];
			var vt = pd.vartype;
			var autocomplete = true;
					
			
			// Delegate to different edit widgets
			if (vt=="html" || vt=="text") {

				inline = false;
				this.editw=$('<textarea cols="80" rows="10">'+this.rec_value+'</textarea>');
				this.w.append(this.editw);	
				this.w.addClass('e2-layout-fw');

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
		
				this.editw = $('<input size="18" type="text" value="'+this.rec_value+'" />');
				this.w.append(this.editw);

			} else if (vt=="boolean") {
				this.editw = $('<select><option selected="selected"></option><option>True</option><option>False</option></select>');
				if (this.rec_value === true) {
					this.editw.val("True");
				} else if (this.rec_value === false) {
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

				this.editw = $('<input size="20" type="text" value="'+this.rec_value+'" />');
				this.w.append(this.editw);
		
			} else if (vt=="comments") {

				inline = false;
				this.editw = $('<input size="20" type="text" value="" />');
						
			} else {

				this.editw = $('<input size="20" type="text" value="'+this.rec_value+'" />');
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

			// if (inline) {
			// 	this.w.css('display','inline');
			// }

			// this.controls = $('<span class="controls" />')		
			// this.controls.append(
			// 	$('<input type="submit" value="Save" name="save" />').one("click", function(e) {self.save()}),
			// 	$('<input type="button" value="Cancel" name="cancel" />').bind("click", function(e) {self.hide()}));
			// this.w.append(this.controls);
			this.element.after(this.w);
			
			
		},
	
		show: function(showcontrols) {
			if (showcontrols==null) {showcontrols=1}
			var self = this;

			if (caches['recs'][this.options.name] == null) {
				$.jsonRPC.call("getrecord", [this.options.name], function(rec) {
					caches["recs"][rec.name] = rec;
					self.show();
				});
				return
			}
			
		
			if (!caches["paramdefs"][this.options.param]) {
				if (this.trygetparams) {return}
				$.jsonRPC.call("getparamdef", [this.options.param], function(paramdef){
					caches["paramdefs"][paramdef.name]=paramdef;
					self.trygetparams = 1;
					self.show(showcontrols);
				});
				return
			}
		
			this.build();
			this.element.hide();
			this.w.show();
			
			// this.w.css('display', 'inline');
			// if (showcontrols) {
			// 	this.element.hide();
			// 	this.w.addClass('inplace');
			// } else {
			// 	this.element.hide();
			// }
		},
	
		hide: function() {
			if (!this.built) {
				return
			}
			this.w.hide();
			this.element.show();
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
			// var t = $('input[name=save]', this.controls);
			// t.val("Retry...");
			// t.one("click", function() {self.save()});
		},

		save: function() {
			var self = this;
			var p = {}
			p[this.options.param] = this.getval();
			$.jsonRPC.call("putrecordvalues", [this.options.name, p], function(rec) {
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
			this.build();
		},	
	
		build: function() {
			var self = this;
			this.items = $('<ul></ul>');
			this.element.append(this.items);
			if (this.options.values == null || this.options.values.length == 0) {
				this.options.values = [""];
			}
			console.log(this.options.values);
			this.items.empty();
			var pd = caches['paramdefs'][self.options.param];
			var vt = pd.vartype;
			if (vt == 'choicelist') {
				self.build_choicelist();
			} else {
				self.build_stringlist();
			}
		},
		
		build_choicelist: function() {
			var self = this;
			var pd = caches['paramdefs'][self.options.param];
			var vt = pd.vartype;
			$.each(pd.choices, function(count,value) {
				// console.log(k,v);
				var id = 'e2-edit-choicelist-'+self.options.param+'-'+count;
				var item = $('<li><input type="checkbox" id="'+id+'" value="'+value+'"/><label for="">'+value+'</label>');
				if ($.inArray(value, self.options.values) > -1) {
					$('input:checkbox', item).attr('checked', 'checked');
				}
				self.items.append(item);
			})
		},

		build_stringlist: function() {
			var self = this;
			var pd = caches['paramdefs'][self.options.param];
			var vt = pd.vartype;
			$.each(this.options.values, function(k,v) {
				var item = $('<li></li>');				
				var edit = $('<input type="text" value="'+v+'" />');
				bind_autocomplete(edit, self.options.param);
									
				var add=$('<span><img src="'+EMEN2WEBROOT+'/static/images/add_small.png" alt="Add" /></span>').click(function() {
					self.addoption(k+1);
					self.build();
				});
			
				var remove=$('<span><img src="'+EMEN2WEBROOT+'/static/images/remove_small.png" alt="Remove" /></span>').click(function() {
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
			$("input:text, input:checkbox:checked, select",this.element).each(function(){
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
    $.widget("ui.NewRecord", {
		options: {
			// go to new record page instead of popup
			newrecordpage: true,						
			// show selector, show newrecord
			embedselector: true,
			showselector: false,
			show: false,
			embed: false,
			// new record options
			rectype: null,
			parent: null,
			private: false,
			copy: false,
			// callbacks
			cb_save: function(recs) {
				window.location = EMEN2WEBROOT + '/record/' + recs[0].name;
			},
			cb_reload: function(recs) {
				window.location = window.location;
			}
			
		},
				
		_create: function() {
			this.typicalchld = [];
			this.built = 0;			
			this.built_selector = false;
			this.options.rectype = this.element.attr('data-rectype') || this.options.rectype;
			this.options.parent = this.element.attr('data-parent') || this.options.parent;
			this.options.private = this.element.attr('data-private') || this.options.private;
			this.options.copy = this.element.attr('data-copy') || this.options.copy;
			this.options.embed = this.element.attr('data-embed') || this.options.embed;			
			
			var self=this;
			if (!this.options.embed) {
				this.element.click(function(e){self.event_click(e)});
			}			
			if (this.options.show || this.options.showselector) {
				this.show();
			}
		},
		
		event_click: function(e) {
			this.show();
		},
		
		show: function() {
			if (this.options.showselector) {
				this.build_selector();
			} else {
				if (this.options.newrecordpage) {
					this.action();
				} else {
					this.build_newrecord();
				}
			}	
		},
		
		action: function() {
			var self = this;
			if (this.options.newrecordpage) {
				var link = EMEN2WEBROOT + '/record/'+this.options.parent+'/new/'+this.options.rectype+'/';
				if (this.options.copy && this.options.private) {
					link = link + '?private=1&amp;copy=1';
				} else if (this.options.copy) {
					link = link + '?copy=1';
				} else if (this.options.private) {
					link = link + '?private=1';
				}
				window.location = link;
			} else {
				this.build_newrecord();
			}
		},
		
		build_selector: function() {
			var self = this;
			if (this.built_selector) {
				return
			}
			this.built_selector = true;
			this.selectdialog = $('<div />');
			this.typicalchld = $('<div><img src="'+EMEN2WEBROOT+'/static/images/spinner.gif" alt="Loading" /></div>')
			this.selectdialog.append('<h4>New Record</h4>', this.typicalchld);

			// new record rectype
			var o = $('<div><input type="radio" name="newrecordselect" data-other="1" id="newrecordselectother" /> <label for="newrecordselectother">Other:</label></div>')
			var s = $('<input type="text" name="newrecordselectother" value="" size="8" />');
			s.FindControl({'keytype':'recorddef'});
			s.click(function() {
				$("#newrecordselectother").attr('checked', 'checked');
			});
			o.append(s);
			this.selectdialog.append(o);

			// options
			ob = $('<div class="controls"><ul class="nonlist"> \
				<li><input type="checkbox" name="private" id="private" /> <label for="private">Private</label></li> \
				<li><input type="checkbox" name="copy" id="copy" /> <label for="private">Copy values</label></li>  \
				</ul></div>');
				
			if (this.options.private) {
				$("input[name=private]", ob).attr("checked", "checked");
			}
			if (this.options.copy) {
				$("input[name=copy]", ob).attr("checked", "checked");
			}

			$('input[name=private]', ob).click(function() {
				var value = $(this).attr('checked');
				self.options.private = value;
			});
			$('input[name=copy]', ob).click(function() {
				var value = $(this).attr('checked');
				self.options.copy = value;
			});

			// action button
			var b = $('<input type="button" value="New record" />');			
			b.click(function() {
				var b = $('input[name=newrecordselect]:checked', this.selectdialog);
				if (b.attr('data-other')) {
					b = $('input[name=newrecordselectother]').val();
				} else {
					b = b.val();
				}
				if (!b) {return}
				self.options.rectype = b;
				self.action();
			});
			ob.append(b);			
			this.selectdialog.append(ob);

			// embed or popup selector dialog
			if (this.options.embedselector) {
				this.element.append(this.selectdialog);
			} else {			
				var pos = this.element.offset();
				this.selectdialog.attr("title", "New Record");
				this.selectdialog.dialog({
					position: [pos.left, pos.top+this.element.outerHeight()],
					autoOpen: true
				});
			}
			
			// run a request to get the recorddef display names
			$.jsonRPC.call("findrecorddef", {'record':[this.options.parent]}, function(rd) {
				var typicalchld = [];
				$.each(rd, function() {
					self.rectype = this.name;
					caches["recorddefs"][this.name] = this;
					typicalchld = this.typicalchld;					
				});
				$.jsonRPC.call("getrecorddef", [typicalchld], function(rd2) {
					$.each(rd2, function() {
						caches["recorddefs"][this.name] = this;
					})
					self.build_typicalchld();
				})
			});
		},
		
		build_typicalchld: function() {
			// callback for setting list of typical children
			this.typicalchld.empty();
			var self = this;
			var t = caches["recorddefs"][this.rectype].typicalchld;
			$.each(t, function() {
				try {
					var i = $('<div><input type="radio" name="newrecordselect" value="'+this+'" id="newrecordselect_'+this+'"  /> <label class="clickable" for="newrecordselect_'+this+'">'+caches["recorddefs"][this].desc_short+'</label></div>');
					self.typicalchld.append(i);
				} catch(e) {
					//self.dialog.append('<div><a href="/record/'+self.options.name+'/new/'+this+'/">('+this+')</a></div>');
				}
			});
			var a = $('input[name=newrecordselect]:first', this.typicalchld).attr('checked', 'checked');
		},
		
		build_newrecord: function() {
			var self = this;
			this.newdialog = $('<div><img src="'+EMEN2WEBROOT+'/static/images/spinner.gif" alt="Loading" /></div>');
			$.jsonRPC.call("newrecord", [this.options.rectype, this.options.parent], function(rec) {	
				rec.name = 'None';
				caches['recs'][rec.name] = rec;
					
				$.jsonRPC.call("renderview", [rec, null, 'defaultview', true], function(data) {
					self.newdialog.empty();

					var content = $('<div></div>');
					content.append(data);
					self.newdialog.append(content);
					$('.editable', content).EditControl({
						name:'None'
					});

					var controls = $('<div></div>');
					self.newdialog.append(controls);
					controls.MultiEditControl({
						name: 'None',
						show: true,
						cb_save: function(recs){
							self.newdialog.dialog('close');
							self.options.cb_save(recs);
						}
					});

				});
			});
					
			this.element.append(this.newdialog);
			this.newdialog.attr("title", "New "+this.options.rectype+", child of "+caches['recnames'][this.options.parent]);

			// popup or embed
			if (!this.options.embed) {
				this.newdialog.dialog({
					width: 800,
					height: $(window).height()*0.8,
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

