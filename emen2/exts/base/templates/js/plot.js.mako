(function($) {
	
	/***** Plot Controller *****/

	$.widget('emen2.PlotControl', {
		options: {
			q: null
		},
		
		_create: function() {
			this.built = 0;
			// Check the query
			if (this.options.q == null) {this.options.q = {}}
			if (this.options.q['x'] == null) {this.options.q['x'] = {}}
			if (this.options.q['y'] == null) {this.options.q['y'] = {}}
			if (this.options.q['z'] == null) {this.options.q['z'] = {}}
			var recs = this.options.q['recs'] || [];
			this.build(recs);
		},
		
		build: function(recs) {
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
			plotelem.width(w-300); // hack
			this.element.append(plotelem);		
				
			// Pass along the parent options
			var opts = {};
			opts['controls'] = this;
			opts['recs'] = recs;
			opts['x'] = this.options.q['x'];
			opts['y'] = this.options.q['y'];
			opts['z'] = this.options.q['z'];
			var bin = this.options.q['x']['bin'];
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
			var opts = this.plot.update();
			var x = opts['x'];
			var y = opts['y'];
			var z = opts['z'];
			var q = this.options.q;

			// This is a temporary hack.
			if (q['x']['key'] == null) {q['x']['key'] = 'name'}
			if (q['y']['key'] == null) {q['y']['key'] = 'name'}
			if (q['z']['key'] == null) {q['z']['key'] = 'rectype'}
			// console.log('x:', x['key'], ':', q['x']['key']);
			// console.log('y:', y['key'], ':', q['y']['key']);
			// console.log('z:', z['key'], ':', q['z']['key']);
			
			var query = (x['key'] != q['x']['key'] || y['key'] != q['y']['key'] || z['key'] != q['z']['key']);
						
			// Update the query options
			this.options.q['x'] = x;
			this.options.q['y'] = y;
			this.options.q['z'] = z;							

			// If any of the axis keys change, do a full update;
			if (query) {
				this.query()
			} else {
				var recs = this.options.q['recs'] || [];
				this.build(recs);
			}
		},

		query: function() {
			var self = this;
			this.built = 0;

			// Copy the query
			var newq = {};
			var c = ['c', 'ignorecase', 'x', 'y', 'z'];
			c.map(function(key){
				newq[key] = self.options.q[key];
			});
			
			// Create query
			emen2.db('plot', newq, function(q) {
				self.options.q = q;
				self.build(q['recs']);
			});
		},		
	});


	/****************** BASIC CHARTS ******************/

	/***** Base Axis Control *****/

	$.widget('emen2.AxisControl', {
		options: {
			// Main options
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
			
			// If we're switching keys, the other options are irrelevant
			opts['key'] = $('input[name=key]', this.controls).val();
			opts['bin'] = $('select[name=bin]', this.controls).val();
			if (opts['key'] != this.options.key) {
				return opts
			}
			
			// Update other options
			opts['min'] = $('input[name=min]', this.controls).val();
			opts['max'] = $('input[name=max]', this.controls).val();

			opts['cumulative'] = Boolean($('input[name=cumulative]', this.controls).attr('checked'));
			opts['stacked'] = Boolean($('input[name=stacked]', this.controls).attr('checked'));

			// Hide these series
			opts['hide'] = $("input[name=hide]:not(:checked)", this.controls).map(function(){return $(this).val()});
			return opts
		},
		
		data: function(recs) {
			// Set the domain from the data
			var x = [];
			for (var i=0;i<recs.length;i++) {
				x.push(this.f(recs[i]));
			}
			
			// If bounds weren't specified, update.
			if (this.options.min == null) {this.options.min = d3.min(x)}
			if (this.options.max == null) {this.options.max = d3.max(x)}
			this.scale.domain([this.options.min, this.options.max]);
		},
		
		bin: function(recs) {
			// Create the bins
			var bins = {};
			for (var i=0;i<this.keys.length;i++) {
				var bx = this.keys[i];
				if (bins[bx]==null) {
					// console.log('Creating bin: ', bx);
					bins[bx] = {'x':bx, 'y': 0, 'yoff': 0, 'ysum': 0, 'w': 0}
				}
			}			
			// Stuff the records into the bins
			for (var i=0;i<recs.length;i++) {
				var bx = this.b(recs[i]);
				// if (bins[bx]==null) {
				// 	console.log('No bin for ', bx);
				// }
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
			// Padding: top, left, bottom, right
			padding: [20,20,50,50],
			width: 600,
			height: 600,
			pan: true
		},

		_create: function() {
			this.built = 0;
			
			// Check size options
			if (this.options.width == null) {};
			this.options.width = this.element.width()
			this.height = this.options.height - (this.options.padding[0] + this.options.padding[2]);
			this.width = this.options.width - (this.options.padding[1] + this.options.padding[3]);

			// Setup axes
			var q = this.options.q
			if (q.x == null) {q.x = {}};
			if (q.y == null) {q.y = {}};
			if (q.z == null) {q.z = {}};
			this.x = null;
			this.y = null;
			this.z = null;

			// Subclass init and build
			this.setup();
			this.build();
			this.plot(q.recs);

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
				.append("svg:g")
				.attr("transform", 'translate('+this.options.padding[1]+','+this.options.padding[0]+')')

			// Support panning/zooming
			if (this.options.pan) {
				this.svg.call(d3.behavior.zoom().on("zoom", function(){self.redraw()}))
			}

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

			// Plot background and plot area
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
			var q = this.options.q;
			var x = q.x;
			var y = q.y;
			var z = q.z;
			if (!x['key']) {x['key'] = 'name'}
			if (!y['key']) {y['key'] = 'name'}
			if (!z['key']) {z['key'] = null}
			x['name'] = 'x';
			x['binnable'] = true;
			x['size'] = [this.width, this.height];
			
			y['name'] = 'y';
			y['size'] = [this.height, this.width],
			y['orient'] = 'right';
			y['invert'] = true;
			
			z['name'] = 'z';
			
			// The jQuery widget factory is too useful not to use.
			this.x = $('<div />').AxisControl(x).data('AxisControl');
			this.y = $('<div />').AxisControl(y).data('AxisControl');
			this.z  = $('<div />').SeriesControl(z).data('SeriesControl');
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
				this.element.empty();
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
			
			// Add a circle for each date.
			var rect = groups.selectAll("circle")
				.data(function(d,i){return d})
				.enter().append("svg:circle")
				.attr("cx", function(d,i) {return self.x.scale(self.x.f(d))})
				.attr("cy", function(d,i) {return self.y.scale(self.y.f(d))})
				.attr("r", 3);								
		}
	});

	/***** Line Chart Control *****/

	$.widget('emen2.PlotLine', $.emen2.PlotBase, {
		plot: function(recs) {	
			var self = this;		
			// Filter the records
			recs = recs.filter(function(d){return (self.x.f(d)!=null && self.y.f(d)!=null)});
			if (!recs.length) {
				this.element.empty();
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

			// Add a path for each cause.
			var groups = this.plotarea.selectAll("g.group")
				.data(series)
				.enter().append("svg:path")
				.attr('class', 'line')
				.attr('fill', 'none')
				.attr('stroke', 'red')
				.attr('stroke-width', 2)
				.attr('d', d3.svg.line()
					.x(function(d) {return self.x.scale(self.x.f(d))})
					.y(function(d) {return self.y.scale(self.y.f(d))})
				);

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
			this.scale = d3.time.scale(); //.utc();
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
			
			// Update the options
			if (this.options.min) {
				this.options.min = new Date(this.options.min)
			} else {
				this.options.min = this.keys[0];
			}
			if (this.options.max) {
				this.options.max = new Date(this.options.max)
			} else {
				this.options.max = this.keys[this.keys.length-1];				
			}
			
			// Scale the axis
			// console.log('scale?', this.options.min, this.options.max);
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
			
			// console.log('cumulative/stacked:', this.options.cumulative, this.options.stacked);

			// Find the highest single bin
			for (var i=0;i<recs.length;i++) {
				for (var j=0;j<recs[i].length;j++) {
					// Largest single item?
					if (recs[i][j].y > max_single) {max_single = recs[i][j].y}
				}
			}
			
			// Calculate the cumulative total for each series
			if (this.options.cumulative) {
				for (var i=0;i<recs.length;i++) {
					// console.log('this series:', recs[i]);
					var ysum = 0;
					for (var j=0;j<recs[i].length;j++) {
						// Add to the current series total
						ysum += recs[i][j].y || 0;
						recs[i][j].ysum = ysum;
					}
					// Largest series?
					if (ysum > max_series) {max_series = ysum}
				}
			}
			
			// Stack the series
			if (this.options.stacked) {
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
			}
			
			// for (var i=0;i<recs.length;i++) {console.log(recs[i])}
			// console.log('Maxes:', max_single, max_series, max_stacked);
			this.options.max = max_single;
			if (this.options.cumulative) {
				this.options.max = max_series;
			}
			if (this.options.stacked) {
				this.options.max = max_stacked;
			}

			// Bug.. Stacked doesn't work if only 1 series. Fix!
			// console.log('Y max single/series/stacked', max_single, max_series, max_stacked);
			if (max_single > this.options.max) {this.options.max = max_single}

			// Update domain
			this.scale.domain([this.options.min, this.options.max]);
		},
		
		build_controls: function() {
			if (!this.controls.length) {return}
			var controls = $('<li></li>');
			controls.append('<h4>'+this.options.name.toUpperCase()+'</h4>');
			controls.append('<div><span class="e2-plot-label">Totals</span><input class="e2-plot-bounds" type="text" name="key" value="name" /></div>')
			controls.append('<div><span class="e2-plot-label">Range:</span><input class="e2-plot-bounds" type="text" name="min" /> - <input class="e2-plot-bounds" type="text" name="max" /></div>');
			controls.append('<div><input type="checkbox" name="cumulative" id="e2-plot-y-cumulative" /><label for="e2-plot-y-cumulative">Cumulative</label></div>');
			controls.append('<div><input type="checkbox" name="stacked" id="e2-plot-y-stacked" /><label for="e2-plot-y-stacked">Stacked</label></div>');
			
			$('input[name=cumulative]', controls).attr('checked', this.options.cumulative);
			$('input[name=stacked]', controls).attr('checked', this.options.stacked);

			this.controls.append(controls);
			this.controls = controls;
			this.update_controls();
		}
	});
		
	/***** Histogram Plot Control *****/
	
	$.widget('emen2.PlotHistogram', $.emen2.PlotBase, {		
		setup: function() {
			// Axis options
			var q = this.options.q;
			var x = q.x;
			var y = q.y;
			var z = q.z;
			if (!x['key']) {x['key'] = 'name'}
			if (!y['key']) {y['key'] = 'name'}
			if (!z['key']) {z['key'] = ''}
			
			x['name'] = 'x';
			x['size'] = [this.width, this.height];
			x['binnable'] = true;
			
			y['name'] = 'y';
			y['size'] = [this.height, this.width],
			y['orient'] = 'right';
			y['invert'] = true;

			z['name'] = 'z';
			
			// X axis is a continuous, either float or time
			var tbins = ['year', 'month', 'day', 'hour', 'minute', 'second'];
			if ($.inArray(x['bin'], tbins) > -1) {
				this.x = $('<div />').HistTimeXControl(x).data('HistTimeXControl');
			} else {
				this.x = $('<div />').HistXControl(x).data('HistXControl');				
			}

			// Y axis produces counts for each bin
			this.y = $('<div />').HistYControl(y).data('HistYControl');
			
			// Z axis, regular series control
			this.z  = $('<div />').SeriesControl(z).data('SeriesControl');			
		},
		
		plot: function(recs) {	
			// Filter the records
			var self = this;	
			recs = recs.filter(function(d){return (self.x.f(d)!=null)});

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

			// console.log("X keys:", this.x.keys);
			// console.log("Y keys:", this.y.keys);
			// console.log("Z keys:", this.z.keys);
			// console.log("Series:", series);
			// console.log("Series binned:", series_binned);

			// Update the X and Y axis domains
			this.svg.select(".x.axis").call(this.x.ax);
			this.svg.select(".y.axis").call(this.y.ax);
			// return

			// Add a group for each cause.
			var groups = this.plotarea.selectAll("g.group")
				.data(series_binned)
				.enter().append("svg:g")
				.attr("class", "group")
				.attr('data-z', function(d, i) {return self.z.keys[i]})
				.attr('data-length', function(d, i) {return series[i].length})
				.style("fill", function(d, i) {return self.z.scale(i)});
				
			// Draw a rectangle for each group/bin
			var rect = groups.selectAll("rect")
				.data(Object)
				.enter().append("svg:rect")
				// .attr('data-x', function(d) {return d.x})
				// .attr('data-y', function(d) {return d.ysum})
				.attr("width", function(d) {
					return self.x.scale(self.x.bw(d))
					})
				.attr('height', function(d) {
					// self.y(0) == self.height
					// self.y(max domain) == 0
					return self.height - self.y.scale(d.ysum)
					})
				.attr('x', function(d) {
					return self.x.scale(d.x)}
					)
				.attr('y', function(d) {
					// Height is in pixels below the Y coordinate:
					// 	set Y coordinate to the top of the box
					return self.y.scale(d.ysum) - (self.height-self.y.scale(d.yoff))
					})
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