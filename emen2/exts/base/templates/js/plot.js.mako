(function($) {
	
	$.widget('emen2.AxisControl', {
		options: {
		},
		
		_create: function() {
			this.scale = d3.scale.linear().domain([0,0]);
			this.min = null;
			this.max = null;
			this.bin = null;
			this.hide = null;
			this.keys = null;
		}
	});
	
	
	$.widget('emen2.PlotControl', {
		options: {
			// q and controls are the only option.
			// xkey: 'name',
			// ykey: 'name',
			// zkey: 'rectype'
		},
		
		_create: function() {
			this.built = 0;
			// options
			this.copy = ['xkey', 'ykey', 'zkey', 'xmin', 'xmax', 'ymin', 'ymax', 'xbin', 'ybin', 'zbin'];
			this.build();
		},
		
		build: function() {
			var self = this;
			// Reset
			// Create query
			var oq = this.options.q;
			var q = {};
			q['c'] = oq['c'];
			q['ignorecase'] = oq['ignorecase'];
			q['boolmode'] = oq['boolmode'];
			q['axes'] = oq['axes'];
			q['recs'] = true;
			
			// Execute the query and build on cb
			$.jsonRPC.call('query', q, function(q) {
				self._build(q);
			});
		},
		
		rebuild: function(q) {
			// Rebuild using a new query
			this.options.q = q;
			this.built = 0;
			this.build();
		},
		
		_build: function(q) {
			this.options.q = q;
			this.build_plot();
			this.build_controls();
		},
		
		build_plot: function(opts) {
			$('.e2-plot', this.element).remove();
			var w = this.element.parent().width(); // hack
			var plotelem = $('<div class="e2-plot e2l-float-left"></div>');
			plotelem.width(w-300);
			this.element.append(plotelem);
			this.options.controls = this;
			if (this.options.xbin) {
				plotelem.PlotHistogram(this.options);
				this.plot = plotelem.data('PlotHistogram');				
			} else {
				plotelem.PlotScatter(this.options);
				this.plot = plotelem.data('PlotScatter');				
			}
		},
		
		build_controls: function() {
			$('.e2-plot-controls', this.element).remove();
			var self = this;
			var controls = $(' \
				<ul class="e2-plot-controls"> \
				</ul>');				
			var x = $('<li data-controls="x"></li>');
			var y = $('<li data-controls="y"></li>');
			var z = $('<li data-controls="z"></li>');
			controls.append(x, y, z);
			controls.append('<li><input type="button" name="apply" value="Apply" class="e2l-float-right" /></li>');
			this.element.append(controls);
			$('input[name=apply]', controls).click(function(e) {self.apply()});
			this.build_continuous('x');
			this.build_continuous('y');
			this.build_discrete('z');
			//this.update();
		},
		
		build_continuous: function(axis) {
			var c = $('[data-controls='+axis+']');
			c.append('<h4>'+axis.toUpperCase()+'</h4>');
			c.append(this.build_param(axis));
			c.append('<div><span class="e2-plot-label">Range:</span> <input type="text" name="'+axis+'min" value="" class="e2-plot-bounds" /> - <input type="text" name="'+axis+'max" class="e2-plot-bounds" /></div>');
			c.append(this.build_bins(axis));
		},
		

		build_param: function(axis) {
			var elem = $('<div><span class="e2-plot-label">Param:</span> </div>');			
			elem.append('<input type="text" name="'+axis+'key" value="'+(this.plot.options[axis+'key'] || "name")+'" style="width:120px"/>');
			return elem
			// This is a horrible hack
			// ... add all keys in all q['recs'] ...
		},
		
		build_bins: function(axis, vartype) {
			var elem = $('<div><span class="e2-plot-label">Bins:</span> </div>');
			elem.append('<input type="text" name="'+axis+'bin" class="e2-plot-bounds" />');
			return elem
			// var btime = ['second', 'minute', 'hour', 'day', 'month', 'year'];
		},

		build_discrete: function(axis) {
			var self = this;
			var c = $('[data-controls='+axis+']');
			c.append('<h4>'+axis.toUpperCase()+'</h4>');			
			c.append(this.build_param(axis));
			var table = $('<table cellpadding="0" cellpadding="0"><tbody></tbody></table>');
			var tb = $('tbody', table);
			// var zkeys = this.plot[axis+'keys'];
			var zcolors = this.plot.options.zcolors;
			var zkeys = $.sortdict(this.plot.zsort);
			zkeys.map(function(z, i) {
				var row = $('<tr></tr>');
				// Show/hide
				var td = $('<td></td>');
				var cbox = $('<input type="checkbox" name="'+axis+'hide" value="'+z+'" />');
				if ($.inArray(z, self.options[axis+'hide'])==-1) {
					cbox.attr('checked', true);
				}
				td.append(cbox);
				row.append(td);
				// Name
				row.append('<td>'+z+'</td>')
				row.append('<td>'+self.plot.zsort[z]+'</td>');
				// Colors
				row.append('<td><div class="e2-plot-color" style="background:'+zcolors(i)+'">&nbsp;</div></td>');
				tb.append(row);
			});
			c.append(table);
		},

		build_markers: function(sel) {
			var markers = ['o', 'x', '+', '-'];
			markers.map(function(m) {
				sel.append('<option value="'+m+'">'+m+'</option>');
			});
		},
			
		update: function() {
			var self = this;
			this.copy.map(function(i) {
				$('input[name='+i+']', self.element).val(self.plot.options[i]);
			});
		},
		
		apply: function() {
			var self = this;
			var opts = {};
			var total = false;
			var changed = {}; // emulate set
			this.copy.map(function(i) {
				var val = $('input[name='+i+']', self.element).val();
				if (!val) {
					val = null;
				}
				if (val != self.options[i]) {changed[i]=true}
				self.options[i] = val;
			});
			var check = ['xkey', 'ykey', 'zkey', 'xbin', 'ybin', 'zbin'];
			check.map(function(i) {
				if (changed[i]) {total = true}
			});


			var zhide = $('input[name=zhide]:not(:checked)').map(function(){return $(this).val()});
			this.options.zhide = zhide;

			var axes = [this.options.xkey, this.options.ykey, this.options.zkey];
			this.options.q['axes'] = axes;						
			if (total) {
				this.build();
			} else {			
				this.build_plot();
				this.update();			
			}
		}
	});
	
   $.widget('emen2.PlotBase', {
		options: {
			q: null,
			// Axes
			xkey: null,
			ykey: null,
			zkey: 'rectype',
			// Bounds
			xmin: null,
			xmax: null,
			ymin: null,
			ymax: null,
			// Hide series
			xhide: null,
			yhide: null,
			zhide: null,
			// Display
			xticks: 10,
			yticks: 10,
			zcolors: d3.scale.category10(),
			// Padding: top, left, bottom, right
			padding: [10,10,50,50], 
			width: null,
			height: null,
			panx: true,
			pany: true,
			// Bar chart / histogram options
			cumulative: true,
			stacked: true,
			xbin: null,			
		},

		_create: function() {
			this.built = 0;
			this.options.width = $.checkopt(this, 'width', this.element.width()); // -300
			this.options.height = $.checkopt(this, 'height', 500);
			this.setup();

			// Keys
			this.xkeys = [];
			this.ykeys = [];
			this.zkeys = [];
			
			// Setup and build
			this.build();
		},
		
		build: function() {
			if (this.built) {return}
			var self = this;
			this.built = 1;

			if (!this.options.xkey || !this.options.ykey || !this.options.zkey) {
				this.element.append('No axes specified');
				return
			}

			// this.build_controls();

			// Account for padding in the output ranges
			var h = this.options.height - (this.options.padding[0] + this.options.padding[2]);
			var w = this.options.width - (this.options.padding[1] + this.options.padding[3]);
			this.w = w;
			this.h = h;
			this.x.range([0,w]);
			this.y.range([h,0]); // flip the coordinates on the Y axis

			// Create the SVG element
			this.svg = d3.select('.e2-plot')
				.append("svg:svg")
				.attr("width", this.options.width)
				.attr("height", this.options.height)
				.call(d3.behavior.zoom().on("zoom", function(){self.redraw()}))
				.append("svg:g")
				.attr("transform", 'translate('+this.options.padding[1]+','+this.options.padding[0]+')')

			// Background for plot
			this.svg.append('svg:rect')
				.attr('width', this.w)
				.attr('height', this.h)
				.attr('class', 'e2-plot-bg');

			// Add the x-axis.
			this.svg.append("svg:g")
				.attr("class", "x axis")
				.attr("transform", "translate(0," + h + ")")
				.call(this.xaxis);

			// Add the y-axis.
			this.svg.append("svg:g")
				.attr("class", "y axis")
				.attr("transform", "translate(" + w + ",0)")
				.call(this.yaxis);

			this.plotarea = this.svg.append("svg:svg")
				.attr('x', 0)
				.attr('y', 0)
				.attr('width', this.w)
				.attr('height', this.h)
				.style('overflow', 'hidden')
				.append('svg:g')
				.attr('class', 'e2-plot-area')

			// Run the query and plot the result
			this.plot(this.options.q['recs'] || []);
		},
		
		setup: function() {
			// Setup axes
			var h = this.options.height - (this.options.padding[0] + this.options.padding[2]);
			var w = this.options.width - (this.options.padding[1] + this.options.padding[3]);			
			this.x = d3.scale.linear().domain([0,0]);
			this.y = d3.scale.linear().domain([0,0]);
			this.z = this.options.zcolors;

			if (this.options.xkey == 'creationtime') {
				this.fx = function(d) {return new Date(d[this.options.xkey])};
				this.x = d3.time.scale();
			}
						
			this.xaxis = d3.svg.axis().scale(this.x).tickSize(-h,3,0).tickSubdivide(true);
			this.yaxis = d3.svg.axis().scale(this.y).tickSize(-w,3,0).orient('right');
		},
		
		plot: function(q) {
			// Draw the plot
		},
		
		update_controls: function() {
			if (this.options.controls) {
				this.options.controls.update();
			}			
		},
		
		redraw: function() {
			// Update the plot
		},

		group: function(recs) {
			// Histograms group on two axes and replace the X with totals
			// See PlotHistogram
			// todo: break out the common behavior for all axes
			var self = this;
			var bins = {};
			var xkeys = {};
			var ykeys = {};
			var zkeys = {};
			recs.map(function(d) {
				var bx = self.fx(d);
				var by = self.fy(d);
				var bz = self.fz(d);
				xkeys[bx] = bx;
				zkeys[bz] = bz;
				ykeys[by] = by;
				if (bins[bz] == null) {
					bins[bz] = []
				}
				bins[bz].push(d);
			});
			
			// X domain
			var xkeys = d3.values(xkeys);
			xkeys.sort(function(a,b){return a-b});
			var xmin = xkeys[0];
			var xmax = xkeys[xkeys.length-1];			
			
			// Y domain
			var ykeys = d3.values(ykeys);
			ykeys.sort(function(a,b){return a-b});
			var ymin = ykeys[0];
			var ymax = ykeys[ykeys.length-1];

			// Z domain
			var zkeys = d3.values(zkeys);
			// sort by count
			var zsort = {};
			for (var i=0;i<zkeys.length;i++) {
				zsort[zkeys[i]] = bins[zkeys[i]].length;
			}
			zkeys = $.sortdict(zsort);

			// Filter out keys in zhide... 
			// Use map instead of filter to preserve Z colors
			var zkeys = zkeys.map(function(z){
				if ($.inArray(z,self.options.zhide)==-1) {return z}
			});
			this.zsort = zsort;
			
			// Update the keys attributes
			this.xkeys = xkeys;
			this.ykeys = ykeys;
			this.zkeys = zkeys;
			
			// Update options
			if (!this.options.xmin) {this.options.xmin = xmin}
			if (!this.options.xmax) {this.options.xmax = xmax}
			if (!this.options.ymin) {this.options.ymin = ymin}
			if (!this.options.ymax) {this.options.ymax = ymax}
			
			return bins			
		},
		
		query: function(cb) {
			$.jsonRPC.call('getchildren', {names:136}, function(recs){
				$.jsonRPC.call('getrecord', [recs], function(recs){
					cb(recs);					
				});
			});
		},

		// Override the following methods
		fx: function(d) {
			// Return the X key value
			return d[this.options.xkey]
		},
		
		fy: function(d) {
			// Return the Y key value
			return d[this.options.ykey]
		},
		
		fz: function(d) {
			// Return the Z key value
			return d[this.options.zkey]
		},
			
	});	

	$.widget('emen2.PlotScatter', $.emen2.PlotBase, {
		plot: function(recs) {
			var self = this;		
			// Filter the records
			recs = recs.filter(function(d){return (self.fx(d)!=null && self.fy(d)!=null)});
			// Group by Z key
			var bins = this.group(recs);
			

			// Update the X and Y axis domains
			this.x.domain([this.options.xmin, this.options.xmax]);
			this.y.domain([this.options.ymin, this.options.ymax]);
			this.svg.select(".x.axis").call(this.xaxis);
			this.svg.select(".y.axis").call(this.yaxis);

			// Add a group for each cause.
			var groups = this.plotarea.selectAll("g.group")
				.data(this.zkeys)
				.enter().append("svg:g")
				.attr("class", "group")
				.attr('data-bz', function(d,i) {return self.zkeys[i]})
				.style("fill", function(d, i) {return self.z(i)})
				.style("stroke", function(d, i) {return d3.rgb(self.z(i))});			
			
			// Add a rect for each date.
			var rect = groups.selectAll("circle")
				.data(function(d){return d3.values(bins[d])})
				.enter().append("svg:circle")
				.attr("cx", function(d,i) {return self.x(self.fx(d))})
				.attr("cy", function(d,i) {return self.y(self.fy(d))})
				.attr('data-x', function(d) {return self.fx(d)})
				.attr('data-y', function(d) {return self.fy(d)})					
				.attr('data-z', function(d) {return self.fz(d)})
				.attr("r", 3);
								
			this.update_controls();
		},
		
		redraw: function() {			
			var scale = d3.event.scale;
			var trans = d3.event.translate;

			// I spent several hours attempting to do this myself
			// before I looked at the source and saw the transform() method
			// in the event......
			d3.event.transform(this.x, this.y);

			this.svg.select(".x.axis").call(this.xaxis);
			this.svg.select(".y.axis").call(this.yaxis);
			this.plotarea.attr('transform', 'matrix('+scale+' 0 0 '+scale+' '+trans[0]+' '+trans[1]+')');

			var xd = this.x.domain();
			this.options.xmin = d3.min(xd);
			this.options.xmax = d3.max(xd);
			var yd = this.y.domain();
			this.options.ymin = d3.min(yd);
			this.options.ymax = d3.max(yd);
			
			this.update_controls();
		}
	});
	
	$.widget('emen2.PlotHistogram', $.emen2.PlotBase, {
		group_bin: function(recs) {
			var self = this;
			var bins = this.group(recs);
			var sbins = {};

			// Get sorted ordinal names from date range			
			var xkeys = d3.time[this.options.xbin+'s'](d3.time[this.options.xbin](this.options.xmin), this.options.xmax);
			this.xkeys = xkeys;
			this.options.ymax = 0;
			
			// Setup the histogram
			var ymax = 0;
			this.zkeys.map(function(z) {
				sbins[z] = {};
				self.xkeys.map(function(x) {
					sbins[z][x] = {x:x, y:0, y1:0, yoff:0}
				})
				d3.values(bins[z]).map(function(d) {
					var x = d3.time.month(self.fx(d));
					sbins[z][x].y += 1
					sbins[z][x].y1 += 1
					if (sbins[z][x].y > ymax) {ymax = sbins[z][x].y}
				});
			});

			// Update the domain
			this.options.ymin = 0;
			this.options.ymax = ymax;

			// Cumulative
			// this.options.cumulative = false;
			// this.options.stacked = false;
			
			if (this.options.cumulative) {
				this.zkeys.map(function(z) {
					var ysum = 0;
					self.xkeys.map(function(x) {
						ysum += sbins[z][x].y || 0;
						sbins[z][x].y1 = ysum;
					});
					if (ysum > self.options.ymax) {self.options.ymax = ysum}
				});
			}
			if (this.options.stacked) {
				self.xkeys.map(function(x) {
					var yoff = 0;
					self.zkeys.map(function(z) {
						sbins[z][x].yoff = yoff;
						yoff += sbins[z][x].y1;
					});
					if (yoff > self.options.ymax) {self.options.ymax = yoff}				
				});
			}
			return sbins
		},

		fx: function(d) {
			var bx = new Date(d[this.options.xkey]);
			return d3.time.months(bx);
		},

		plot: function(recs) {
			var self = this;
			var bins = this.group_bin(recs);
			var w = this.options.width - (this.options.padding[1] + this.options.padding[3]);
			var binwidth = (w / this.xkeys.length);

			// this.zkeys = ['project'];
			// Update the X and Y axis domains
			this.x.domain([this.options.xmin, this.options.xmax]);
			this.y.domain([this.options.ymin, this.options.ymax]);
			this.svg.select(".x.axis").call(this.xaxis);
			this.svg.select(".y.axis").call(this.yaxis);
			
			// // Add a group for each group.
			var groups = this.plotarea.selectAll("g.group")
				.data(this.zkeys)
				.enter().append("svg:g")
				.attr("class", "group")
				.attr('data-bz', function(d,i) {return self.zkeys[i]})
				.style("fill", function(d, i) {return self.z(i)})
				.style("stroke", function(d, i) {return d3.rgb(self.z(i))});
			
			// Add recs for each bin in each group.
			var rect = groups.selectAll("rect")
				.data(function(d){return d3.values(bins[d])})
				.enter().append("svg:rect")
				.attr('x', function(d) {return self.x(d.x)})
				.attr('y', function(d) {return self.y(d.y1)-(self.h-self.y(d.yoff))})
				.attr('height', function(d) {return self.h-self.y(d.y1)})
				// .attr("y", function(d) {return self.y(d.yoff)})
				// .attr("height", function(d) {return self.h-self.y(d.y1)})
				.attr("width", binwidth)
				.attr('data-y', function(d) {return d.y})
				.attr('data-y1', function(d) {return d.y1})
				.attr('data-yoff', function(d) {return d.yoff});

			this.update_controls();
		},
		
		redraw: function() {			
			d3.event.translate[1] = 0;
			d3.event.transform(this.x);
			var scale = d3.event.scale;
			var trans = d3.event.translate;
			this.svg.select(".x.axis").call(this.xaxis);
			this.plotarea.attr('transform', 'matrix('+scale+' 0 0 1 '+trans[0]+' '+trans[1]+')');

			var xd = this.x.domain();
			this.options.xmin = d3.min(xd);
			this.options.xmax = d3.max(xd);
			var yd = this.y.domain();
			this.options.ymin = d3.min(yd);
			this.options.ymax = d3.max(yd);

			this.update_controls();
		}
		
	});	
	
})(jQuery);


<%!
public = True
headers = {
	'Content-Type': 'application/javascript',
	'Cache-Control': 'max-age=86400'
}
%>