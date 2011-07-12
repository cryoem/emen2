(function($) {
    $.widget("ui.AttachmentViewerControl", {
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

		event_build_tablearea: function(e) {
			var self = this;
			this.tablearea.empty();
			this.tablearea.append('<div>Loading...</div>');
			$.jsonRPC("findparamdef", {'record':this.options.name}, function(paramdefs) {
			
				$.each(paramdefs, function() {
					caches["paramdefs"][this.name] = this;
				});
			
				$.jsonRPC("findbinary", {'record':self.options.name}, 
					function(bdos) {
                  console.log(bdos);
						if (bdos == null) {bdos=[]}
						if (bdos.length == null) {bdos=[bdos]}
						self.bdos = bdos || {};
						self.makebdomap();
						self.build_tablearea();
					}
				);

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
			var bdotable = $('<table cellpadding="0" cellspacing="0" />');
			$.each(this.bdomap, function(k,bdos) {

				var header = $('<tr><th></th><th colspan="2"><strong>'+caches["paramdefs"][k].desc_short+' ('+k+')</strong></th><th>Size</th><th>Creator</th><th>Created</th></tr>');
				// if (self.options.edit) {header.prepend('<th><input type="radio" name="param" value="'+k+'" /></th>');}
				bdotable.append(header);
				
				$.each(bdos, function(i,v) {
					var row = $('<tr data-param="'+k+'" data-bdo="'+v.name+'"/>');
					if (self.options.edit) {
						row.append('<td><input type="checkbox" name="remove"/></td>');
					}
					row.append('<td><a target="_blank" href="'+EMEN2WEBROOT+'/download/'+v.name+'/'+v.filename+'"><img class="thumbnail" src="'+EMEN2WEBROOT+'/download/'+v.name+'/'+v.filename+'?size=thumb" alt="Thumb" /></a></td>');
					row.append('<td><a target="_blank" href="'+EMEN2WEBROOT+'/download/'+v.name+'/'+v.filename+'">'+v.filename+'</a></td>');
					row.append('<td>'+$.convert_bytes(v.filesize)+'</td>');
					row.append('<td>'+v.creator+'</td>');
					row.append('<td>'+v.creationtime+'</td>');
					bdotable.append(row);
				});
				
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

			var controls = $(' \
				<div class="controls"> \
						<input type="hidden" name="location" value="'+EMEN2WEBROOT+'/record/'+this.options.name+'#showattachments=1" /> \
						<ul class="options nonlist"> \
							<li> \
								<input checked="checked" type="radio" name="param" value="file_binary" id="param_file_binary" /> \
								<label for="param_file_binary">Regular Attachment</label> \
							</li><li> \
								<input type="radio" name="param" value="" id="param_other" /> \
								<label for="param_other">Other: <input name="param_other" type="text" size="4" /></label> \
							</li> \
						</ul> \
						<input type="file" name="filedata" size="6" /><br /> \
				</div> \
				<div style="clear:both;float:none" class="controls"> \
					<input class="floatleft save" name="remove" type="button" value="Remove Selected" /> \
					<input class="floatright save" name="save" type="submit" value="Upload Attachment" /> \
				</div>');
			
			if (this.options.edit) {
				$('form', this.dialog).append(controls);
			}

			$('input[name=remove]', controls).click(function() {
				self.removebdos();
			});

			$('input[name=param_other]', controls).FindControl({
				keytype: 'paramdef',
				vartype: ['binary', 'binaryimage'],
				minimum: 0,
				cb: function(self, value) {
					$('#param_other').attr('value', value);
					self.element.val(value);
				}
			});
			$('input[name=param_other]', controls).click(function() {
				$("#param_other").attr('checked', 'checked');
			});

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
			
			$.jsonRPC("putrecordvalues", [this.options.name, p],
				function(rec) {
					record_update(rec);
					self.event_build_tablearea();
					self.options.cb(self);
				}
			);			
		},		

		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);
