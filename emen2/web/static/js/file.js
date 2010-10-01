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
			show: false
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
			this.bdomap = {};
			var rec = caches["recs"][this.options.recid];
			var self=this;

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

			var bdotable = $('<table class="files" />');
			bdotable.append('<tr><th>Filename</th><th>Size</th><th>Creator</th><th>Created</th></tr>'); 
			$.each(this.bdomap, function(k,bdos) {

				bdotable.append('<tr><td colspan="4"><h4>'+caches["paramdefs"][k].desc_short+' ('+k+')</h4></td></tr>');
			
				$.each(bdos, function(i,v) {
					var row = $('<tr/>');
					var link = $('<td><a target="_blank" href="'+EMEN2WEBROOT+'/download/'+v.name+'/'+v.filename+'"><img class="thumbnail" src="'+EMEN2WEBROOT+'/download/'+v.name+'/'+v.filename+'?size=thumb" alt="" />'+v.filename+'</a></td>');
					row.append(link);
					row.append('<td>'+v.filesize+'</td>');
					row.append('<td>'+v.creator+'</td>');
					row.append('<td>'+v.creationtime+'</td>');
					bdotable.append(row);
				})

				if (self.options.edit) {
					var h = $('<tr><td colspan="4"><span class="editable label">Edit</span></td></tr>');
					h.FileControl({show: 0, recid:self.options.recid, param:k, cb:function(){self.event_build_tablearea()}});
					bdotable.append(h);
				} else {
					bdotable.append('<tr><td>&nbsp;</td></tr>');
				}

			})
			this.tablearea.append(bdotable);
		
		},


		make_filecontrol: function(param) {
			var i = $('<div />');
			i.FileControl({
				recid: this.options.recid,
				show: 1,
				param: param
			});
		},
		
		build: function() {
			var self=this;

			if (this.built) {
				return
			}
			this.built = 1;

			this.dialog = $('<div></div>');	
			this.tablearea = $('<div />');
			this.browserarea = $('<div />');
			this.queryarea = $('<div></div>')


			var controls = $('<div class="controls" />');

			controls.append('<ul class="nonlist"><li><a href="'+EMEN2WEBROOT+'/query/recid=='+this.options.recid+'/files/">View / Download all in this record</a></li><li><a href="'+EMEN2WEBROOT+'/query/parent.recid.'+this.options.recid+'*/files/">View / Download all files in children</a></li></ul>');

			console.log(this.recid);

			var ss = $('<select data-recid="'+this.options.recid+'"/>');
			ss.append('<option value="" />');

			//$.each(['file_binary','file_binary_image'], function() {
			//	ss.append('<option value="'+this+'">'+this+'</option>');
			//});
			ss.append('<option value="file_binary">Regular Attachment</option>');
			ss.append('<option value="file_binary_image">Image File (e.g. CCD)</option>');

			ss.val("file_binary");

			ssc = $('<input type="button" value="Add File" />');
			ssc.click(function() {
				var v = ss.val();
				if (!v){return}
				self.make_filecontrol(v);
			})
			controls.append(ss, ssc);
			
			this.dialog.append(this.tablearea, this.browserarea, this.queryarea, controls);


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
			
			this.event_build_tablearea();
			

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
			$.jsonRPC("putrecordvalue",
				[this.options.recid, this.options.param, keep],
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

			var reset = $('<p><input type="button" value="Remove Selected Items" /></p>');
			reset.click(function(e){e.stopPropagation();self.event_removebdos(e)});
			this.tablearea.append(reset);		

		},
	
		build_browser: function() {
			var self = this;
			var fform = $('<form method="post" enctype="multipart/form-data" action="'+EMEN2WEBROOT+'/upload/'+self.options.recid+'?param='+self.options.param+'">');

			this.button_browser = $('<input type="file" name="filedata" />');
			this.button_submit = $('<input  type="submit" value="Upload" />');


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
