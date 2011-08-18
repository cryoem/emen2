(function($) {
    $.widget("emen2.AttachmentControl", {
		options: {
			name: null,
			edit: 0,
			modal: false,
			embed: false,
			show: false,
			cb: function(self) {}
		},
				
		_create: function() {
			this.bdomap = {};
			this.built = 0;
			this.bdos = {};
		
			var self=this;
			this.element.click(function(e) {self.event_click(e)});

			if (this.options.show) {			
				this.show();
			}
		},
	
		event_click: function(e) {
			this.show();
		},
		
		_findbinary: function() {
			var self = this;
			$.jsonRPC.call("binary.find", {'record':self.options.name}, 
				function(bdos) {						
					if (bdos == null) {bdos=[]}
					if (bdos.length == null) {bdos=[bdos]}
					self.bdos = bdos || {};
					self.makebdomap();
					self._findusernames();
					//self.build_tablearea();
				}
			);
		},
		
		_findusernames: function() {
			var findusers = [];
			var self = this;
			$.each(self.bdos, function() {
				if (caches['displaynames'][this.creator] == null) {
					findusers.push(this.creator);
				}
			});

			if (findusers.length) {
				$.jsonRPC.call('user.get', [findusers], function(users) {
					$.each(users, function() {
						caches['displaynames'][this.name] = this.displayname;
					});
					self.build_tablearea();
				})
			} else {
				self.build_tablearea();				
			}
			
		},
		
		event_build_tablearea: function(e) {
			var self = this;
			this.tablearea.empty();
			this.tablearea.append('<div><img src="'+EMEN2WEBROOT+'/static/images/spinner.gif" alt="Loading" /></div>');
			$.jsonRPC.call("paramdef.find", {'record':this.options.name}, function(paramdefs) {			
				$.each(paramdefs, function() {
					caches["paramdefs"][this.name] = this;
				});
				self._findbinary();
			});

		},
	
		makebdomap: function() {
			// This is to avoid an extra RPC call, and sort BDOs by param name
			this.bdomap = {};
			var rec = caches["recs"][this.options.name];
			var self = this;

			$.each(this.bdos, function(i, bdo) {
				// find bdo in record..
				$.each(rec, function(k,v) {
					if (typeof(v)=="object" && v != null) {
						if ($.inArray(bdo.name, v) > -1) {
							self.bdomap_append(k, bdo);
						}
					} else {
						if (v==bdo.name) {
							self.bdomap_append(k, bdo);
						}
					}
				});
			});			
		},

		bdomap_append: function(param, value) {
			if (this.bdomap[param] == null) {
				this.bdomap[param] = [];
			}
			this.bdomap[param].push(value);
		},
	
		build_tablearea: function() {
			var self=this;
			this.tablearea.empty();
			if (this.bdos.length == 0) {
				this.tablearea.append('<h4>There are currently no attachments.</h4>');
				return
			}
			var bdotable = $('<table cellpadding="0" cellspacing="0" class="shaded" />');
			$.each(this.bdomap, function(k,bdos) {
				var header = $('<thead><tr><th></th><th colspan="2"><strong>'+caches["paramdefs"][k].desc_short+' ('+k+')</strong></th><th>Size</th><th>Uploaded</th><th></th></tr></thead>');
				// if (self.options.edit) {header.prepend('<th><input type="radio" name="param" value="'+k+'" /></th>');}
				bdotable.append(header);
				var tbody = $('<tbody></tbody>');
				$.each(bdos, function(i,v) {
					var row = $('<tr data-param="'+k+'" data-bdo="'+v.name+'"/>');
					if (self.options.edit) {
						row.append('<td><input type="checkbox" name="remove"/></td>');
					}
					row.append('<td><a target="_blank" href="'+EMEN2WEBROOT+'/download/'+v.name+'/'+v.filename+'"><img class="thumbnail" src="'+EMEN2WEBROOT+'/download/'+v.name+'/'+v.filename+'?size=thumb" alt="Thumb" /></a></td>');
					row.append('<td><a target="_blank" href="'+EMEN2WEBROOT+'/download/'+v.name+'/'+v.filename+'">'+v.filename+'</a></td>');
					row.append('<td class="nowrap">'+$.convert_bytes(v.filesize)+'</td>');
					row.append('<td><a href="'+EMEN2WEBROOT+'/user/'+v.creator+'/">'+caches['displaynames'][v.creator]+'</a></td>');
					row.append('<td>'+v.creationtime+'</td>');
					tbody.append(row);
				});
				bdotable.append(tbody);
			});
			
			$('input[name=remove]', bdotable).click(function() {
				var target = $(this).parent().parent();
				var state = $(this).attr('checked');
				if (state) {
					target.addClass('removed');
				} else {
					target.removeClass('removed');
				}
			});
			
			$('input[value=file_binary]', bdotable).attr('checked', 'checked');
			this.tablearea.append(bdotable);
		
		},

		build: function() {
			var self = this;

			if (this.built) {
				return
			}
			this.built = 1;

			this.dialog = $('<div><form method="post" enctype="multipart/form-data" action="'+EMEN2WEBROOT+'/upload/'+this.options.name+'"></form></div>');	
			this.tablearea = $('<div />');
			this.browserarea = $('<div />');
			this.queryarea = $('<div></div>')

			$('form', this.dialog).append(this.tablearea, this.browserarea, this.queryarea);
			this.event_build_tablearea();
			
			var controls = $(' <br /> \
				<div class="controls"> \
					<input type="hidden" name="param" id="e2-file-param" value="file_binary" /> \
					<input type="hidden" name="location" value="'+EMEN2WEBROOT+'/record/'+this.options.name+'#attachments" /> \
					<input style="opacity:0" type="file" name="filedata" /> \
					<span class="clickable label e2-file-target">Regular Attachment</span> \
					</span> \
				</div> \
				<div style="width:100%" class="controls"> \
					<input class="floatleft save" name="remove" type="button" value="Remove Selected Attachments" /> \
					<input class="floatright save" name="save" type="submit" value="Upload Attachment" /> \
					<img class="spinner floatright hide" src="'+EMEN2WEBROOT+'/static/images/spinner.gif" alt="Loading" /> \
				</div>');
			
			// If we have permission to edit, show controls.
			if (this.options.edit) {
				$('form', this.dialog).append(controls);
			}

			// Remove items
			$('input[name=remove]', controls).click(function() {
				self.removebdos();
			});
			
			// Submit the form when this changes.
			$('input[name=filedata]', controls).change(function() {
				if (!$(this).val()) {return}
				$('img.spinner', self.dialog).show();
				$('form', self.dialog).submit();
			});

			// Submit button causes file selection then upload when value changes
			$('input[name=save]', this.dialog).click(function(e) {
				$('input[name=filedata]', self.dialog).click();
				e.preventDefault();
			});			

			// Change the selected param for upload..
			$('.e2-file-target', controls).FindControl({
				keytype: 'paramdef',
				vartype: ['binary', 'binaryimage'],
				minimum: 0,
				cb: function(self, value) {
					$('#e2-file-param').val(value);
					self.element.html(value);
				}
			});

			// Embed or put in a dialog
			if (this.options.embed) {
				this.element.append(this.dialog);
			} else {
				var pos = this.element.offset();
				this.dialog.attr("title", "Attachments");
				this.dialog.dialog({
					autoOpen: false,
					width:850,
					height:650,
					position:[pos.left, pos.top+this.element.outerHeight()],
					modal:this.options.modal
				});
			}

		},
		
		rebuild: function() {
			$("#attachment_count").html("");
		},
		
		show: function() {
			this.build();
			if (!this.options.embed) {this.dialog.dialog('open')}
		},
	
		close: function() {
			if (!this.options.embed) {this.dialog.dialog('close')}
		},
		
		removebdos: function() {
			var self = this;
			var newvalues = {}
			//:not(.removed)
			$('tr[data-param]', this.element).each(function() {
				var t = $(this);
				var param = t.attr('data-param');
				var bdo = t.attr('data-bdo');
				if (!newvalues[param]) {newvalues[param]=[]}
				if (!t.hasClass('removed')) {
					newvalues[param].push(bdo)
				}
			});

			var p = {};
			$.each(newvalues, function(k,v) {
				vt = caches['paramdefs'][k].vartype;
				if (v.length == 0) {
					v=null
				} else if (vt=='binaryimage') {
					v = v[0];
				}
				p[k]=v;
			});
			
			$.jsonRPC.call("record.update", [this.options.name, p],
				function(rec) {
					record_update(rec);
					self.event_build_tablearea();
					self.options.cb(self);
				}
			);			
		}
	});
})(jQuery);
