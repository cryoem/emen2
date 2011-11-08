(function($) {
	
	/***** Plot Controller *****/

	$.widget('emen2.PlotControl', {
		options: {
		},
		
		_create: function() {
			this.built = 0;
			this.build();
		},
		
		build: function() {
			var self = this;
			this.options.q['recs'] = [];
			self._build(this.options.q);
		},
		
		rebuild: function() {
			// Rebuild using a new query
			var self = this;
			this.built = 0;
			// Create query
			var oq = this.options.q;
			var q = {};
			q['c'] = oq['c'];
			q['ignorecase'] = oq['ignorecase'];
			q['boolmode'] = oq['boolmode'];
			q['axes'] = oq['axes']; // axis keys
			q['recs'] = true;
			
			// Execute the query and build on cb
			$.jsonRPC.call('query', q, function(q) {
				self._build(q);
			});
			
		},
		
		_build: function(q) {
			this.options.q = q;
			var self = this;
			// Build the controls stub first
			$('.e2-plot-controls', this.element).remove();
			var controls = $('<ul class="e2-plot-controls"></ul>');
			this.element.append(controls);
			// Build the plot
			this.build_plot();
			// Update controls
			controls.append('<li><br /><input type="button" name="update" value="Apply" class="e2l-float-right" /></li>');
			$('input[name=update]', controls).click(function(e){self.update()});
		},
		
		build_plot: function(opts) {
			$('.e2-plot', this.element).remove();
			var plotelem = $('<div class="e2-plot e2l-float-left"></div>');
			var w = this.element.parent().width(); // hack
			plotelem.width(w-300);
			this.element.append(plotelem);			
			// Pass along the parent options
			this.options.controls = this;

			var axopts = this.options.axopts || {};
			var xbin = axopts['x'] || {};
			var bin = xbin['bin'];
			console.log("bin?:", bin);
			if (bin) {
				plotelem.PlotHistogram(this.options);
				this.plot = plotelem.data('PlotHistogram');					
			} else {
				plotelem.PlotScatter(this.options);
				this.plot = plotelem.data('PlotScatter');				
			}
			
		},
		
		update: function() {
			// Ask the plot to read the controls and update
			var q = this.options.q || {};
			var oaxes = q['axes'] || [null,null,null];
			// Do we do a complete query and rebuild, or just update?
			var axopts = this.plot.update();
			console.log(axopts);
			var axes = [axopts['x'].key, axopts['y'].key, axopts['z'].key];
			if (axes[0] != oaxes[0] || axes[1] != oaxes[1] || axes[2] != oaxes[2]) {
				// Full update if an axis param changes
				this.options.axopts = axopts;
				this.options.q['axes'] = axes;
				this.rebuild();
			} else {
				// Partial update
				this.options.axopts = axopts;
				this.options.q['axes'] = axes;
				this._build(this.options.q);
			}
		}
	});


	/****************** BASIC CHARTS ******************/

	/***** Base Axis Control *****/

	$.widget('emen2.AxisControl', {
		options: {
			key: null,
			name: null,
			min: null,
			max: null,
			// Histogram options
			bin: null,
			binnable: false,
			stacked: false,
			cumulative: false,
			hide: [],
			// Display
			ticks: 10,
			pan: true,			
			size: [400,400],
			orient: null,
			invert: false
		},
		
		_create: function() {
			// Other options kept in this.options
			this.keys = [];
			this.controls = $('.e2-plot-controls');			
			this.scale = d3.scale.linear().domain([0,1]);
			this.bins = {};
			this.counted = {};
			this.ax = null;
			this.setup();
		},
		
		f: function(d) {
			// Get the param from a record
			return d[this.options.key];
		},
		
		p: function(d) {
			// Map a value to a point
			return this.scale(this.f(d));
		},
		
		setup: function() {
			// Additional (subclass) setup
			var self = this;
			// Todo: separate subclass
			if (this.options.key == 'creationtime') {
				this.f = function(d) {return new Date(d[self.options.key])};
				this.scale = d3.time.scale();
			}		
			// Axis drawing...
			if (this.options.invert) {
				this.scale.range([this.options.size[0], 0]);
			} else {
				this.scale.range([0, this.options.size[0]]);				
			}

			if (this.options.orient != null) {
				this.ax = d3.svg.axis().scale(this.scale).tickSize(-this.options.size[1],3,0).orient(this.options.orient);
			} else {
				this.ax = d3.svg.axis().scale(this.scale).tickSize(-this.options.size[1],3,0);				
			}
		},
		
		build_controls: function() {
			// Build the control widgets
			if (!this.controls.length) {return}
			var controls = $('<li></li>');
			controls.append('<h4>'+this.options.name.toUpperCase()+'</h4>');
			controls.append('<div><span class="e2-plot-label">Param:</span><input style="width:150px" type="text" name="key" /></div>')
			controls.append('<div><span class="e2-plot-label">Range:</span><input class="e2-plot-bounds" type="text" name="min" /> - <input class="e2-plot-bounds" type="text" name="max" /></div>');
			if (this.options.binnable) {
				controls.append('<div><span class="e2-plot-label">Bin:</span><input class="e2-plot-bounds" type="text" name="bin" /></div>');
			}
			this.controls.append(controls);
			this.controls = controls;
			$('input[name=key]', this.controls).val(this.options.key);
			$('input[name=bin]', this.controls).val(this.options.bin);
			this.update_controls();
		},
		
		update_controls: function() {
			// Update the control widgets on redraw
			if (this.controls) {
				$('input[name=min]', this.controls).val(this.options.min);
				$('input[name=max]', this.controls).val(this.options.max);
			}			
		},
		
		update: function() {
			// Read the controls values
			var opts = {};
			opts['name'] = this.options.name;
			// If we're switching keys, we'll need a total rebuild
			opts['key'] = $('input[name=key]', this.controls).val();
			if (opts['key'] != this.options.key) {
				return opts
			}
			opts['min'] = $('input[name=min]', this.controls).val();
			opts['max'] = $('input[name=max]', this.controls).val();
			opts['bin'] = $('input[name=bin]', this.controls).val();
			opts['stacked'] = $('input[name=stacked]', this.controls).val();
			opts['cumulative'] = $('input[name=cumulative]', this.controls).val();
			opts['hide'] = $("input[name=hide]:not(:checked)", this.controls).map(function(){return $(this).val()});
			return opts
		},
		
		data: function(recs) {
			// Set the domain from the data
			var x = [];
			for (var i=0;i<recs.length;i++) {
				x.push(this.f(recs[i]));
			}
			// If we weren't given bounds, update..
			if (this.options.min == null) {this.options.min = d3.min(x)}
			if (this.options.max == null) {this.options.max = d3.max(x)}
			this.scale.domain([this.options.min, this.options.max]);
		},
		
		redraw: function() {
			// Redraw will always update the bounds
			var domain = this.scale.domain();
			this.options.min = d3.min(domain);
			this.options.max = d3.max(domain);			
			this.update_controls();
		}
	});

	/***** Series Control *****/	
	
	$.widget('emen2.SeriesControl', $.emen2.AxisControl, {
		setup: function() {
			this.options.pan = false;
			this.scale = d3.scale.category10();
		},
		
		data: function(recs) {
			var bins = {};
			for (var i=0;i<recs.length;i++) {
				var bx = this.f(recs[i]);
				if (bins[bx] == null) {bins[bx] = []}
				bins[bx].push(recs[i]);
			}
			var counted = {};
			$.each(bins, function(k,v) {
				counted[k] = v.length;
			});
			this.counted = counted;
			this.keys = $.sortdict(counted);
			var ret = [];
			// Filter out keys in this.options.hide... 
			// Use map instead of filter to preserve Z colors
			for (var i=0;i<this.keys.length;i++) {
				if ($.inArray(this.keys[i], this.options.hide)==-1) {
					ret.push(bins[this.keys[i]]);
				} else {
					ret.push([]);
				}
			}
			return ret
		},
		
		build_controls: function() {
			if (!this.controls) {return}
			var self = this;
			var controls = $('<li></li>');
			controls.append('<h4>'+this.options.name.toUpperCase()+'</h4>');
			controls.append('<div><span class="e2-plot-label">Param:</span><input style="width:150px" type="text" name="key" /></div>')
			var total = 0;
			var table = $('<table cellspacing="0" cellpadding="0"><tbody></tbody></table>');
			var tb = $('tbody', table);
			this.keys.map(function(key, i) {
				var row = $('<tr></tr>');
				// Show/hide series
				var cbox = $('<input type="checkbox" name="hide" value="'+key+'" />');
				if ($.inArray(key, self.options.hide)==-1) {cbox.attr('checked', true)}
				row.append($('<td></td>').append(cbox));
				// Name
				row.append('<td>'+key+'</td>')
				row.append('<td>'+self.counted[key]+'</td>');
				total += self.counted[key];
				// Colors
				row.append('<td><div class="e2-plot-color" style="background:'+self.scale(i)+'">&nbsp;</div></td>');
				tb.append(row);
			});
			tb.append('<tr class="e2-plot-totals"><td /><td>Total: </td><td>'+total+'</td><td /></tr>');
			controls.append(table);
			this.controls.append(controls);
			this.controls = controls;
			$('input[name=key]', this.controls).val(this.options.key);
			$('input[name=bin]', this.controls).val(this.options.bin);
			this.update_controls();
		},
		
		update_controls: function() {
		}
	});
	
	/***** Base Plotting Control *****/
	
	$.widget('emen2.PlotBase', {
		options: {
			q: null,
			// Padding: top, left, bottom, right
			padding: [10,10,50,50],
			width: 500,
			height: 500,
			// Axis options...
			axopts: null
		},

		_create: function() {
			this.built = 0;
			this.options.width = this.element.width();
			this.height = this.options.height - (this.options.padding[0] + this.options.padding[2]);
			this.width = this.options.width - (this.options.padding[1] + this.options.padding[3]);
			if (this.options.axopts == null) {this.options.axopts = {}}
			// Setup and build
			this.setup();
			this.build();
		},
		
		build: function() {
			if (this.built) {return}
			this.built = 1;
			var self = this;

			// Create the SVG element
			this.svg = d3.select('.e2-plot')
				.append("svg:svg")
				.attr("width", this.options.width) // outer width
				.attr("height", this.options.height) // outer height
				.call(d3.behavior.zoom().on("zoom", function(){self.redraw()}))
				.append("svg:g")
				.attr("transform", 'translate('+this.options.padding[1]+','+this.options.padding[0]+')')

			// Background for plot
			this.svg.append('svg:rect')
				.attr('width', this.width)
				.attr('height', this.height)
				.attr('class', 'e2-plot-bg');

			// Add the x-axis.
			this.svg.append("svg:g")
				.attr("class", "x axis")
				.attr("transform", "translate(0," + this.height + ")")
				.call(this.x.ax);

			// Add the y-axis.
			this.svg.append("svg:g")
				.attr("class", "y axis")
				.attr("transform", "translate(" + this.width + ",0)")
				.call(this.y.ax);

			this.plotarea = this.svg.append("svg:svg")
				.attr('x', 0)
				.attr('y', 0)
				.attr('width', this.width)
				.attr('height', this.height)
				.style('overflow', 'hidden')
				.append('svg:g')
				.attr('class', 'e2-plot-area');

			// Run the query and plot the result
			this.plot(this.options.q['recs'] || []);
			// Build the controls
			this.x.build_controls();
			this.y.build_controls();
			this.z.build_controls();			
		},
		
		setup: function() {
			// Setup axes
			// The jQuery widget factory is too useful not to use.
			var xopts = this.options.axopts['x'] || {};
			var yopts = this.options.axopts['y'] || {};
			var zopts = this.options.axopts['z'] || {};
			xopts['name'] = 'x';
			xopts['binnable'] = true;
			xopts['size'] = [this.width, this.height];
			yopts['name'] = 'y';
			yopts['size'] = [this.height, this.width],
			yopts['orient'] = 'right';
			yopts['invert'] = true;
			zopts['name'] = 'z';
			this.x = $('<div />').AxisControl(xopts).data('AxisControl');
			this.y = $('<div />').AxisControl(yopts).data('AxisControl');
			this.z  = $('<div />').SeriesControl(zopts).data('SeriesControl');
		},
		
		plot: function(q) {
			// Draw the plot
		},
		
		redraw: function() {
			var trans = d3.event.translate;
			var scale = [d3.event.scale, d3.event.scale];
			// d3.event.transform needs to be documented.
			if (this.x.options.pan && this.y.options.pan) {
				d3.event.transform(this.x.scale, this.y.scale);				
			} else if (this.x.options.pan) {
				d3.event.transform(this.x.scale);
				scale[1] = 1;
				trans[1] = 0;
			}
			this.plotarea.attr('transform', 'matrix('+scale[0]+' 0 0 '+scale[1]+' '+trans[0]+' '+trans[1]+')');
			this.svg.select(".x.axis").call(this.x.ax);
			this.svg.select(".y.axis").call(this.y.ax);			
			this.x.redraw();
			this.y.redraw();
		},
		
		update: function() {
			var opts = {};
			opts['x'] = this.x.update();
			opts['y'] = this.y.update();
			opts['z'] = this.z.update();
			return opts
		}
	});	

	/***** Scatter Plot Control *****/

	$.widget('emen2.PlotScatter', $.emen2.PlotBase, {
		plot: function(recs) {	
			var self = this;		
			// Filter the records
			recs = recs.filter(function(d){return (self.x.f(d)!=null && self.y.f(d)!=null)});

			// Bind the data to the axes..?
			this.x.data(recs);
			this.y.data(recs);
			
			// Update the X and Y axis domains
			this.svg.select(".x.axis").call(this.x.ax);
			this.svg.select(".y.axis").call(this.y.ax);

			// Add a group for each cause.
			var groups = this.plotarea.selectAll("g.group")
				.data(this.z.data(recs))
				.enter().append("svg:g")
				.attr("class", "group")
				.style("fill", function(d, i) {return self.z.scale(i)});
			
			// Add a rect for each date.
			var rect = groups.selectAll("circle")
				.data(function(d,i){return d})
				.enter().append("svg:circle")
				.attr("cx", function(d,i) {return self.x.p(d)})
				.attr("cy", function(d,i) {return self.y.p(d)})
				.attr("r", 3);								
		}
	});
	
	
	
	/****************** BAR CHARTS AND HISTOGRAMS ******************/
	
	/***** Bar Chart Control *****/
	
	// $.widget('emen2.BarChartControl', .....
	
	/***** Histogram X Axis Control *****/
	
	$.widget('emen2.HistXControl', $.emen2.AxisControl, {
		setup: function() {
			var self = this;

			// Set the bin method
			this.bin = this.bin_count;

			// Date keys; parse the record timestamps (usually iso8601)
			if (this.options.key == 'creationtime') {
				this.f = function(d) {return new Date(d[self.options.key])};
				this.scale = d3.time.scale();
				this.options.min = null;
				this.options.max = null;
				//if (this.options.min != null) {this.options.min = new Date(this.options.min)}
				//if (this.options.max != null) {this.options.min = new Date(this.options.max)}
			}			
			

			// Display options
			this.ax = d3.svg.axis().scale(this.scale).tickSize(-this.options.size[1],3,0);	
			this.scale.range([0, this.options.size[0]]);
		},
		
		p: function(d) {
			// Map a value to a point
			return this.scale(d.x);
		},		
		
		// Grumble..
		bin_count: function(recs) {
			// This should work by date...?
			var bins = {};
			var keys = [];
			var binwidth = (this.options.max - this.options.min) / this.options.bin;

			// Setup all the bins
			for (var i=0;i<this.options.bin;i++) {
				// grumble... Dates can do subtraction but not addition?
				if (this.options.key == 'creationtime') {
					var bx = new Date(this.options.min.getTime() + (binwidth*i));
				} else {
					var bx = (binwidth * i) + this.options.min;	
				}
				bins[bx]= {'x':bx, 'y': 0, 'yoff': 0, 'ysum': 0}
				keys.push(bx);
			}
			keys.sort(function(a,b){return a-b});

			// Sort all the items into bins
			for (var i=0;i<recs.length;i++) {
				// Get the bin # for this item
				var bx = Math.floor((this.f(recs[i]) - this.options.min) / binwidth);
				if (keys[bx] == null){
					bx = keys.length-1;
				} // closed interval
				bx = keys[bx];
				// Increment the bin
				// console.log(this.f(recs[i]), bx);
				bins[bx].y += 1;
				bins[bx].ysum += 1;
			}
			bins = d3.values(bins);

			// Update settings
			this.keys = keys;
			this.bins = bins;
			this.binwidth = binwidth;
			return bins
		},

		bin_time: function(recs) {
			// Quasi-fixed time bins: year, month, day, hour, minute, second
		}
	});	
	
	/***** Histogram Y Axis Control *****/	
	
	$.widget('emen2.HistYControl', $.emen2.AxisControl, {
		setup: function() {
			this.options.min = 0;
			this.options.pan = false;
			this.options.cumulative = true;
			this.options.stacked = true;
			this.ax = d3.svg.axis().scale(this.scale).tickSize(-this.options.size[1],3,0).orient(this.options.orient);
			this.scale.range([this.options.size[0], 0]);
		},
		
		data: function(recs) {
			// Calculate cumulative and stacked totals and Y domain
			var max_single = 0;
			var max_series = 0;
			var max_stacked = 0;

			// Calculate the cumulative total for each series
			for (var i=0;i<recs.length;i++) {
				var ysum = 0;
				for (var j=0;j<recs[i].length;j++) {
					// Largest single item?
					if (recs[i][j].y > max_single) {max_single = recs[i][j].y}
					// Add to the current series total
					ysum += recs[i][j].y || 0;
					recs[i][j].ysum = ysum;
				}
				// Largest series?
				if (ysum > max_series) {max_series = ysum}
			}
			this.options.max = max_series;
			
			// Stack the series
			if (this.options.stacked) {
				for (var i=1;i<recs.length;i++) {
					for (j=0;j<recs[i].length;j++) {
						recs[i][j].yoff = recs[i-1][j].ysum + recs[i-1][j].yoff;
						// Largest stack?
						if ((recs[i][j].yoff + recs[i][j].ysum) > max_stacked) {
							max_stacked = recs[i][j].yoff + recs[i][j].ysum;
						}
					}
				}
				this.options.max = max_stacked;
			}

			// Update domain
			this.scale.domain([this.options.min, this.options.max]);
		},
		
		build_controls: function() {
			if (!this.controls.length) {return}
			var controls = $('<li></li>');
			controls.append('<h4>'+this.options.name.toUpperCase()+'</h4>');
			controls.append('<div>Record totals<input type="hidden" name="key" value="name" /></div>')
			controls.append('<div><span class="e2-plot-label">Range:</span><input class="e2-plot-bounds" type="text" name="min" /> - <input class="e2-plot-bounds" type="text" name="max" /></div>');
			this.controls.append(controls);
			this.controls = controls;
			this.update_controls();
		},
		
		p: function(d) {
			return d.ysum;
		}
	});
		
	/***** Histogram Plot Control *****/
	
	$.widget('emen2.PlotHistogram', $.emen2.PlotBase, {		
		setup: function() {
			// Axis options
			var xopts = this.options.axopts['x'] || {'key':'name'};
			var yopts = this.options.axopts['y'] || {'key':'name'};
			var zopts = this.options.axopts['z'] || {'key':'rectype'};
			xopts['name'] = 'x';
			xopts['size'] = [this.width, this.height];
			xopts['binnable'] = true;
			if (xopts['bin']==null) {xopts['bin'] = 10}
			yopts['name'] = 'y';
			yopts['size'] = [this.height, this.width],
			yopts['orient'] = 'right';
			yopts['invert'] = true;
			zopts['name'] = 'z';
			this.x = $('<div />').HistXControl(xopts).data('HistXControl');
			this.y = $('<div />').HistYControl(yopts).data('HistYControl');
			this.z  = $('<div />').SeriesControl(zopts).data('SeriesControl');			
		},
		
		plot: function(recs) {	
			// Filter the records
			var self = this;		
			recs = recs.filter(function(d){return (self.x.f(d)!=null && self.y.f(d)!=null)});

			// Calculate the X bounds
			this.x.data(recs);

			// Group by series
			var series = [];
			var b = this.z.data(recs);
			for (var i=0;i<b.length;i++) {
				var b2 = this.x.bin(b[i]);
				series.push(b2);
			}

			// console.log('Series:');
			// console.log(series);
			// console.log(series.length);

			// Update Y axis
			this.y.data(series);

			// Update the X and Y axis domains
			this.svg.select(".x.axis").call(this.x.ax);
			this.svg.select(".y.axis").call(this.y.ax);

			// Add a group for each cause.
			var groups = this.plotarea.selectAll("g.group")
				.data(series)
				.enter().append("svg:g")
				.attr("class", "group")
				.style("fill", function(d, i) {return self.z.scale(i)});

			var bw = this.width / this.x.keys.length;
				
			// Draw a rectangle for each group/bin
			var rect = groups.selectAll("rect")
				.data(Object)
				.enter().append("svg:rect")
				.attr('x', function(d,i) {return self.x.scale(d.x)})
				.attr("width", bw)
				.attr('y', function(d) {return self.y.scale(d.ysum)-(self.height-self.y.scale(d.yoff))})
				.attr('height', function(d) {return self.height-self.y.scale(d.ysum)})
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