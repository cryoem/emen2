(function($) {
   $.widget('emen2.PlotBase', {
		options: {
			q: null,
			// Axes
			xkey: 'name',
			ykey: 'name',
			zkey: 'rectype',
			// Bounds
			xmin: null,
			xmax: null,
			ymin: null,
			ymax: null,
			// Display
			xticks: 10,
			yticks: 10,
			colors: d3.scale.category10(),
			padding: [50,50,50,50], // top, left, bottom, right
			width: null,
			height: null,
			xformat: Object,
			yformat: Object,
			// Bar chart / histogram options
			cumulative: true,
			stacked: true,
			bin: 'month',			
		},

		_create: function() {
			this.built = 0;
			this.options.width = $.checkopt(this, 'width', this.element.width()-2);
			this.options.height = $.checkopt(this, 'height', 600);

			// Axes
			this.x = d3.scale.linear();
			this.y = d3.scale.linear();
			this.z = this.options.colors;	

			// Keys
			this.xkeys = [];
			this.ykeys = [];
			this.zkeys = [];
			
			// Setup and build
			this.setup();			
			this.build();
		},
		
		build: function() {
			if (this.built) {return}
			var self = this;
			this.built = 1;

			// Account for padding in the output ranges
			var h = this.options.height - (this.options.padding[0] + this.options.padding[2]);
			var w = this.options.width - (this.options.padding[1] + this.options.padding[3]);
			this.x.range([0,w]);
			this.y.range([h,0]); // flip the coordinates on the Y axis
			
			// Create the SVG element
			this.svg = d3.select("#chart").append("svg:svg")
				.attr("width", this.options.width)
				.attr("height", this.options.height)
				.append("svg:g")
				.attr("transform", 'translate('+this.options.padding[1]+','+this.options.padding[0]+')');

			// Run the query and plot the result
			this.query(function(q){self.plot(q)});
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
	
		setup: function() {
			// Subclass init
			var dfunc = function(d) {
				var bx = new Date(d[this.options.xkey]);
				return bx
			}
			if (this.options.xkey == 'creationtime') {
				this.fx = dfunc;
				this.x = d3.time.scale();
				this.options.xformat = d3.time.format("%Y-%m-%d");
			}
		},
		
		plot: function(q) {
			// Draw the plot
		},
		
		controls: function() {
			// Draw the plot controls
		},
		
		redraw: function() {
			// Update the plot
		},

		draw_label: function(axis, format) {
			// Draw plot lines and labels
			// axis is 'x', 'y'
			var format = format || d3.format('.3r');
			var self = this;	
			var textanchor = 'middle';
			var scale = this[axis];
			var otheraxis = 'y';
			var otherscale = this[otheraxis];
			var dx = 0;
			var dy = '1.3em';
			if (axis == 'y') {
				otheraxis = 'x';
				otherscale = this[otheraxis];
				dx = '0.3em';
				dy = '0.3em';
				textanchor = 'start';
			}
			// Find the end point side of the other axis..
			var offset = d3.max(otherscale.range());
			// var offset = otherscale.range()[0];
			var ticks = this.options[axis+'ticks'];

			// Draw labels for this axis
			this.svg.selectAll("text.label"+axis)
				.data(scale.ticks(ticks))
				.enter()
				.append("svg:text")
				.attr(axis, function(d) {return scale(d)})
				.attr(otheraxis, offset) // hack
				.attr('dx', dx)
				.attr('dy', dy)
				.attr('text-anchor', textanchor)
				.text(this.options[axis+'format']);

			// Rules
			this.svg.selectAll("g.tick"+axis)
				.data(scale.ticks(ticks))
				.enter()
				.append("svg:line")
				.attr(axis+"1", function(d) {return scale(d)})
				.attr(axis+"2", function(d) {return scale(d)})
				.attr(otheraxis+"1", 0)
				.attr(otheraxis+"2", offset)
				.style("stroke", '#eee');

			// Bold baseline
			this.svg.append("svg:line")
				.attr(axis+'1', 0)
				.attr(axis+'2', d3.max(scale.range()))
				.attr(otheraxis+'1', offset)
				.attr(otheraxis+'2', offset)
				.style("stroke", 'black');
		},
		
		group: function(recs) {
			// Histograms group on two axes and replace the X with totals
			// See PlotHistogram
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
			
			// Update the keys attributes
			this.xkeys = xkeys;
			this.ykeys = ykeys;
			this.zkeys = zkeys;
			
			// Update options
			if (this.options.xmin==null) {this.options.xmin = xmin}
			if (this.options.xmax==null) {this.options.xmax = xmax}
			if (this.options.ymin==null) {this.options.ymin = ymin}
			if (this.options.ymax==null) {this.options.ymax = ymax}
			
			return bins			
		}		
	});	

	$.widget('emen2.PlotScatter', $.emen2.PlotBase, {
		query: function(cb) {
			// var c = [['rectype'], ['ctf_bfactor'], ['ctf_defocus_measured']];
			// $.jsonRPC.call('query', [c], function(q) {
			// 	console.log(q['recs'].length);
			// 	cb(q['recs']);
			// });
			$.jsonRPC.call('getchildren', [419869], function(recs) {
				$.jsonRPC.call('getrecord', [recs], function(recs) {
					$.updatecache(recs);
					cb(recs);
				})
			});
		},
		
		plot: function(recs) {
			var self = this;
			
			// Filter the records
			recs = recs.filter(function(d){return (self.fx(d)!=null && self.fy(d)!=null)});
			// Group by Z key
			var bins = this.group(recs);

			// Update the X and Y axis domains
			this.x.domain([this.options.xmin, this.options.xmax]);
			this.y.domain([this.options.ymin, this.options.ymax]);

			// Add the labels
			this.draw_label('x');
			this.draw_label('y');
			
			// Add a group for each cause.
			var groups = this.svg.selectAll("g.group")
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
		}
	});
	
	$.widget('emen2.PlotHistogram', $.emen2.PlotBase, {
		group_bin: function(recs) {
			var bins = this.group(recs);
			var xks = d3.time[this.options.bin+'s'](this.options.xmin, this.options.xmax);// hack
			var xbins = {};
			
			return bins			
		},

		setup: function() {
			if (this.options.xkey != 'creationtime') {
				return
			}
		
			var self = this;
			// Subclass init
			var dfunc = function(d) {
				var bx = new Date(d[self.options.xkey]);
				return d3.time[self.options.bin](bx)
			}

			this.fx = dfunc;
			this.x = d3.time.scale();
			this.options.xformat = d3.time.format("%Y-%m-%d");

		},
	
		fx: function(d) {
			var bx = new Date(d[this.options.xkey]);
			return this.d3x(bx)
		},

		plot: function(recs) {
			this.group_bin(recs);
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