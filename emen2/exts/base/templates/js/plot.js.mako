
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
			//self.query();
			self._build([]);
		},
		
		query: function() {
			// Rebuild using a new query
			this.built = 0;
			var self = this;
			// emen2.db('getchildren', [136], function(recs) {
			// 	emen2.db('getrecord', [recs], function(recs) {
			// 		self._build(recs);
			// 	})
			// });
			//	return
			
			// Create query
			var axopts = this.options.axopts || {'x':{}, 'y':{}, 'z':{}};
			var axes = [axopts.x.key, axopts.y.key, axopts.z.key];
			var oq = this.options.q || {};
			var q = {};
			q['c'] = oq['c'] || [];
			q['axes'] = axes;
			q['recs'] = true;
			q['ignorecase'] = oq['ignorecase'];
			
			// Execute the query and build on cb
			emen2.db('query', q, function(q) {
				self.options.q = q;
				self._build(q['recs']);
			});
		},
		
		_build: function(recs) {
			var self = this;	
					
			// Build the controls stub first
			$('.e2-plot-controls', this.element).remove();
			var controls = $('<ul class="e2-plot-controls"></ul>');
			this.element.append(controls);

			// Build the plot
			this.build_plot(recs);

			// Update controls
			controls.append('<li><br /><input type="button" name="update" value="Apply" class="e2l-float-right" /></li>');
			$('input[name=update]', controls).click(function(e){self.update()});

		},
		
		build_plot: function(recs) {
			$('.e2-plot', this.element).remove();
			var plotelem = $('<div class="e2-plot e2l-float-left"></div>');
			var w = this.element.parent().width(); // hack
			plotelem.width(w-300);
			this.element.append(plotelem);		
				
			// Pass along the parent options
			var opts = {};
			opts['controls'] = this;
			opts['recs'] = recs;
			opts['axopts'] = this.options.axopts;

			// Plot type
			var axopts = this.options.axopts || {};
			var xbin = axopts['x'] || {};
			var bin = xbin['bin'];
			if (bin) {
				plotelem.PlotHistogram(opts);
				this.plot = plotelem.data('PlotHistogram');					
			} else {
				plotelem.PlotScatter(opts);
				this.plot = plotelem.data('PlotScatter');				
			}
			
		},
		
		update: function() {
			// Ask the plot to read the controls and update
			// Do we do a complete query and rebuild, or just update?
			this.options.axopts = this.plot.update();
			this.query();
			return
			// var axes = [axopts['x'].key, axopts['y'].key, axopts['z'].key];
			// if (axes[0] != oaxes[0] || axes[1] != oaxes[1] || axes[2] != oaxes[2]) {
				// Full update if an axis param changes
			// } else {
			// 	// Partial update
			// 	this.options.axopts = axopts;
			// 	this.options.q['axes'] = axes;
			// 	this._build(this.options.q);
			// }
		}
	});


	/****************** BASIC CHARTS ******************/

	/***** Base Axis Control *****/

	$.widget('emen2.AxisControl', {
		options: {
			key: 'name',
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
			invert: false,
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
		
		b: function(d,i) {
			return 0
		},
		
		bw: function(d,i) {
			var binwidth = (this.options.max - this.options.min) / this.options.bin;
			return this.options.min + binwidth
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
				var b = $('<div><span class="e2-plot-label">Bin:</span></div>').append(this.build_controls_bin());
				controls.append(b);
			}
			this.controls.append(controls);
			this.controls = controls;
			$('input[name=key]', this.controls).val(this.options.key);
			$('select[name=bin]', this.controls).val(this.options.bin);
			this.update_controls();
		},
		
		build_controls_bin: function() {
			var bin = $('<select name="bin"></select>');
			bin.append('<option value=""></option>');
			var keys = [1, 5, 10, 20, 50, 100, 'year', 'month', 'day', 'hour'];
			keys.map(function(i) {
				bin.append('<option value="'+i+'">'+i+'</option>');
			})
			return bin
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
			opts['bin'] = $('select[name=bin]', this.controls).val();
			if (opts['key'] != this.options.key) {
				return opts
			}
			opts['min'] = $('input[name=min]', this.controls).val();
			opts['max'] = $('input[name=max]', this.controls).val();
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
		
		bin: function(recs) {
			// Take a series of records and bin them into this.keys
			// Create the bins
			// console.log('In Bin, this.keys:', this.keys);
			var bins = {};
			for (var i=0;i<this.keys.length;i++) {
				var bx = this.keys[i];
				if (bins[bx]==null) {
					// console.log('Creating bin: ', bx);
					bins[bx] = {'x':bx, 'y': 0, 'yoff': 0, 'ysum': 0, 'w': 0}
				}
			}			
			// Stuff the records into the bins
			for (var i=0;i < recs.length;i++) {
				var bx = this.b(recs[i]);
				if (bins[bx]==null) {
					console.log('No bin for ', bx);
					// console.log(bins);
				}
				bins[bx].y += 1;
				bins[bx].ysum += 1;
			}
			// Return the sorted bins
			var ret = [];
			for (var i=0;i<this.keys.length;i++) {
				ret.push(bins[this.keys[i]]);
			}
			return ret

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
			this.keys = emen2.util.sortdict(counted);

			// Filter out keys in this.options.hide... 
			// Use map instead of filter to preserve Z colors
			var series = [];
			for (var i=0;i<this.keys.length;i++) {
				if ($.inArray(this.keys[i], this.options.hide)==-1) {
					series.push(bins[this.keys[i]]);
				} else {
					series.push([]);
				}
			}
			return series
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
			$('select[name=bin]', this.controls).val(this.options.bin);
			this.update_controls();
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
			this.x = null;
			this.y = null;
			this.z = null;
			this.built = 0;
			
			if (this.options.axopts == null) {this.options.axopts = {}}
			if (this.options.width == null) {};
			this.options.width = this.element.width()
			this.height = this.options.height - (this.options.padding[0] + this.options.padding[2]);
			this.width = this.options.width - (this.options.padding[1] + this.options.padding[3]);

			// Setup and build
			this.setup();
			this.build();
			this.plot(this.options.recs);

			// Build the controls
			this.x.build_controls();
			this.y.build_controls();
			this.z.build_controls();
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

			if (!recs.length) {
				this.element.append('<p>No records to display</p>');
				return
			}
			
			// Bin into series
			var series = this.z.data(recs);

			// Bind the data to the axes..?
			this.x.data(recs);
			this.y.data(recs);
			
			// Update the X and Y axis domains
			this.svg.select(".x.axis").call(this.x.ax);
			this.svg.select(".y.axis").call(this.y.ax);

			// Add a group for each cause.
			var groups = this.plotarea.selectAll("g.group")
				.data(series)
				.enter().append("svg:g")
				.attr("class", "group")
				.style("fill", function(d, i) {return self.z.scale(i)});
			
			// Add a rect for each date.
			var rect = groups.selectAll("circle")
				.data(function(d,i){return d})
				.enter().append("svg:circle")
				.attr("cx", function(d,i) {return self.x.scale(self.x.f(d))})
				.attr("cy", function(d,i) {return self.y.scale(self.y.f(d))})
				.attr("r", 3);								
		}
	});
	
	
	
	/****************** BAR CHARTS AND HISTOGRAMS ******************/
	
	/***** Bar Chart Control *****/
	
	// $.widget('emen2.BarChartControl', .....
	
	/***** Histogram X Axis Control *****/
	
	$.widget('emen2.HistTimeXControl', $.emen2.AxisControl, {
		setup: function() {
			// Use a year/month/day/hour/minute/second bin
			var self = this;
			this.scale = d3.time.scale();
			this.options.min = null;
			this.options.max = null;
			this.ax = d3.svg.axis().scale(this.scale).tickSize(-this.options.size[1],3,0);	
			this.scale.range([0, this.options.size[0]]);
		},
		
		f: function(d) {
			return new Date(d[this.options.key])
		},
		
		b: function(d) {
			return emen2.time.start(this.f(d), this.options.bin)
		},
		
		bw: function(d,i) {
			// Calculate the start/end points of this interval
			var iv = emen2.time.interval[this.options.bin](d.x);
			// Add the interval width to the minimum time
			var bw = new Date(this.options.min.getTime()+(iv[1]-iv[0]));
			return bw
		},

		data: function(recs) {
			// Extract the sorted keys
			var keys = [];
			for (var i=0;i<recs.length;i++) {
				keys.push(this.f(recs[i]));
			}			
			keys.sort(function(a,b){return a-b});		
			var interval = emen2.time.range(keys[0], keys[keys.length-1], this.options.bin);
			
			// Update the keys
			this.keys = interval;
			this.options.min = this.keys[0];
			this.options.max = this.keys[this.keys.length-1];
			this.scale.domain([this.options.min, this.options.max]);
		}
	});
	
	$.widget('emen2.HistXControl', $.emen2.AxisControl, {
		setup: function() {
			var self = this;
			this.ax = d3.svg.axis().scale(this.scale).tickSize(-this.options.size[1],3,0);	
			this.scale.range([0, this.options.size[0]]);
		},
		
		data: function(recs) {
			// Set the domain from the data
			var keys = {};
			var x = [];
			for (var i=0;i<recs.length;i++) {
				x.push(this.f(recs[i]));
			}
			var min = d3.min(x);
			var max = d3.max(x);			
			// Calculate the bin width and the bin breaks
			var binwidth = (max - min) / this.options.bin;
			var keys = [];
			for (var i=0;i<this.options.bin;i++) {
				keys.push(min+(binwidth*i));
			}
			// Update the keys
			this.keys = keys;
			// Update the domain
			this.options.min = this.keys[0];
			this.options.max = this.keys[this.keys.length-1];
			this.scale.domain([this.options.min, this.options.max]);
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
			// Recs is a dict[series key][x key]
			var max_single = 0;
			var max_series = 0;
			var max_stacked = 0;
			// console.log('Y control data:', recs.length, recs);
			
			// Calculate the cumulative total for each series
			for (var i=0;i<recs.length;i++) {
				// console.log('this series:', recs[i]);
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

			// Stack the series
			var ysum = 0;
			for (var i=1;i<recs.length;i++) {
				for (j=0;j<recs[i].length;j++) {
					recs[i][j].yoff = recs[i-1][j].ysum + recs[i-1][j].yoff;
					// Largest stack?
					if ((recs[i][j].yoff + recs[i][j].ysum) > max_stacked) {
						max_stacked = recs[i][j].yoff + recs[i][j].ysum;
					}
				}
			}
	
			// console.log('Maxes:', max_single, max_series, max_stacked);
			this.options.max = max_single;
			if (this.options.cumulative) {
				this.options.max = max_series;
			}
			if (this.options.stacked) {
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
			yopts['name'] = 'y';
			yopts['size'] = [this.height, this.width],
			yopts['orient'] = 'right';
			yopts['invert'] = true;
			zopts['name'] = 'z';
			
			// X axis is a continuous, either float or time
			//var tbins = ['year', 'month', 'day', 'hour', 'minute', 'second'];
			//if ($.inArray(this.options.bin, tbins)>-1) {
				this.x = $('<div />').HistTimeXControl(xopts).data('HistTimeXControl');
			//} else {
			//	this.x = $('<div />').HistXControl(xopts).data('HistXControl');				
			//}

			// Y axis produces counts for each bin
			this.y = $('<div />').HistYControl(yopts).data('HistYControl');
			
			// Z axis is normal
			this.z  = $('<div />').SeriesControl(zopts).data('SeriesControl');			
		},
		
		plot: function(recs) {	
			// Filter the records
			var self = this;	
			recs = recs.filter(function(d){return (self.x.f(d)!=null)});
			// console.log("Filtered recs:", recs);
			
			// Separate by series key
			var series = this.z.data(recs);

			// Update the X bounds
			this.x.data(recs);

			if (this.x.keys.length > 1000) {
				alert('Too many bins');
				return
			}

			// Group each series into bins
			var series_binned = [];
			for (var i=0;i<series.length;i++) {
				series_binned.push(this.x.bin(series[i]));
			}
			
			// Update Y axis acounts
			this.y.data(series_binned);

			// Update the X and Y axis domains
			this.svg.select(".x.axis").call(this.x.ax);
			this.svg.select(".y.axis").call(this.y.ax);
			// return

			// Add a group for each cause.
			var groups = this.plotarea.selectAll("g.group")
				.data(series_binned)
				.enter().append("svg:g")
				.attr("class", "group")
				.style("fill", function(d, i) {return self.z.scale(i)});
				
			// Draw a rectangle for each group/bin
			var rect = groups.selectAll("rect")
				.data(Object)
				.enter().append("svg:rect")
				.attr('x', function(d) {return self.x.scale(d.x)})
				.attr('y', function(d) {return self.y.scale(d.ysum)-(self.height-self.y.scale(d.yoff))})
				.attr('height', function(d) {return self.height-self.y.scale(d.ysum)})
				.attr("width", function(d) {return self.x.scale(self.x.bw(d))})
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