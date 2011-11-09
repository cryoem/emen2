(function($) {
	
    $.widget("emen2.UploadControl", {
		options: {
			modal: true,
			action: '/upload/',
			location: '/',
			wait: 1000,
			param: 'file_binary',
		},
				
		_create: function() {
			this.built = 0;
			this.files = [];	
			this.build();
			var self = this;
			
			this.options.action = this.element.attr('action');
			var location = $('input[name=location]', this.element);
			if (location.length) {
				this.options.location = location.val();
			}
			
			// Check that we have browser support for File API
			if (window.File && window.FileReader && window.FileList && window.Blob) {
				// Great success! All the File APIs are supported.
			} else {
				// alert('The File APIs are not fully supported in this browser.');
				return
			}

			// If the browser supports it, bind to the form submission event.
			// this.element.submit(function(e) {
			//	self.submit(e);
			// });
		},
		
		submit: function(e) {
			var self = this;
			// e.preventDefault();

			// Clear the table body
			$('.e2-upload-table tbody', this.dialog).empty();
			
			// Show the dialog
			this.dialog.dialog('open');

			// Get the files and parameter name
			var fileinput = $('input:file', this.element);
			var files = fileinput[0].files;
			var param = fileinput.attr('name');
			if (param) {this.options.param = param}

			// Add each file to the table and upload
			$.each(files, function(index, file) {
				self.add(index, file);
			});
			// Start the upload
			this.next(0);
		},
		
		add: function(index, file) {
			// Add to the file queue
			this.files.push([index, file]);
			// Add a row for the file
			var tbody = $('.e2-upload-table tbody', this.dialog);

			var row = $(' \
				<tr data-index="'+index+'"> \
					<td>'+file.name+'</td> \
					<td>'+emen2.template.prettybytes(file.size)+'</td> \
					<td><div class="e2-upload-progress"></div></td> \
					<td style="width:32px" class="e2-upload-action"></td> \
				</tr>');

			tbody.append(row);
		},
		
		next: function(wait) {
			var self = this;
			if (wait == null) {wait = this.options.wait}

			if (!this.files.length) {
				$('input:submit[disabled]', this.dialog).attr('disabled',false);
				return
			}

			var item = this.files.shift();			
			setTimeout(function(){
				self.upload(item[0], item[1]);
			}, wait);
			
		},
		
		retry: function(index, file) {
			console.log("Retry", index, file);
			this.upload(index, file);
		},
		
		upload: function(index, file) {
			// Upload the file blob
			var self = this;
			var elem = $('tr[data-index='+index+'] .e2-upload-progress');
			var action = $('tr[data-index='+index+'] .e2-upload-action');
			elem.empty();
			action.empty();
			
			// Copy the form data; we need to submit it as GET querystring
			// because the request itself will be PUT
			var qs = this.element.serialize();
			var uri = this.options.action + '?' + qs;			

			clr = function(elem, action) {
				elem.empty();
				action.empty();
				elem.progressbar('destroy');
			}
			
			var xhr = new XMLHttpRequest();
			xhr.upload.onprogress = function(e) {
				var prog = Math.round((e.loaded / e.total) * 100);
				elem.progressbar('value', prog);
			}
			xhr.onloadend = function(e) {
				// Always go ahead and try the next item
				self.next()
				if (this.status == 0) {
					return
				}
				clr(elem, action);
				elem.html('Completed');
				action.append(emen2.template.image('ok.png','Success'));
			}
			xhr.onloadstart = function(e) {
				clr(elem, action);
				elem.progressbar({});
				var cancel = $(emen2.template.image('cancel.png','Cancel')).click(function(){xhr.abort()});
				action.append(cancel);				
			}
			xhr.onabort = function(e) {
				clr(elem, action);
				elem.html('Aborted');
				var retry = $(emen2.template.image('retry.png','Retry')).click(function(){self.retry(index, file)});
				action.append(retry);
			}
			xhr.onerror = function(e) {
				clr(elem, action);
				elem.html('Error');
				var retry = $(emen2.template.image('retry.png','Retry')).click(function(){self.retry(index, file)});
				action.append(retry);
			}
			xhr.ontimeout = function(e) {
				clr(elem, action);
				elem.html('Timed out');
				var retry = $(emen2.template.image('retry.png','Retry')).click(function(){self.retry(index, file)});
				action.append(retry);				
			}
			xhr.open('PUT', uri, true);			
			xhr.setRequestHeader('X-File-Name', file.name);
			xhr.setRequestHeader('X-File-Size', file.size);
			xhr.setRequestHeader('X-File-Param', this.options.param);
			xhr.setRequestHeader('Content-Type', file.type);			
			xhr.send(file);

			// var size = file.size;
			// var pos = 0;
			// var chunk = 128;
			// function getslice(file, start, stop) {
			// 	if (file.webkitSlice) {
			// 		var blob = file.webkitSlice(start, stop + 1);
			// 	} else if (file.mozSlice) {
			// 		var blob = file.mozSlice(start, stop + 1);
			// 	}
			// 	return blob;
			// }
			// reader = new FileReader();
			// reader.onloadend = function(e) {
			// 	console.log('reader.onloadend', pos, chunk);
			// 	if (e.target.readyState == FileReader.DONE) {
			// 		xhr.sendAsBinary(e.target.result);
			// 		pos += chunk;
			// 		reader.readAsBinaryString(getslice(file, pos, pos+chunk));
			// 	}
			// }
			// reader.readAsBinaryString(getslice(file, pos, pos+chunk));
		},

		build: function() {
			this.dialog = $('<div></div>');
			this.dialog.attr('title','Upload Progress');
			
			//style="table-layout:fixed" 
			var table = $(' \
				<table cellspacing="0" cellpadding="0" class="e2l-shaded e2-upload-table"> \
					<thead> \
						<tr> \
							<th>Filename</th> \
							<th>Filesize</th> \
							<th>Progress</th> \
							<th></th> \
						</tr> \
					</thead> \
					<tbody> \
					</tbody> \
				</table>');
			
			this.dialog.append(table);
			
			// <li><input type="button" value="Cancel" /></li>
			var ok = $('<form method="post" action="'+this.options.location+'"><ul class="e2l-controls"><li><input type="submit" value="Ok" disabled /></li></ul></form>');
			this.dialog.append(ok);
			
			if (this.options.modal) {
				$('body').append(this.dialog);
				this.dialog.dialog({
					width: 600,
					height: 600,
					autoOpen: false,
					modal: true,
					closeOnEscape: false,
					dialogClass: 'e2-dialog-no-close'
				});
			} else {
				this.element.append(this.dialog);
			}
		}
	});
	
	
    $.widget("emen2.AttachmentControl", {
		options: {
			name: null,
			edit: false,
			show: true,
			controls: null,
			multiple: true,
			// events: saved..
		},
				
		_create: function() {
			this.built = 0;
			this.bdos = [];
			this.bdomap = {};
			if (this.options.show) {			
				this.show();
			}
		},

		show: function() {
			this.build();
		},

		build: function() {
			// Find binaries attached to the named record
			var self = this;
			emen2.db("binary.find", {'record':self.options.name}, 
				function(bdos) {
					self.bdos = bdos;
					emen2.cache.update(bdos);

					// Grab all the users we need
					var users = $.map(self.bdos, function(i){return i['creator']});
					users = emen2.cache.check('user', users);
					if (users.length) {
						emen2.db('user.get', [users], function(users) {
							emen2.cache.update(users);
							self._build();
						});
					} else {
						self._build();
					}
				}
			);			
		},

		_build: function() {
			if (this.built) {return}
			this.built = 1;
			
			var self = this;
			var dialog = $('<div></div>');	
			
			// Key the binaries by parameter
			this.bdomap = this.makebdomap(this.bdos);
			
			// Build the items
			$.each(this.bdomap, function(k,v) {
				self.element.append(self.build_level(k,k,v))
			});

			this.element.append(dialog);

			if (this.options.controls) {
				this.build_controls();
			}
			$('.e2-attachments-infobox').InfoBox('show');

		},

		build_level: function(label, level, items) {
			var self = this;
			var pd = emen2.caches['paramdef'][level];
			if (pd) {label = pd.desc_short}

			// Update the select count when built or checked..
			var cb = function() {$('.e2-select', self.options.controls).SelectControl('update')}
			
			var header = $('<h4>'+label+'</h4>');
			var d = $('<div class="e2l-cf e2l-fw"></div>');
			$.each(items, function() {
				// Like other InfoBoxes, don't show until appended to DOM
				var infobox = $('<div class="e2-attachments-infobox" />').InfoBox({
					show: false,
					name: this,
					keytype: 'binary',
					selectable: self.options.edit,
					input: ['checkbox',level,true],
					built: cb,
					selected: cb
				});
				d.append(infobox);
			});
			
			return $('<div>').append(header, d)
		},

		build_controls: function() {
			var self = this;
			
			// Controls includes it's own form for uploading files
			var controls = $(' \
					<ul class="e2l-options"> \
						<li class="e2-select" /> \
						<li><span class="e2l-a e2l-label e2-attachments-param">Regular Attachment</span></li> \
						<li><input type="file" class="e2-attachments-fileinput" name="file_binary" multiple /></li> \
					</ul> \
					<ul class="e2l-controls"> \
						<li>'+emen2.template.spinner()+'<input type="submit" value="Save attachments" /></li> \
					</ul>');

			// Selection control
			$('.e2-select', controls).SelectControl({root: this.element});
			
			// $('input:submit', controls).click(function(e){self.save(e)});
			
			// Submit the form when this changes.
			$('.e2-attachments-fileinput', controls).change(function(e) {
				self.upload(e);
			});
			
			// Submit button causes file selection then upload when value changes
			// $('input[name=save]', controls).click(function(e) {
			//	$('input[name=filedata]', self.element).click();
			//	e.preventDefault();
			// });	

			// Change the selected param for upload..
			// $('.e2-attachments-param', controls).FindControl({
			// 	keytype: 'paramdef',
			// 	vartype: ['binary'],
			// 	minimum: 0,
			// 	selected: function(self, value) {
			// 		$('#e2-attachments-param').val(value);
			// 		self.element.html(value);
			// 	}
			// });
			
			this.options.controls.append(controls);

			// $('#e2-attachments-upload').UploadControl({});
			// $('#e2-attachments-upload').submit(function(e) {
			// 	e.preventDefault();
			// 	console.log(e);
			// })
			
		},
		
		save: function(e) {
			this.element.submit();
		},
		
		upload: function(e) {
			this.element.UploadControl({});
			this.element.UploadControl('submit');
		},

		// Utility methods --
		makebdomap: function(bdos) {
			// This is to avoid an extra RPC call, and sort BDOs by param name
			var bdomap = {};
			var rec = emen2.caches['record'][this.options.name];
			var self = this;

			$.each(bdos, function(i, bdo) {
				// find bdo in record..
				$.each(rec, function(k,v) {
					if (typeof(v)=="object" && v != null) {
						if ($.inArray(bdo.name, v) > -1) {
							self.bdomap_append(bdomap, k, bdo.name);
						}
					} else {
						if (v==bdo.name) {
							self.bdomap_append(bdomap, k, bdo.name);
						}
					}
				});
			});	
			return bdomap
		},

		bdomap_append: function(bdomap, param, value) {
			if (bdomap[param] == null) {
				bdomap[param] = [];
			}
			bdomap[param].push(value);
		},	
			
	});
})(jQuery);

<%!
public = True
headers = {
	'Content-Type': 'application/javascript',
	'Cache-Control': 'max-age=86400'
}
%>