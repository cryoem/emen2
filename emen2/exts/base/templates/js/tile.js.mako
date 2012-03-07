(function($) {
    $.widget("emen2.BoxerControl", {
		options: {
			name: null,
			bdo: null,
			boxrecords: null,
			boxes: [],
			boxsize: 128,
			show: true,
			colors: ['#000000', '#00FF00', '#0000FF', '#FFFFFF', '#FF0000']
		},
				
		_create: function() {
			this.emdata = {};
			this.currentlabel = -1;			
			this.pen = -1;
			this.boxid = 0;

			this.options.bdo = emen2.util.checkopt(this, 'bdo');
			this.element.attr('data-bdo', this.options.bdo);

			this.options.name = emen2.util.checkopt(this, 'name');
			this.element.attr('data-name', this.options.name);

			if (this.options.show) {
				this.event_click();
			}
		},
		
		build: function() {
			var self = this;
			this.build_controls();
			this.build_map();
			this.build_map_controls();
			
			$(window).resize(function() {self.event_resize()});			

			// if there are records, do some callbacks..
			if (this.options.name != null) {				

				emen2.db("getchildren", [this.options.name, 1, "box"], function(children) {

					emen2.db("getrecord", [children], function(recs) {			
						$.each(recs, function(i) {
							self.load_record(this);
						});					
					});	

					if (children.length==0) {
						self.load_record(null);
					}

				});

			} else {
				// If there are no boxes, start a new set..
				this.build_boxarea();				
			}

		},

		build_map: function() {
			var self = this;						
			// Tile Map Browser
			this.img = $('<div class="e2-tile" />');
			this.element.append(this.img);
			this.event_resize();			
			this.img.TileControl({bdo: this.options.bdo, scale: 'auto', width: this.emdata['nx'], height: this.emdata['ny']});
		},
		
		build_controls: function() {
			var self = this;
	
			// Box areas
			var boxtable = $('<table class="e2-box-table"><thead><tr><th style="width:60px">Visible</th><th style="width:30px">Count</th><th style="width:40px">Size</th><th>Name</th><th>Actions</th></tr></thead><tbody></tbody></table>');
			var controls = $('<div class="e2l-controls" />');
			// controls.resizable({
			// 	handles: 'w',
			// 	minWidth: 450,
			// 	resize: function(e, ui) {self.event_resize()}
			// 	});
			
			controls.append(boxtable);
			this.element.append(controls);			
		},
		
		build_map_controls: function() {
			var self = this;

			var controls = $('.e2-tile[data-bdo='+this.options.bdo+'] .tileTreeControls');
			controls.append('<h4 class="e2l-label">Boxes</h4>\
				<input type="button" name="bigger" value="&laquo;" /> <input name="smaller" type="button" value="&raquo;" /><br /> \
				<input type="button" name="newset" value="New Set" /><br /> \
				'+emen2.template.spinner(false)+' \
				<input type="button" name="saveall" value="Save All" /> \
				');
			controls.find("input[name=bigger]").click(function() {
				self.resize_controls(1);
			});			
			controls.find("input[name=smaller]").click(function() {
				self.resize_controls(-1);
			});
			controls.find("input[name=newset]").click(function() {
				self.load_record();
			});				
			controls.find("input[name=saveall]").click(function() {
				self.saveall();
			});				
		},
					

		event_click: function(e) {
			var self = this;	
			$.ajax({
				type: 'POST',
				url: EMEN2WEBROOT+'/eman2/'+this.options.bdo+'/get_attr_dict',
				dataType: 'json',
				success: function(d) {
					self.emdata = d;
					self.build();
				}
			});
		},
		
		event_resize: function() {
			// going to make an ugly, evil hack..
			var maxh = document.height;
			var pos = this.element.parent().offset();
			this.element.height(parseInt(maxh-pos.top)-22);
			var cw = $('.e2l-controls', this.element);
			var w = cw.width();
			if (cw.css("display") == "none") { w = 0 }
			this.img.width(this.element.width()-w);
			this.img.TileControl('recenter');
		},

		addbox: function(x, y, label) {
			// add a new box at x, y with label			
			label = label || this.pen;
			// get current image scale
			var scale = this.img.TileControl('option', 'scale');

			// increment box counter for id's
			this.boxid += 1;

			// create a new box overlay
			var boxsize = emen2.caches['record'][label]['box_size'];
			
			var boxbox = $('<div>&nbsp;</div>');
			boxbox.BoxBox({bdo: this.options.bdo, x: x, y: y, size: boxsize, boxid: this.boxid, scale: scale, label: label});
			this.img.TileControl('getinner').append(boxbox);

			// create a new box image
			var boximg = $('<img alt="Box" />');
			boximg.BoxImg({bdo: this.options.bdo, x: x, y: y, size: boxsize, boxid: this.boxid, scale: 1, label: label, draggable: true});
			$('.e2-box-area[data-label='+label+']').prepend(boximg);			

			// update box count
			this.updateboxcount(label);
		},
		
		resize_controls: function(size) {
			// make the controls bigger or smaller...
			var cw = $('.e2l-controls', this.element);
			var maxsize = this.element.width()-100;			
			var datawidth = parseInt(cw.attr('data-width'));
			var datamaxsize = parseInt(cw.attr('data-maxsize'));						
			if (size == 1) {
				if (datamaxsize) {

				} else if (cw.css('display') != 'none') {
					cw.attr('data-width', cw.width());
					cw.attr('data-maxsize', '1');
					cw.width(maxsize);
				} else {
					cw.show();
				}
			} else {
				if (cw.css('display') == 'none') {
					
				} else if (datamaxsize) {
					cw.attr('data-maxsize', '0');
					cw.width(datawidth);
				} else {
					cw.hide();
				}
			}		
			this.event_resize();
		},
		
		remove_box: function(boxid) {
			// kill a box dead
			var label = $('.e2-box-img[data-boxid='+boxid+']').attr('data-label');
			$('.e2-box-img[data-boxid='+boxid+']').remove();
			$('.e2-box-box[data-boxid='+boxid+']').remove();
			this.updateboxcount(label);
		},
		
		updateboxcount: function(label) {
			label = label || null;
			var boxcount = $('.e2-box-img[data-label='+label+']').length;
			$('.e2-box-count[data-label='+label+']').html(boxcount);
		},

		unlink_label: function(label, confirm, confirmed) {
			var self = this;
			if (!confirm) {
				var dialog = $('<div title="Remove Box"><p>This will unlink record '+label+' from the parent record.</p><p>It may be orphaned and difficult to find after this action.</p><p>Continue?</p></div>');
				dialog.dialog({
					modal: true,
					buttons: {
						'Remove Box': function() {
							$(this).dialog('close');
							self.unlink_label(label, true);
						},
						Cancel: function() {
							$(this).dialog('close');
						}
					}
				});
				return
			}
			
			if (confirm == true) {
				emen2.db("pcunlink", [this.options.name, label], function() {
					self.remove_label(label);
				});
			}		
		},
		
		remove_label: function(label) {
			$('.e2-box-img[data-label='+label+']').remove();
			$('.e2-box-box[data-label='+label+']').remove();			
			$('tr[data-label='+label+']').remove();			
		},


		clear: function() {
			$('.e2-box-img').remove();
			$('.e2-box-box').remove();
			$('tr[data-label]').remove();
		},

		_save: function(label) {
			var boxes = $('.e2-box-img[data-label='+label+']');
			var rec = emen2.caches['record'][label];
			rec['box_coords'] = $.makeArray(boxes.map(function(){return $(this).BoxImg('getcoords')}));
			rec['box_label'] = $('.e2-box-label[data-label='+label+']').val();
			rec['box_size'] = $('.e2-box-size[data-label='+label+']').val();
			return rec
		},

		saveall: function() {
			var self = this;
			var recs = [];

			$('.e2l-spinner', this.element).show();

			$(".e2-box-boxarea", this.element).each(function(){
				var rec = self._save($(this).attr('data-label'));
				recs.push(rec);
			});

			recs = recs.reverse();
			this.clear();	
			
			emen2.db("putrecord", [recs], function(recs) {
				$.each(recs, function() {
					$('.e2l-spinner', self.element).hide();
					self.load_record(this);
				});
			});			
		},

		save: function(label) {
			var rec = this._save(label);
			emen2.db("putrecord", [rec], function(newrec) {
				emen2.caches['record'][newrec.name] = newrec;
				self.remove_label(label, true);
				self.load_record(newrec);
			});
		},
		
		load_record: function(rec) {
			var self = this;
			
			if (rec==null) {
				emen2.db("newrecord", ["box", self.options.name], function(rec) {
					rec.name = self.currentlabel;
					self.currentlabel -= 1;
					//rec["parents"] = [self.options.name];
					self.load_record(rec);
				})
				return				
			}
			
			rec["box_size"] = rec["box_size"] || this.options.boxsize;
			emen2.caches['record'][rec.name] = rec;
			this.build_boxarea(rec.name);
			$.each(rec['box_coords'] || [], function(i) {
				self.addbox(this[0], this[1], rec.name);
			});
			
		},		
		
		build_boxarea: function(label) {
			var self = this;
						
			emen2.caches["colors"][label] = emen2.caches['colors'][label] || this.options.colors.pop();

			var box_label = "";
			if (label >= 0) {
				var box_label = emen2.caches['record'][label]['box_label'] || "Box Set "+label;
			}
			

			// This will toggle display of this label group
			var hide = $('<input type="checkbox" data-label="'+label+'" checked="checked" />');
			hide.click(function(){
				var label = $(this).attr("data-label");				
				$('.e2-box-boxarea[data-label='+label+']').toggle()
				$('.e2-box-box[data-label='+label+']').toggle()
			});	


			var colorpicker = $('<input class="e2-box-colorpicker" data-label="'+label+'" type="text" size="4" value="'+emen2.caches["colors"][label]+'" />');
			colorpicker.change(function() {
				var label = $(this).attr("data-label");				
				var newcolor = $(this).val();
				emen2.caches["colors"][label] = newcolor;
				$('.e2-box-img[data-label='+label+']').css("border-color", newcolor);
				$('.e2-box-box[data-label='+label+']').css("border-color", newcolor);
			});
			
			var pen = $('<input type="radio" name="pen" value="" data-label="'+label+'"/>');
			pen.change(function() {
				self.pen = $(this).attr('data-label');
			});
			
			var save1 = $('<input data-label="'+label+'" type="button" value="Save" />');
			save1.click(function(e){
				var label = $(this).attr("data-label");
				self.save(label);
			});
			
			var remove = $('<input data-label="'+label+'" type="button" value="Remove" />');
			remove.click(function(e) {
				var label = $(this).attr("data-label");
				self.unlink_label(label, false);
			});			
			
			// Setup the droppable area
			var boxarea = $('<tr data-label="'+label+'"><td colspan="6" class="e2-box-boxarea" data-label="'+label+'" ></tr>');
			$(".e2-box-boxarea", boxarea).droppable({
				greedy: true,
				accept: '.boximg[data-label!='+label+']',
				tolerance: 'pointer',
				activeClass: 'e2-box-boxarea-active',
				drop: function(event, ui) {
					var o = $(ui.draggable).BoxImg('getopts');
					var newlabel = $(this).attr('data-label');
					$('.e2-box-box[data-boxid='+o['boxid']+']').BoxBox('option', 'label', newlabel);
					$('.e2-box-box[data-boxid='+o['boxid']+']').BoxBox('refresh');
					$(ui.draggable).remove();
					$(ui.helper).remove();
					var boximg = $('<img alt="Box" />');
					boximg.BoxImg({bdo: self.options.bdo, x: o['x'], y: o['y'], size: emen2.caches['record'][newlabel]['box_size'], boxid: o['boxid'], scale: 1, label: newlabel, draggable: true});
					$('.e2-box-boxarea[data-label='+newlabel+']').append(boximg);
					self.updateboxcount(newlabel);
					self.updateboxcount(o['label']);		
				}
			});
						
												
			// Attach everything to the table..
			var colorcontrols = $('<td />');
			colorcontrols.append(pen, hide, colorpicker);

			var actions = $('<td />');
			actions.append(emen2.template.spinner(), save1, remove);					

			var boxheader = $('<tr data-label="'+label+'" />');
			
			boxheader.append(colorcontrols, '<td class="e2-box-count" data-label="'+label+'"></td>', '<td><input type="text" class="e2-box-size" name="box_size" data-label="'+label+'" value="'+emen2.caches['record'][label]['box_size']+'" size="2" /></td>', '<td><input class="e2-box-label" data-label="'+label+'" name="box_label" type="text" size="30" value="'+box_label+'" /></td>', actions);

			this.element.find(".boxtable tbody").prepend(boxheader, boxarea);

			// this is down here because colorPicker is primitive.
			$('.e2-box-colorpicker[data-label='+label+']', boxheader).colorPicker();

			// select this as active pen
			$('input:radio[data-label='+label+']', boxheader).trigger('click');
			this.pen = label;
			
			$('input[name=box_size]', boxheader).change(function() {
				var label = $(this).attr("data-label");				
				var boxsize = parseInt($(this).val());
				emen2.caches['record'][label]['box_size'] = boxsize;
				$('.e2-box-img[data-label='+label+']').BoxImg('setsize', boxsize);
				$('.e2-box-box[data-label='+label+']').BoxBox('setsize', boxsize);
			});
			
		},		

		
		set_range: function() {
			// this.dispmin.val(this.emdata['render_min']);
			// this.dispmax.val(this.emdata['render_max']);
			// this.minmax.slider('option', 'min', parseInt(this.emdata['minimum']));
			// this.minmax.slider('option', 'max', parseInt(this.emdata['maximum']));
			// this.minmax.slider('values', 0, parseInt(this.emdata['render_min']));
			// this.minmax.slider('values', 1, parseInt(this.emdata['render_max']));
			// this.img.attr('data-min', this.emdata['render_min']);
			// this.img.attr('data-max', this.emdata['render_max']);
			// this.img.trigger('refresh');
		}
	});


    $.widget("emen2.BoxBox", {
		options: {
			bdo: null,
			x: 0,
			y: 0,
			size: 0,
			scale: 1,
			rmin: null,
			rmax: null,
			boxid: null,
			label: null
		},		
				
		_create: function() {
			this.element.addClass("e2-box");			
			this.element.addClass("e2-box-box");
			this.element.attr("data-boxid", this.options.boxid);
			this.element.attr("data-label", this.options.label);
			this.element.css("position", 'absolute');			
			this.bind_draggable();
			this.refresh();
		},
		
		bind_draggable: function() {
			var self = this;

			this.element.click(function(e) {
				e.stopPropagation();
				if ( e.shiftKey ) {
					self.remove_box();
				}
			});

			this.element.hover(function() {
				$('[data-boxid='+self.options.boxid+']').addClass("e2-box-hover");
			}, 
			function() {
				$('[data-boxid='+self.options.boxid+']').removeClass("e2-box-hover");				
			});

			this.element.draggable({
				// containment: $(self.element.parent()),
				stop: function() {
					// calculate new coords and update linked BoxImg
					self.options.x = (this.offsetLeft * self.options.scale) + (self.options.size) / 2;
					self.options.y = (this.offsetTop * self.options.scale) + (self.options.size) / 2;
					var linkedbox = $('.e2-box-img[data-boxid='+self.options.boxid+']');
					linkedbox.BoxImg('option', 'x', self.options.x);
					linkedbox.BoxImg('option', 'y', self.options.y);
					linkedbox.BoxImg('refresh');
				}
			});	
					
		},
		
		remove_box: function() {
			$('div[data-bdo='+this.options.bdo+']').Boxer('remove_box', this.options.boxid);
		},
				
		refresh: function() {
			var boxscale = this.options.size / this.options.scale;
			var disp_x = (this.options.x - (this.options.size) / 2) / this.options.scale;
			var disp_y = (this.options.y - (this.options.size) / 2) / this.options.scale;			
			var color = emen2.caches["colors"][this.options.label];
			this.element.css('border-color', color)			
			this.element.css("left", disp_x);
			this.element.css("top", disp_y);
			this.element.css("width", boxscale);
			this.element.css("height", boxscale)
		},
		
		setsize: function(size) {
			this.options.size = size;
			this.refresh();
		}
	});


    $.widget("emen2.BoxImg", {
		options: {
			bdo: null,
			x: 0,
			y: 0,
			size: 0,
			scale: 1,
			rmin: null,
			rmax: null,
			boxid: null,
			label: null,
			draggable: false
		},
				
		_create: function() {
			this.element.addClass("e2-box");
			this.element.addClass("e2-box-img");
			this.element.attr('data-boxid', this.options.boxid);
			this.element.attr("data-label", this.options.label);
			if (this.options.draggable) {
				this.bind_draggable();
			}
			this.refresh();
		},
		
		bind_draggable: function() {
			var self = this;

			this.element.hover(function() {
				$('.e2-box-box[data-boxid='+self.options.boxid+']').addClass("e2-box-hover");
			}, 
			function() {
				$('.e2-box-box[data-boxid='+self.options.boxid+']').removeClass("e2-box-hover");				
			});

			this.element.click(function(e) {
				e.stopPropagation();
				if ( e.shiftKey ) {
					self.remove_box();
					return
				}
				$('.e2-tile[data-bdo='+self.options.bdo+']').TileControl('move', self.options.x, self.options.y);
			});
			
			this.element.draggable({
				appendTo: "body",
				helper: "clone"
				//containment: $('#controls').length ? '#controls' : 'document', // stick to demo-frame if present
			});
		},
		
		remove_box: function() {
			$('div[data-bdo='+this.options.bdo+']').Boxer('remove_box', this.options.boxid);
		},		
		
		getopts: function() {
			var optcopy = {}
			$.each(this.options, function(k,v) {
				optcopy[k]=v;
			})
			return optcopy
		},
		
		getcoords: function() {
			return [[this.options.x, this.options.y]]
		},	
		
		refresh: function() {
			var self = this;
			var color = emen2.caches["colors"][this.options.label];
			this.element.css('border-color', color);
			
			var eman2_x = self.options.x - self.options.size / 2;
			var eman2_y = self.options.y - self.options.size / 2;
			
			var src = EMEN2WEBROOT+'/eman2/'+self.options.bdo+'/box?x='+eman2_x+'&y='+eman2_y+'&size='+self.options.size+'&scale='+self.options.scale;
			if (self.options.rmin || self.options.rmax) {
				src += '&amp;min='+self.options.rmin+'&amp;max='+self.options.rmax;
			} 
			self.element.attr('src', src);			
		},
		
		setsize: function(size) {
			this.options.size = size;
			this.refresh();
		}
	});


    $.widget("emen2.TileControl", {
		options: {
			width: 0,
			height: 0,
			size: 256,
			x: null,
			y: null, 
			scale: 'auto',
			bdo: null,
			mode: "live",
			displaymode: 'image',
			show: true,
			controlsinset: true,
			scales: [1, 2, 4, 8, 16],
			name: null
		},
		
		_create: function() {		
			if (this.options.bdo == null) {
				this.options.bdo = this.element.attr('data-bdo');
			}
			this.element.attr('data-bdo', this.options.bdo);			
			
			if (this.options.show) {
				this.show();
			}
		},
		
		show: function() {
			var self = this;
			if (this.options.mode == "cached") {
				this.element.append(emen2.template.spinner());
				$.ajax({
					type: 'POST',
					url: EMEN2WEBROOT+'/tiles/'+this.options.bdo+'/check/',
					dataType: 'json',
					success: function(d) {
						$('.e2l-spinner', self.element).remove();
						//self.options.extend(d);
						self.options.width = d['width'];
						self.options.height = d['height'];
						self.options.filename = d['filename'];
						self.options.maxscale = d['maxscale'];
						self.build();
					},
					error: function(x,y,z) {
						//alert("Error! Could not access tiles!");
						$('.e2l-spinner', self.element).remove();
						self.build_static();
						self.element.append('Could not access tiles!');
					}
				});
			} else if (this.options.mode == "static") {
				this.build_static();
			} else {
				this.build();
			}
		},
		
		build_static: function() {
			var img = $('<img src="'+EMEN2WEBROOT+'/download/'+this.options.bdo+'/" />');
			this.element.empty();
			this.element.append(img);
		},
		
		build: function() {
			
			var self = this;
			this.inner = $('<div style="position:relative;top:0px;left:0px" />'); //;width:1024px;height:1024px;
			this.element.append(this.inner);
			this.element.attr('data-bdo', this.options.bdo);			

			//this.setscale(this.options.scale);
			this.setdisplaymode(this.options.displaymode);
			
			this.inner.draggable({
				drag:function(){
					var offset = self.offset_to_center();
					self.options.x = offset[0];
					self.options.y = offset[1];
					self.recalc();
				}
			}); //.addTouch();
			
			this.inner.click(function(e) {
				e.stopPropagation();
				parentpos = self.inner.position();
				var x = (e.clientX - parentpos.left) * self.options.scale;
				var y = (e.clientY - parentpos.top) * self.options.scale;
				$('div[data-bdo='+self.options.bdo+']').Boxer('addbox', x, y); // callback to the Boxer controller
			});

			var apix = null; //emen2.caches['record'][this.options.name]['angstroms_per_pixel'];
			if (!apix) {
				apix = 1.0;
			}

			var controls = $('<div class="e2-tile-controls"> \
				<h4 class="e2l-label">Image</h4> \
				<input type="button" name="zoomout" value="-" /> <input type="button" name="zoomin" value="+" /><br /> \
				<input type="button" name="autocenter" value="Center" /> <br />\
				<a class="e2-button" href="'+EMEN2WEBROOT+'/download/'+self.options.bdo+'/'+self.options.filename+'">Download</a> \
				<h4 class="e2l-label">Mode</h4> \
				<div style="text-align:left"> \
				<input type="radio" name="displaymode" value="image" id="displaymode_image" checked="checked" /><label for="displaymode_image">Image</label><br />\
				<input type="radio" name="displaymode" value="pspec" id="displaymode_pspec" /><label for="displaymode_pspec">PSpec</label><br />\
				<input type="radio" name="displaymode" value="1d" id="displaymode_1d" /><label for="displaymode_1d">1D</label> <br />\
				<input type="text" name="apix" value="'+apix+'" size="1" /><span class="e2l-small">A/px</a><br />\
				</div> \
			</div>');
			
			this.element.append(controls);			

			controls.find("input[name=displaymode]").click(function() {
				self.setdisplaymode($(this).val());
			});
			controls.find("input[name=zoomin]").click(function() {
				self.zoomin();
			});
			controls.find("input[name=zoomout]").click(function() {
				self.zoomout();
			});			
			controls.find("input[name=autocenter]").click(function() {
				self.autocenter();
			});			
			controls.find("input[name=larger]").click(function() {
				var ot =  $(window).height()-100;
				var of = self.element.offset().top;
				$('html, body').animate({scrollTop:of}, 0);
				self.element.height(ot);
				self.options.scale = self.autoscale();
				self.autocenter();
			});			
			controls.find("input[name=apix]").change(function() {
				if (self.options.displaymode == '1d') {
					self.setdisplaymode('1d')
				}
			});
		},
		
		setdisplaymode: function(mode) {
			$('img', this.inner).remove();
			var mx = this.element.width();
			var my = this.element.height();
			this.options.displaymode = mode;
			if (mx > my) {mx = my}
			if (mode=="image") {
				this.options.scale = this.autoscale();
				this.setscale(this.options.scale);
				this.autocenter();

			} else if (mode == "1d") {
				var apix = $('input[name=apix]').val(); // this should include [data-bdo=..]
				if (!apix) {
					apix = 1;
				}
				var modeimg = $('<img src="'+EMEN2WEBROOT+'/tiles/'+this.options.bdo+'/1d/?angstroms_per_pixel='+apix+'" alt="apix" />');				
				modeimg.height(mx);
				this.inner.append(modeimg);
				this.inner.css('top',0);
				this.inner.css('left',0);

			} else if (mode == "pspec") {
				var modeimg = $('<img src="'+EMEN2WEBROOT+'/download/'+this.options.bdo+'/pspec.png?size=pspec&format=png" alt="pspec" />');
				this.inner.append(modeimg);				
			}
		},

		autoscale: function(refresh) {
			var mx = this.options.maxscale;
			if (mx == null) {mx = 32}
			this.options.scales = [];
			for (var i=0; Math.pow(2,i) <= mx; i++) {
				this.options.scales.push(Math.pow(2, i));
			}
			var sx = this.options.width / this.element.width();
			var sy = this.options.height / this.element.height();
			if (sy > sx) {sx = sy}
			var q = 1;
			for (var i=0; i<this.options.scales.length; i++) {
				if ( sx > this.options.scales[i-1] ){
					q = this.options.scales[i];
				}
			};
			return Math.round(q);
		},
		
		autocenter: function() {
			this.move(this.options.width / 2, this.options.height / 2);
		},
		
		recenter: function() {
			this.move(this.options.x, this.options.y);
		},
		
		move: function(x,y) {
			this.options.x = x;
			this.options.y = y;
			var offset = this.center_to_offset();
			this.inner.css('left', offset[0]);
			this.inner.css('top', offset[1]);
			this.recalc();
		},

		viewsize: function() {
			return [(this.element.width() / 2) * this.options.scale, (this.element.height() / 2) * this.options.scale]
		},
		
		offset_to_center: function() {
			var pos = this.inner.position();
			var v = this.viewsize();
			return [v[0] - (pos.left * this.options.scale), v[1] - (pos.top * this.options.scale)];
		},
		
		center_to_offset: function() {
			var v = this.viewsize();
			var left = this.options.x - v[0];
			var top = this.options.y - v[1];
			return [-left/this.options.scale, -top/this.options.scale]
		},
		
		getbounds: function() {
			var v = this.viewsize();			
			var bounds = [
				this.options.x - v[0], 
				this.options.y - v[1],
				this.options.x + v[0],
				this.options.y + v[1]
				];
			return bounds			
		},
		
		getinner: function() {
			return this.inner
		},		
		
		recalc: function() {
			var v = this.viewsize();
			var bounds = this.getbounds();			
			bounds[0] = bounds[0] - bounds[0] % (this.options.size * this.options.scale);
			bounds[1] = bounds[1] - bounds[1] % (this.options.size * this.options.scale);
			bounds[2] = bounds[2] + bounds[2] % (this.options.size * this.options.scale);
			bounds[3] = bounds[3] + bounds[3] % (this.options.size * this.options.scale);
			if (bounds[0] < 0) {bounds[0] = 0}
			if (bounds[1] < 0) {bounds[1] = 0}
			if (bounds[2] > this.options.width) {bounds[2] = this.options.width}
			if (bounds[3] > this.options.height) {bounds[3] = this.options.height}

			for (var x = bounds[0]; x < bounds[2]; x += this.options.size * this.options.scale) {				
				for (var y = bounds[1]; y < bounds[3] ; y += this.options.size * this.options.scale) {
					var id = 'tile-'+this.options.scale+'-'+x+'-'+y;
					var img = document.getElementById(id);
					if (!img) {
						var src = this.get_tile(x,y);
						var img = $('<img src="'+src+'" id="'+id+'" alt="Tile '+x+' '+y+'" />');
						img.css('position', 'absolute');
						img.css('width', this.options.size);
						img.css('height', this.options.size);					
						img.css('left', x / this.options.scale);
						// Tiles used to be inverted; now they aren't.
						img.css('top', ((this.options.height - y) / this.options.scale) - this.options.size);
						this.inner.append(img);							
					}

				}
			}
		},
		
		get_tile: function(x, y) {
			if (this.options.mode == "cached") {
				return EMEN2WEBROOT+'/tiles/'+this.options.bdo+'/image/?x='+x+'&y='+y+'&level='+this.options.scale
			} else {
				return EMEN2WEBROOT+'/eman2/'+this.options.bdo+'/box?x='+x+'&y='+y+'&size='+this.options.size*this.options.scale+'&fill=1&scale='+this.options.scale
			}
		},
		
		setscale: function(scale) {
			var autoscale = this.autoscale();
			if (scale == 'auto' || scale > autoscale) { scale = autoscale } 
			if (scale < 1) { scale = 1 }
			this.options.scale = scale;
			$('img', this.inner).remove();
			$('.e2-box-box', this.inner).each(function(){$(this).BoxBox('option', 'scale', scale).BoxBox('refresh')});
			this.move(this.options.x, this.options.y);
		},
		
		zoomout: function() {
			var scale = this.options.scale * 2;
			this.setscale(scale);
		},
		
		zoomin: function() {
			var scale = this.options.scale / 2;
			this.setscale(scale);
		}
	});
})(jQuery);

		
// Controls Table
// var ct = $('<table><tbody></tbody></table>');
// // Contrast controls
// var contrast = $('<tr><td>Contrast</td><td><input type="button" name="autocontrast" value="Auto Contrast" /> <input type="text" value="" size="4" name="dispmin" /> <input type="text" name="dispslider" /> <input type="text" name="dispmax" value="" size="4" /></td></tr>');
// contrast.find('input[name=autocontrast]').click(function() {
// 	$.ajax({
// 		type: 'POST',
// 		url: EMEN2WEBROOT+'/eman2/'+self.options.bdo+'/auto_contrast',
// 		dataType: 'json',
// 		success: function(d) {
// 			self.emdata = d;
// 			self.set_range();
// 		}
// 	});
// })
// 
// contrast.find('input[name=dispmin]')
// 	.val(this.emdata['render_min'])
// 	.change(function() {
// 		self.emdata["render_min"] = parseFloat($(this).val());
// 		self.set_range();
// 	});
// 
// contrast.find('input[name=dispmax]')
// 	.val(this.emdata['render_max'])
// 	.change(function() {
// 		self.emdata["render_max"] = parseFloat($(this).val());
// 		self.set_range();
// 	});
// 
// contrast.find('input[name=dispslider]').slider({
// 	range: true,
// 	min: parseInt(this.emdata['minimum']),
// 	max: parseInt(this.emdata['maximum']),
// 	values: [parseInt(this.emdata['render_min']), parseInt(this.emdata['render_max'])],
// 	slide: function(event, ui) {
// 		self.emdata["render_min"] = parseFloat(ui.values[0]);
// 		self.emdata["render_max"] = parseFloat(ui.values[1]);
// 		self.set_range();
// 	}
// });
// 
// ct.find("tbody").append(contrast);

<%!
public = True
headers = {
	'Content-Type': 'application/javascript',
	'Cache-Control': 'max-age=86400'
}
%>
