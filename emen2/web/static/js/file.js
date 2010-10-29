(function($) {
    $.widget("ui.popup", {
		options: {
		},
				
		_create: function() {
         this.element.wrap('<div class="profile_form_label clickable" style="position:relative;display:block;vertical-align:middle"></div>')
            .after('<div style="position:absolute;clear:both;height:200px;width:200px;border:black thin solid;background:#888;top:100%;display:none;z-index:100">asd</div>').parent()
            .click(function (e) {$(this).children().last().toggle()});
         this.element.removeClass('profile_form_label');
      },
				
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);






(function($) {
    $.widget("ui.AttachmentViewerControl", {
		options: {
			recid: null,
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
			$.jsonRPC("getparamdef", [[this.options.recid]], function(paramdefs) {
			
				$.each(paramdefs, function() {
					caches["paramdefs"][this.name] = this;
				});
			
				$.jsonRPC("getbinary", [[self.options.recid]], 
					function(bdos) {
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
			var rec = caches["recs"][this.options.recid];
			var self = this;

			$.each(this.bdos, function(i, bdo) {
				// find bdo in record..
				$.each(rec, function(k,v) {
					if (typeof(v)=="object") {
						if ($.inArray(bdo.name, v) > -1) { //v.indexOf(bdo.name) > -1
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
			var bdotable = $('<table class="files" cellpadding="0" cellspacing="0" />');
			$.each(this.bdomap, function(k,bdos) {

				var header = $('<tr><th></th><th colspan="2"><strong>'+caches["paramdefs"][k].desc_short+' ('+k+')</strong></th><th>Size</th><th>Creator</th><th>Created</th></tr>');
				// if (self.options.edit) {header.prepend('<th><input type="radio" name="param" value="'+k+'" /></th>');}
				bdotable.append(header);
				
				$.each(bdos, function(i,v) {
					var row = $('<tr data-param="'+k+'" data-bdo="'+v.name+'"/>');
					if (self.options.edit) {
						row.append('<td><input type="checkbox" name="remove"/></td>');
					}
					row.append('<td><a target="_blank" href="'+EMEN2WEBROOT+'/download/'+v.name+'/'+v.filename+'"><img style="width:64px" class="thumbnail" src="'+EMEN2WEBROOT+'/download/'+v.name+'/'+v.filename+'?size=thumb" alt="" /></a></td>');
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

			this.dialog = $('<div><form method="post" enctype="multipart/form-data" action="'+EMEN2WEBROOT+'/upload/'+this.options.recid+'"></form></div>');	
			this.tablearea = $('<div />');
			this.browserarea = $('<div />');
			this.queryarea = $('<div></div>')

			$('form', this.dialog).append(this.tablearea, this.browserarea, this.queryarea);
			this.event_build_tablearea();

			var controls = $(' \
				<div class="controls"> \
						<input type="hidden" name="location" value="'+EMEN2WEBROOT+'/record/'+this.options.recid+'#showattachments=1" /> \
						<ul class="options nonlist"> \
							<li> \
								<input checked="checked" type="radio" name="param" value="file_binary" id="param_file_binary" /> \
								<label for="param_file_binary">Regular Attachment</label> \
							</li><li> \
								<input type="radio" name="param" value="file_binary_image" id="param_file_binary_image" /> \
								<label for="param_file_binary">Image File (e.g. CCD)</label> \
							</li><li> \
								<input type="radio" name="param" value="" id="param_other" /> \
								<label for="param_other">Other: <input name="param_other" type="text" size="4" /></label> \
							</li> \
						</ul> \
				</div> \
				<div class="controls" style="width:100%"> \
					<div style="float:left"> \
						<input class="save" name="remove" type="button" value="Remove Selected Files" /> \
					</div> \
					<div style="float:right"> \
						<input type="file" name="filedata" style="width:230px" /> \
						<input class="save" name="save" type="submit" value="Add File" /> \
					</div> \
				</div>');
			
			if (this.options.edit) {
				$('form', this.dialog).append(controls);
			}

			$('input[name=remove]', controls).click(function() {
				self.removebdos();
			});

			$('input[name=param_other]', controls).FindControl({
				'mode':'findparamdef',
				'cb': function(self, value) {
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
			$('.files tr[data-param]').each(function() {
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
			
			$.jsonRPC("putrecordvalues", [this.options.recid, p],
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


/////////////////////////////////////
/////////////////////////////////////
/////////////////////////////////////
/////////////////////////////////////

// ian: Deprecated.

(function($) {
    $.widget("ui.FileControl", {
		options: {
			show: 0,
			recid: null,
			vartype: null,
			param: null,
			modal: true,
			cb: function(){}			
		},
				
		_create: function() {
			this.built = 0;
			this.bdos = {};
			this.options.recid = this.options.recid || parseInt(this.element.attr("data-recid"));
			this.options.param = this.options.param || this.element.attr("data-param");
			this.options.vartype = this.options.vartype || this.element.attr("data-vartype");
		
			var self=this;
			$('.label', this.element).click(function(e) {e.stopPropagation();self.event_click(e)});

			if (this.options.show) {			
				this.show();
			}
		},
	

		event_click: function(e) {
			var self = this;
			this.show();
			$.jsonRPC("getrecord", [this.options.recid],
				function(rec) {				
					caches["recs"][rec.recid] = rec;
					self.event_build_tablearea();
				}
			);
		},
	
	
		event_build_tablearea: function(e) {
			var self = this;
			this.tablearea.empty();
			this.tablearea.append('<div>Loading...</div>');
			$.jsonRPC("getbinary", [caches["recs"][this.options.recid][this.options.param]], 
				function(bdos) {
					if (bdos == null) {bdos=[]}
					if (bdos.length == null) {bdos=[bdos]}
					self.bdos = bdos || {};
					self.build_tablearea();
				}
			);
		},
	
	
		event_removebdos: function(e) {
			var self = this;
			var keep = [];
			var q = $("input:checkbox:checked", this.tablearea).length;
			if (q == 0) {return}
			$("input:checkbox:not(:checked)", this.tablearea).each(function(){return keep.push(this.value)});
			if (this.options.vartype == "binaryimage") {
				keep = keep[0];
			}
			var p = {};
			p[this.options.param]=keep
			$.jsonRPC("putrecordvalues", [this.options.recid, p],
				function(rec) {
					record_update(rec);
					self.event_build_tablearea();
					self.options.cb();
				}
			);
			
		},
	
		
		build: function() {
			var self=this;
			this.built = 1;

			this.dialog = $('<div title="Attachment Manager" />');	
			this.tablearea = $('<div />');
			this.browserarea = $('<div />');
		
			this.dialog.append(this.tablearea, this.browserarea);
		
			this.build_browser();
			this.event_build_tablearea();

			this.dialog.dialog({
				autoOpen: false,
				width:800,
				height:600,
				modal:this.options.modal
			});

		},
	
	
		build_tablearea: function() {
			// build a column-style browser
			this.tablearea.empty();
			var self=this;

			var test = 0;
			for (i in this.bdos) {test++}
			if (test == 0) {
				this.tablearea.append('<p>No attachments</p>');
				return
			}
		
			var bdotable = $('<table class="files" />');
			bdotable.append('<tr><th style="width:20px"><input type="checkbox" name="toggleall" /></th><th>Filename</th><th>Size</th><th>Creator</th><th>Created</th></tr>'); //<th>md5</th>

			$.each(this.bdos, function(k,v) {
				var row = $('<tr/>');
				var remove = $('<td><input type="checkbox" name="remove" value="'+v.name+'" /></td>');
				row.append(remove);
				var link = $('<td><a target="_blank" href="'+EMEN2WEBROOT+'/download/'+v.name+'/'+v.filename+'"><img class="thumbnail" src="'+EMEN2WEBROOT+'/download/'+v.name+'/'+v.filename+'?size=thumb" alt="" />'+v.filename+'</a></td>');
				row.append(link);
				row.append('<td>'+v.filesize+'</td>');
				row.append('<td>'+v.creator+'</td>');
				row.append('<td>'+v.creationtime+'</td>');
				//row.append('<td>'+v.md5+'</td>');
				bdotable.append(row);
			});	
		
			this.tablearea.append(bdotable);
		
			$("input:checkbox[name=toggleall]", this.dialog).click(function(e){e.stopPropagation();self.event_toggleall(e)})

			var reset = $('<p><input class="save" type="button" value="Remove Selected Items" /></p>');
			reset.click(function(e){e.stopPropagation();self.event_removebdos(e)});
			this.tablearea.append(reset);		

		},
	
		build_browser: function() {
			var self = this;
			var fform = $('<form method="post" enctype="multipart/form-data" action="'+EMEN2WEBROOT+'/upload/'+self.options.recid+'?param='+self.options.param+'">');

			this.button_browser = $('<input type="file" name="filedata" />');
			this.button_submit = $('<input class="save" type="submit" value="Upload" />');


			//if (typeof(FileReader) != "undefined") {
			if (false) {
				if (this.options.vartype == "binary") {
					this.button_browser.attr("multiple","multiple");
				}	

				this.button_browser.html5_upload({
					onFinish: function(event, total) {
						$('#progress').progressbar("destroy");
						$.jsonRPC("getrecord", [self.options.recid], function(rec) {
							record_update(rec);
							self.event_build_tablearea();
							self.options.cb();		
						})
					},
					setProgress: function(val) {
						$('#progress').progressbar( "option", "value", val*100 );
					},
					url: function() {
						return EMEN2WEBROOT+'/upload/'+self.options.recid+'?param='+self.options.param;				
					},
					onStart: function(event, total) {
						if (total > 1) {
							return confirm("You are trying to upload " + total + " files. Are you sure?");
						}
						$('#progress').progressbar({});				
						return true;
					},
					autostart: false
				});
				this.button_submit.bind('click', function(e){e.stopPropagation();self.button_browser.trigger('html5_upload.start')});
			}
			
			var progress = $('<div style="float:left;width:200px;margin:10px;" id="progress" />');
			var location = $('<input type="hidden" value="'+EMEN2WEBROOT+'/record/'+this.options.recid+'/" name="Location">');
			
			fform.append(this.button_browser, this.button_submit, progress, location);
			fform.wrap('<div class="controls"></div>');
			this.browserarea.append(fform);

			//if (this.options.vartype == "binary") {
			//	this.browserarea.append('(you can select multiple files)');
			//}


		},
	
		event_toggleall: function(e) {
			var c = $(e.target).attr("checked");
			$("input:checkbox", this.dialog).each(function(){$(this).attr("checked",c)});
		},
	
		show: function() {
			this.build();
			this.dialog.dialog('open');
		},
	
		close: function() {
			this.dialog.dialog('close');
		},		
				
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);
