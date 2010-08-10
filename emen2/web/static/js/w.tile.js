(function($) {
    $.widget("ui.Boxer", {
		options: {
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
			this.element.attr('data-bdo', this.options.bdo);
			if (this.options.show) {
				this.event_click();
			}
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

		build: function() {
			var self = this;
			
			
			var ct = $('<table><tbody></tbody></table>');

			// Zoom in / zoom out
			var zoom = $('<tr><td>Zoom</td><td><input type="button" name="zoomout" value="-" /> <input type="button" name="zoomin" value="+" /></td></tr>');
			zoom.find("input[name=zoomin]").click(function() {
				self.img.TileMap('zoomin');
			});
			zoom.find("input[name=zoomout]").click(function() {
				self.img.TileMap('zoomout');
			});			
			ct.find("tbody").append(zoom);
			
					
			// Contrast controls
			var contrast = $('<tr><td>Contrast</td><td><input type="button" name="autocontrast" value="Auto Contrast" /> <input type="text" value="" size="4" name="dispmin" /> <input type="text" name="dispslider" /> <input type="text" name="dispmax" value="" size="4" /></td></tr>');
			contrast.find('input[name=autocontrast]').click(function() {
				$.ajax({
					type: 'POST',
					url: EMEN2WEBROOT+'/eman2/'+self.options.bdo+'/auto_contrast',
					dataType: 'json',
					success: function(d) {
						self.emdata = d;
						self.set_range();
					}
				});
			})

			contrast.find('input[name=dispmin]')
				.val(this.emdata['render_min'])
				.change(function() {
					self.emdata["render_min"] = parseFloat($(this).val());
					self.set_range();
				});

			contrast.find('input[name=dispmax]')
				.val(this.emdata['render_max'])
				.change(function() {
					self.emdata["render_max"] = parseFloat($(this).val());
					self.set_range();
				});

			contrast.find('input[name=dispslider]').slider({
				range: true,
				min: parseInt(this.emdata['minimum']),
				max: parseInt(this.emdata['maximum']),
				values: [parseInt(this.emdata['render_min']), parseInt(this.emdata['render_max'])],
				slide: function(event, ui) {
					self.emdata["render_min"] = parseFloat(ui.values[0]);
					self.emdata["render_max"] = parseFloat(ui.values[1]);
					self.set_range();
				}
			});

			ct.find("tbody").append(contrast);



			// Box areas
			this.boxtable = $('<table><thead><tr><th style="width:60px">Visible</th><th style="width:30px">Count</th><th>Name <input name="newset" type="button" value="New Set" /></th><th style="width:60px">Actions</th></tr></thead><tbody></tbody></table>');
			$('input[name=newset]', this.boxtable).click(function() {self.createboxarea()});



			this.controls = $('<div class="boxercontrols floatright" style="width:800px" ></div>');			
			this.controls.append(ct, this.boxtable);


			//this.element.append('<div id="wtf">WTF</div>');			
			this.element.append(this.controls)			



			this.img = $('<div class="tilemap" />');
			this.element.append(this.img);
			this.img.TileMap({bdo: this.options.bdo, scale: 4, width: this.emdata['nx'], height: this.emdata['ny']});

	


			// if there are records, do some callbacks..
			if (this.options.boxrecords) {
				
				$.jsonRPC("getrecord", [this.options.boxrecords], function(recs) {
					
					$.each(recs, function(i) {
						caches["recs"][this.recid] = this;
						self.createboxarea(this.recid);
						self.reload_record(this);						
					});
					
				});	
			
			} else {
				// If there are no boxes, start a new set..
				this.createboxarea();				
			}
						
		},
		
		reload_record: function(rec) {
			var self = this;
			$('.boximg[data-label='+rec.recid+']').remove();
			$('.boxbox[data-label='+rec.recid+']').remove();
			$.each(rec['box_coords'], function(i) {
				self.addbox(this[0], this[1], rec.recid);
			});
		},

		addbox: function(x, y, label) {
			// add a new box at x, y with label			
			label = label || this.pen;
			// get current image scale
			var scale = this.img.TileMap('option', 'scale');

			// increment box counter for id's
			this.boxid += 1;

			// create a new box overlay
			var boxbox = $('<div>&nbsp;</div>');
			boxbox.BoxBox({bdo: this.options.bdo, x: x, y: y, size: this.options.boxsize, boxid: this.boxid, scale: scale, label: label});
			this.img.TileMap('getinner').append(boxbox);

			// create a new box image
			var boximg = $('<img />');
			boximg.BoxImg({bdo: this.options.bdo, x: x, y: y, size: this.options.boxsize, boxid: this.boxid, scale: 1, label: label, draggable: true});
			$('.boxarea[data-label='+label+']').append(boximg);

			// update box count
			this.updateboxcount(label);
		},
		
		removebox: function(boxid) {
			// kill a box dead
			var label = $('.boximg[data-boxid='+boxid+']').attr('data-label');
			$('.boximg[data-boxid='+boxid+']').remove();
			$('.boxbox[data-boxid='+boxid+']').remove();
			this.updateboxcount(label);
		},
		
		updateboxcount: function(label) {
			label = label || null;
			var boxcount = $('.boximg[data-label='+label+']').length;
			$('.boxcount[data-label='+label+']').html(boxcount);
		},
		
		relabel: function(oldlabel, newlabel) {
			if (this.pen == oldlabel) {
				this.pen = newlabel;
			}
			oldcolor = caches['colors'][oldlabel];
			caches['colors'][newlabel] = oldcolor;
			
			$('[data-label='+oldlabel+']').each(function() {
				$(this).attr("data-label", newlabel);
			});
			$('.boximg[data-label='+oldlabel+']').each(function() {
				$(this).BoxImg('option', 'label', newlabel).BoxImg('refresh');
			});
			$('.boxbox[data-label='+oldlabel+']').each(function() {
				$(this).BoxBox('option', 'label', newlabel).BoxBox('refresh');				
			});
		},
		
		removelabel: function(label) {
			$('.boximg[data-label='+label+']').remove();
			$('.boxbox[data-label='+label+']').remove();			
			$('tr[data-label='+label+']').remove();
		},

		save: function(label) {
			var self = this;
			var boxes = $('.boximg[data-label='+label+']');
			var l = $('.boximg[data-label='+label+']').length;			
			var coords = $.makeArray(boxes.map(function(){return $(this).BoxImg('getcoords')}));
			label = parseInt(label);

			var rec = caches['recs'][label];
			rec['box_coords'] = coords;
			rec['box_count'] = l;
			$.jsonRPC("putrecord", [rec], function(newrec) {
				caches['recs'][newrec.recid] = newrec;
				if (newrec.recid != label) {
					self.relabel(label, newrec.recid);
				}
				//self.reload_record(newrec);
			});
		},
		
		createboxarea: function(label) {
			var self = this;
			
			if (typeof(label) == 'undefined') {
				$.jsonRPC("newrecord", ["box", 1], function(rec) {
					rec.recid = self.currentlabel;
					rec["parents"] = [1];
					caches['recs'][rec.recid] = rec;
					self.createboxarea(rec.recid);
					self.currentlabel -= 1;
				})
				return
			}

			var color = this.options.colors.pop();
			caches["colors"][label] = color;


			if (label >= 0) {
				box_label = caches["recs"][label]['box_label'] || "Box Set "+label;
			} else {
				box_label = "Unsaved Set";
			}

			// This will toggle display of this label group
			var hide = $('<input type="checkbox" data-label="'+label+'" checked="checked" />');
			hide.click(function(){
				var label = $(this).attr("data-label");				
				$('.boxarea[data-label='+label+']').toggle()
				$('.boxbox[data-label='+label+']').toggle()
			});	
			
			

			var colorpicker = $('<input class="colorpicker" data-label="'+label+'" type="text" size="4" value="'+caches["colors"][label]+'" />');
			colorpicker.change(function() {
				var label = $(this).attr("data-label");				
				var newcolor = $(this).val();
				caches["colors"][label] = newcolor;
				$('.boximg[data-label='+label+']').css("border-color", newcolor);
				$('.boxbox[data-label='+label+']').css("border-color", newcolor);
			})

			
			
			var pen = $('<input type="radio" name="pen" value="" data-label="'+label+'"/>');
			pen.change(function() {
				self.pen = $(this).attr('data-label');
			})
			

			var save1 = $('<input data-label="'+label+'" type="button" value="Save" />');
			save1.click(function(e){
				var label = $(this).attr("data-label");
				self.save(label);
			})
			
			var remove = $('<input data-label="'+label+'" type="button" value="Remove" />');
			remove.click(function(e) {
				var label = $(this).attr("data-label");
				self.removelabel(label);				
			});
			
			// Setup the droppable area
			var boxarea = $('<tr data-label="'+label+'"><td /><td colspan="5" class="boxarea" data-label="'+label+'" ></tr>');
			$(".boxarea", boxarea).droppable({
				greedy: true,
				accept: '.boximg[data-label!='+label+']',
				tolerance: 'pointer',
				activeClass: 'boxarea-active',
				drop: function(event, ui) {
					var o = $(ui.draggable).BoxImg('getopts');
					var newlabel = $(this).attr('data-label');
					$('.boxbox[data-boxid='+o['boxid']+']').BoxBox('option', 'label', newlabel);
					$('.boxbox[data-boxid='+o['boxid']+']').BoxBox('refresh');
					$(ui.draggable).remove();
					$(ui.helper).remove();
					var boximg = $('<img />');
					boximg.BoxImg({bdo: self.options.bdo, x: o['x'], y: o['y'], size: self.options.boxsize, boxid: o['boxid'], scale: 1, label: newlabel, draggable: true});
					$('.boxarea[data-label='+newlabel+']').append(boximg);
					self.updateboxcount(newlabel);
					self.updateboxcount(o['label']);		
				}
			});
						
			// Attach everything to the table..
			var colorcontrols = $('<td />');
			colorcontrols.append(pen, hide, colorpicker);

			var actions = $('<td />');
			actions.append(save1, remove);					

			var boxheader = $('<tr data-label="'+label+'" />');
			boxheader.append(colorcontrols, '<td class="boxcount" data-label="'+label+'"></td>', '<td><input name="box_label" type="text" size="30" value="'+box_label+'" /></td>', actions);

			$("tbody", this.boxtable).prepend(boxheader, boxarea);

			// this is down here because colorPicker is primitive.
			$('.colorpicker[data-label='+label+']').colorPicker();

			// select this as active pen
			$('input:radio[data-label='+label+']').trigger('click');
			this.pen = label;
			
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
		},		
				
		destroy: function() {
			
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});


})(jQuery);




(function($) {
    $.widget("ui.BoxBox", {
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
			this.element.addClass("boxbox");
			this.element.attr("data-boxid", this.options.boxid);
			this.element.attr("data-label", this.options.label);
			this.bind_draggable();
			this.refresh();
		},
		
		bind_draggable: function() {
			var self = this;

			this.element.click(function(e) {
				e.stopPropagation();
				if ( e.shiftKey ) {
					self.removebox();
				}
			});


			this.element.hover(function() {
				$('[data-boxid='+self.options.boxid+']').addClass("boxhover");
			}, 
			function() {
				$('[data-boxid='+self.options.boxid+']').removeClass("boxhover");				
			});

			this.element.draggable({
				// containment: $(self.element.parent()),
				stop: function() {
					// calculate new coords and update linked BoxImg
					self.options.x = (this.offsetLeft * self.options.scale) + (self.options.size) / 2;
					self.options.y = (this.offsetTop * self.options.scale) + (self.options.size) / 2;
					var linkedbox = $('.boximg[data-boxid='+self.options.boxid+']');
					linkedbox.BoxImg('option', 'x', self.options.x);
					linkedbox.BoxImg('option', 'y', self.options.y);
					linkedbox.BoxImg('refresh');
				}
			});	
					
		},

		build: function() {
			$("#range").slider({
				range: true,
				min: -10,
				max: 10,
				values: [64, 198],
				slide: function(event, ui) {
					$("#preview").attr('data-min', ui.values[0]);
					$("#preview").attr('data-max', ui.values[1]);
					$("#preview").trigger("refresh");	
				}
			});
		
			$("#scale").slider({
				min: 1,
				max: 8,
				value: 8,
				slide: function(event, ui) {
					$("#preview").attr('data-scale', ui.value); 
					$("#preview").trigger("refresh");
				}
			});		

		removebox: function() {
			$('div[data-bdo='+this.options.bdo+']').Boxer('removebox', this.options.boxid);
		},
				
		refresh: function() {
			var boxscale = this.options.size / this.options.scale;
			var disp_x = (this.options.x - (this.options.size) / 2) / this.options.scale;
			var disp_y = (this.options.y - (this.options.size) / 2) / this.options.scale;			

			var color = caches["colors"][this.options.label];
			this.element.css('border-color', color)			
			this.element.css("left", disp_x);
			this.element.css("top", disp_y);
			this.element.css("width", boxscale);
			this.element.css("height", boxscale)
		},
				
		destroy: function() {
		},

		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);



(function($) {
    $.widget("ui.BoxImg", {
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
			this.element.addClass("boximg");
			this.element.attr('data-boxid', this.options.boxid);
			this.element.attr("data-label", this.options.label);
			if (this.options.draggable) {
				this.bind_draggable();
			}
			this.refresh();
		},
		
		bind_draggable: function() {
			var self = this;
			this.element.click(function(e) {
				e.stopPropagation();
				if ( e.shiftKey ) {
					self.removebox();
				}
			})
			
			
			this.element.hover(function() {
				$('[data-boxid='+self.options.boxid+']').addClass("boxhover");
			}, 
			function() {
				$('[data-boxid='+self.options.boxid+']').removeClass("boxhover");				
			});
			
			this.element.draggable({
				appendTo: "body",
				helper: "clone",
				//containment: $('#controls').length ? '#controls' : 'document', // stick to demo-frame if present
			});			
			
		},
		
		removebox: function() {
			$('div[data-bdo='+this.options.bdo+']').Boxer('removebox', this.options.boxid);
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
			var color = caches["colors"][this.options.label];
			this.element.css('border-color', color);
			
			var eman2_x = self.options.x - self.options.size / 2;
			var eman2_y = self.options.y - self.options.size / 2;
			
			var src = EMEN2WEBROOT+'/eman2/'+self.options.bdo+'/box?x='+eman2_x+'&amp;y='+eman2_y+'&amp;size='+self.options.size+'&amp;scale='+self.options.scale;
			if (self.options.rmin || self.options.rmax) {
				src += '&amp;min='+self.options.rmin+'&amp;max='+self.options.rmax;
			} 
			self.element.attr('src', src);			
		},
				
		destroy: function() {
			
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
})(jQuery);



(function($) {
    $.widget("ui.TileMap", {
		options: {
			width: 4096,
			height: 4096,
			size: 256,
			scale: 4,
			bdo: null
		},
				
		_create: function() {
			this.pos = null;
			this.inner = $('<div style="position:relative;width:1024px;height:1024px;top:0px;left:0px" />');
			this.element.append(this.inner);
			var self = this;
			this.inner.draggable({
				helper:function(){return $('<span />')},
				drag:function(e){self.event_drag(e)},
				start:function(e){self.event_drag_start(e)}
			});
			this.inner.click(function(e) {self.event_click(e)});
			this.setscale(self.options.scale);

		},
		
		event_click: function(e) {
			e.stopPropagation();
			var pos = this.offset_to_native(e);
			// callback to the Boxer controller
			$('div[data-bdo='+this.options.bdo+']').Boxer('addbox', pos[0], pos[1]);
		},

		event_drag_start: function(e) {
			this.pos = this.inner.position();
			this.dpos = [e.clientX, e.clientY];
		},
		
		event_drag_stop: function(e) {
		},
		
		event_drag: function(e) {			
			var x_offset = e.clientX - this.dpos[0];
			var y_offset = e.clientY - this.dpos[1];
			this.setpos(x_offset, y_offset);		
		},
		
		setpos: function(x,y) {
			this.inner.css('left', this.pos.left + x);
			this.inner.css('top', this.pos.top + y);
			this.recalc();
		},
		
		offset_to_native: function(e) {
			var pos = this.inner.position();
			var parentpos = this.element.offset();			
			console.log(e);
			var x = (e.pageX - parentpos.left) * this.options.scale;
			var y = (e.pageY - parentpos.top) * this.options.scale;
			//$("#wtf").html(x+" - "+y+" - "+this.options.scale);
			return [parseInt(x), parseInt(y)]
		},		
		
		getinner: function() {
			return this.inner
		},		
		
		recalc: function() {
			var pos = this.inner.position();						
			var wx = this.options.width / (this.options.size * this.options.scale);
			var wy = this.options.height / (this.options.size * this.options.scale);

			var x = Math.floor(pos.left / this.options.size);
			var y = Math.floor(pos.top / this.options.size);
			var end_x = -x + this.element.width() / this.options.size;
			var end_y = -y + this.element.height() / this.options.size;
			
			if (x < 0) {x = 0}
			if (y < 0) {y = 0}
			if (end_x > wx) {end_x = wx}
			if (end_y > wy) {end_y = wy}


			for (var nx=x;nx < end_x;nx++) {

				for (var ny=y;ny < end_y;ny++) {					

					var img = document.getElementById(nx+'-'+ny);
					if (!img) {
						var x_offset = nx * this.options.size * this.options.scale;
						var y_offset = ny * this.options.size * this.options.scale;
						var src = EMEN2WEBROOT+'/eman2/'+this.options.bdo+'/box?x='+x_offset+'&amp;y='+y_offset+'&amp;size='+this.options.size*this.options.scale+'&amp;scale='+this.options.scale;
						var img = $('<img src="'+src+'" id="'+nx+'-'+ny+'" />');
						img.css("position", "absolute");
						img.css('width', this.options.size);
						img.css('height', this.options.size);					
						img.css('left', nx * this.options.size);
						img.css('top', ny * this.options.size);				
						this.inner.append(img);							
					}

				}

			}
		},
		
		getcenter: function() {
			var pos = this.inner.position();			
			return [this.element.width() / 2 * this.options.scale - pos.left * this.options.scale, this.element.height() / 2 * this.options.scale - pos.top * this.options.scale];
		},
		
		setscale: function(scale) {
			console.log(scale);
			if (scale < 1) {
				return
			}
			if (scale > 8) {
				return
			}
			
			var center = this.getcenter();
			this.options.scale = scale;
			
			var x_offset = (center[0] - (this.element.width() / 2) * this.options.scale) / this.options.scale;
			var y_offset = (center[1] - (this.element.height() / 2) * this.options.scale) / this.options.scale;

			// change position so we zoom in and out of the same spot
			this.inner.css('left', -x_offset);
			this.inner.css('top', -y_offset);
			$("img", this.inner).remove();
			this.recalc();
			
			$('.boxbox').BoxBox('option', 'scale', this.options.scale);
			$('.boxbox').BoxBox('refresh');
			

		},
		
		zoomout: function() {
			var scale = this.options.scale * 2;
			this.setscale(scale);
		},
		
		zoomin: function() {
			var scale = this.options.scale / 2;
			this.setscale(scale);
		},
				
		destroy: function() {
		},
		
		_setOption: function(option, value) {
			$.Widget.prototype._setOption.apply( this, arguments );
		}
	});
})(jQuery);

// 
// function TileWidget(elem, opts) {
// 	this.elem = $(elem);
// 	if (typeof(opts) != "object") opts = {};
// 	$.extend(this, TileWidget.DEFAULT_OPTS, opts);
// 	this.init();
// };
// 
// TileWidget.prototype = {
// 	
// 	init: function() {
// 		this.built = 0;
// 		this.boxes = [[0,0],[1023,1023],[0,1023], [2047,2047], [4095,4095]];
// 		this.boxsize = 20;
// 		this.imgsize = 4096;
// 				
// 		this.nx = 0;
// 		this.ny = 0;
// 		this.level = this.nx.length - 1;
// 		this.recid = parseInt(this.elem.attr("data-recid"));
// 		this.bid = this.elem.attr("data-bid");
// 		this.build();
// 
// 	},
// 	
// 	
// 	build: function() {
// 		var self=this;
// 		this.built = 1;
// 		
// 	},
// 	
// 	build_boxes: function() {
// 		
// 		var scale = this.imgsize / this.elem.width();
// 		// console.log(scale);
// 
// 		$.each(this.boxes, function(){
// 
// 			var box = $('<div>');
// 			box.css("position","absolute");
// 			box.css("left", (this[0]/scale)-(self.boxsize/2));
// 			box.css("top", (this[1]/scale)-(self.boxsize/2));
// 			box.css("width", self.boxsize);
// 			box.css("height", self.boxsize)
// 			box.css("border", "solid");
// 			box.css("border-color", "red");
// 			box.css("border-width", "1px");
// 			self.elem.append(box);
// 		});
// 
// 	}
// 
// }
// 
// $.fn.TileWidget = function(opts) {
//   return this.each(function() {
// 		return new TileWidget(this, opts);
// 	});
// };
// 
// return TileWidget;
// 
// })(jQuery); // End localisation of the $ function
// 
// var isdown=false;
// var nx=0
// var ny=0
// var level=nx.length-1
// var tileid = "";
// var divdim = [512,512];
// var imgw = 256;
// var bid = null;
// 
// /*************************************************/
// 
// 
// function tile_download(bid,filename) {
// 	//alert("Download "+bid+", "+filename);
// 	//http://ncmidb2:8080/download/200412170010B/20041208031758.dm3.gz
// 	//window.location("/download/"+bid+"/"+filename);
// }
// 
// function tile_bindresize() {   
// 	var resizeTimer = null;
// 	$(window).bind('resize', function() {
// 		if (resizeTimer) clearTimeout(resizeTimer);
// 		resizeTimer = setTimeout(tile_fitheight, 100);
// 	});	
// }
// 
// function tile_fitheight() {
// 
// 	var e1=$(window).height();
// 	$("#outerdiv").height(e1-120);
// 	tile_center();
// 	
// }
// 
// function tile_center() {
// 	indiv=document.getElementById("innerdiv");	
// 	indiv.style.left=($("#outerdiv").width() - (imgw*nx[level]))/2 + "px";
// 	indiv.style.top=($("#outerdiv").height() - (imgw*ny[level]))/2 + "px";
// }
// 
// function tile_larger(bid) {
// 	window.location = EMEN2WEBROOT+"/db/tiles/"+bid+"/large/";
// }
// 
// function tile_pspec(bid) {
// 	indiv=document.getElementById("innerdiv");
// 	indiv.style.left="0px";
// 	indiv.style.top="0px";
// 	var e=document.createElement("img");
// 	e.src=EMEN2WEBROOT+'/db/tiles/'+bid+'/image/?level=-1&amp;x=0&amp;y=0';
// 	e.width=divdim[0];
// 	e.height=divdim[1];
// 	$(indiv).empty().append(e);
// }
// function tile_1d(bid) {
// 	indiv=document.getElementById("innerdiv");
// 	indiv.style.left="0px";
// 	indiv.style.top="0px";
// 	var e=document.createElement("img");
// 	e.src=EMEN2WEBROOT+'/db/tiles/'+bid+'/image/?level=-2&amp;x=0&amp;y=0';
// 	e.width=divdim[0];
// 	e.height=divdim[1];
// 	$(indiv).empty().append(e);
// }
// 
// 
// function tile_init(ibid) {
// 	bid = ibid;
// 	
// 	var outerdivie=document.getElementById("outerdiv");
// 	var imgw = $("#outerdiv").height() / 2.0;
// 	if (imgw > 256) {imgw = 256;}
// 	
// 	var innerdivie=document.getElementById("innerdiv");
// 	innerdivie.innerHTML = '<img style="margin-top:60px;" src="'+EMEN2WEBROOT+'/images/spinner.gif" /><br />Checking tiles...'
// 
// 	$.getJSON(EMEN2WEBROOT+"/db/tiles/"+bid+"/check/", tile_checktile_cb);
// 
// }
// 
// 
// function tile_rebuild(bid) {
// 	var innerdivie=document.getElementById("innerdiv");
// 	innerdivie.innerHTML = '<img style="margin-top:60px;" src="'+EMEN2WEBROOT+'/images/spinner.gif" /><br />Generating tiles...'	
// 	//$.getJSON(EMEN2WEBROOT+"/db/tiles/"+bid+"/create/", tile_createtile_cb, tile_checktile_eb);
// 	return jQuery.ajax({
// 		type: "GET",
// 		url: EMEN2WEBROOT+"/db/tiles/"+bid+"/create/",
// 		success: tile_createtile_cb,
// 		error: tile_checktile_eb,
// 		dataType: "json"
// 		});
// }
// 
// 
// function tile_checktile_cb(r) {
// 	//console.log("got checktile cb");
// 	//console.log(r);
// 	
// 	var innerdivie=document.getElementById("innerdiv");
// 	if (r[0][0] > 0) {
// 		// tile ok
// 		tile_init2(r[0],r[1],r[2]);
// 		tile_center();
// 	} else {
// 		// generate tile; init on callback
// 		innerdivie.innerHTML = '<img style="margin-top:60px;" src="'+EMEN2WEBROOT+'/images/spinner.gif" /><br />Generating tiles...'
// 		tile_rebuild(r[2]);
// 		//var createtile = new CallbackManager();
// 		//createtile.register(tile_createtile_cb);
// 		//createtile.req("createtile",[r[2],ctxid]);
// 
// 	}
// }
// 
// function tile_checktile_eb(r) {
// 	tile_error();
// }
// 
// function tile_createtile_cb(r) {
// 	if (r[0][0] > -1) {
// 		tile_init2(r[0],r[1],r[2]);
// 	} else {
// 		tile_error();
// 	}
// }
// 
// function tile_error() {
// 	var innerdivie=document.getElementById("innerdiv");	
// 	innerdivie.innerHTML = '<img style="margin-top:60px;" src="'+EMEN2WEBROOT+'/images/error.gif" /><br />Error: Could not create or access tiles.'
// }
// 
// /*************************************************/
// 
// 
// 
// function tile_init2(nxinit,nyinit,tileidinit) {
// 	nx = nxinit;
// 	ny = nyinit;
// 	tileid = tileidinit;
// 	level = nx.length-1;
// //	alert("nx: " + nx + "\nny: " + ny + "\ntileid: " + tileid + "\nlevel: " + level);
// 	
// 	setsize(nx[level]*imgw,ny[level]*imgw);
// 	var outdiv=document.getElementById("outerdiv");
// 	outdiv.onmousedown = mdown;
// 	outdiv.onmousemove = mmove;
// 	outdiv.onmouseup = mup;
// 	outdiv.ondragstart = function() { return false; }
// 	recalc();
// }
// 
// function tofloat(s) {
// 	if (s=="") return 0.0;
// 	return parseFloat(s.substring(0,s.length-2));
// }
// 
// function zoom(lvl) {
// 	if (lvl==level || lvl<0 || lvl>=nx.length) return;
// 	indiv=document.getElementById("innerdiv");
// 	x=tofloat(indiv.style.left);
// 	y=tofloat(indiv.style.top);
// 
// 	outdiv=document.getElementById("outerdiv");
// 
// 	cx=outdiv.clientWidth / 2.0;
// 	cy=outdiv.clientHeight / 2.0;
// 
// 
// 	setsize(nx[lvl]*256,ny[lvl]*256);
// 
// 	scl=Math.pow(2.0,level-lvl)
// 	indiv.style.left=cx-((cx-x)*scl) + "px";
// 	indiv.style.top=cy-((cy-y)*scl) + "px";
// //	//console.log([cx-((cx-x)*scl),cy-((cy-y)*scl)]);
// 
// 	for (i=indiv.childNodes.length-1; i>=0; i--) indiv.removeChild(indiv.childNodes[i]);
// 	level=lvl
// 	recalc();
// }
// 
// function zoomout() {
// 	zoom(level+1);
// }
// 
// function zoomin() {
// 	zoom(level-1);
// }
// 
// function mdown(event) {
// 	if (!event) event=window.event;		// for IE
// 	indiv=document.getElementById("innerdiv");
// 	isdown=true;
// 	y0=tofloat(indiv.style.top);
// 	x0=tofloat(indiv.style.left);
// 	mx0=event.clientX;
// 	my0=event.clientY;
// 	return false;
// }
// 
// function mmove(event) {
// 	if (!isdown) return;
// 	if (!event) event=window.event;		// for IE
// 	indiv=document.getElementById("innerdiv");
// 	indiv.style.left=x0+event.clientX-mx0 + "px";
// 	indiv.style.top=y0+event.clientY-my0 + "px";
// 
// 	recalc();
// }
// 
// function mup(event) {
// 	if (!event) event=window.event;		// for IE
// 	isdown=false;
// 	recalc();
// }
// 
// function recalc() {
// //	alert("Recalc");
// 	indiv=document.getElementById("innerdiv");
// 	x=-Math.ceil(tofloat(indiv.style.left)/imgw);
// 	y=-Math.ceil(tofloat(indiv.style.top)/imgw);
// 	outdiv=document.getElementById("outerdiv");
// 	dx=outdiv.clientWidth/imgw+1;
// 	dy=outdiv.clientHeight/imgw+1;
// 	for (i=x; i<x+dx; i++) {
// 		for (j=y; j<y+dy; j++) {
// 			if (i<0 || j<0 || i>=nx[level] || j>=ny[level]) continue;
// 			nm="im"+i+"."+j
// 			var im=document.getElementById(nm);
// 			if (!im) {
// 				im=document.createElement("img");
// 				im.src=EMEN2WEBROOT+"/db/tiles/" + tileid + "/image/?level="+level+"&x="+i+"&y="+j;
// 				im.style.position="absolute";
// 				im.style.height=imgw+"px";
// 				im.style.width=imgw+"px";
// 				im.style.left=i*imgw+"px";
// 				im.style.top=j*imgw+"px";
// 				im.setAttribute("id",nm);
// 				indiv.appendChild(im);
// 			}
// 		}
// 	}
// }
// 
// function setsize(w,h) {
// 	var indiv=document.getElementById("innerdiv");
// 	indiv.style.height=h;
// 	indiv.style.width=w;
// }

