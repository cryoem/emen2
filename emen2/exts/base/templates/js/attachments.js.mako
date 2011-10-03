(function($) {
    $.widget("emen2.AttachmentControl", {
		options: {
			name: null,
			edit: false,
			show: true,
			controls: null
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
			// Find binaries attached to the named record
			var self = this;
			$.jsonRPC.call("binary.find", {'record':self.options.name}, 
				function(bdos) {
					self.bdos = bdos;
					$.updatecache(bdos);

					// Grab all the users we need
					var users = $.map(self.bdos, function(i){return i['creator']});
					users = $.checkcache('user', users);
					if (users.length) {
						$.jsonRPC.call('user.get', [users], function(users) {
							$.updatecache(users);
							self.build();
						});
					} else {
						self.build();
					}
				}
			);
		},		

		build: function() {
			if (this.built) {return}
			this.built = 1;
			
			var self = this;
			var dialog = $('<div></div>');	
			
			// Key the binaries by parameter
			this.bdomap = this.makebdomap(this.bdos);
			
			// Build the items
			$.each(this.bdomap, function(k,v) {
				self.element.append(self.build_level(k,k,v))
			})

			this.element.append(dialog);

			if (this.options.controls) {
				this.build_controls();
			}
		},

		build_level: function(label, level, items) {
			var self = this;
			var pd = caches['paramdef'][level];
			if (pd) {label = pd.desc_short}
			
			var header = $('<h4>'+label+'</h4>');
			var d = $('<div class="e2l-cf e2l-fw"></div>');
			$.each(items, function() {
				var infobox = $('<div />');
				infobox.InfoBox({
					name: this,
					keytype: 'binary',
					selectable: self.options.edit,
					input: ['checkbox',level,true]
				});
				d.append(infobox);
			});
			
			return $('<div>').append(header, d)
		},

		build_controls: function() {
			
			// Controls includes it's own form for uploading files
			var controls = $(' \
				<form id="e2-attachments-upload" method="post" enctype="multipart/form-data" action="'+EMEN2WEBROOT+'/upload/'+this.options.name+'"> \
					<input type="hidden" name="param" id="e2-attachments-param" value="file_binary" /> \
					<input type="hidden" name="location" value="'+EMEN2WEBROOT+'/record/'+this.options.name+'#attachments" /> \
					<ul class="e2l-options"> \
						<li><span class="e2l-a e2l-label e2-attachments-target">Regular Attachment</span></li> \
						<li><input type="file" name="filedata" /></li> \
					</ul> \
					<ul class="e2l-controls"> \
						<li>'+$.e2spinner()+'<input name="save" type="submit" value="Upload Attachment" /></li> \
					</ul> \
				</form>');
				
			// <li><input class="e2l-float-left e2l-save" name="remove" type="button" value="Remove Selected Attachments" /></li> \
			
			// Submit the form when this changes.
			// $('input[name=filedata]', controls).change(function() {
			//	 console.log("Got files:", $(this).val());
			//	 if (!$(this).val()) {return}
			// 	$('#e2-attachments-upload', self.element).submit();
			// });

			// Submit button causes file selection then upload when value changes
			// $('input[name=save]', controls).click(function(e) {
			//	$('input[name=filedata]', self.element).click();
			//	e.preventDefault();
			// });			

			// Change the selected param for upload..
			$('.e2-attachments-target', controls).FindControl({
				keytype: 'paramdef',
				vartype: ['binary'],
				minimum: 0,
				selected: function(self, value) {
					$('#e2-attachments-param').val(value);
					self.element.html(value);
				}
			});
			
			this.options.controls.append(controls);
		},

		// Utility methods --
		makebdomap: function(bdos) {
			// This is to avoid an extra RPC call, and sort BDOs by param name
			var bdomap = {};
			var rec = caches['record'][this.options.name];
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