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
			// Padding: top, left, bottom, right
			padding: [10,10,50,50], 
			width: null,
			height: null,
			// Bar chart / histogram options
			cumulative: true,
			stacked: true,
			bin: 'month',			
		},

		_create: function() {
			this.built = 0;
			this.options.width = $.checkopt(this, 'width', this.element.width()); // -300
			this.options.height = $.checkopt(this, 'height', 600);
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

			// this.build_controls();

			// Account for padding in the output ranges
			var h = this.options.height - (this.options.padding[0] + this.options.padding[2]);
			var w = this.options.width - (this.options.padding[1] + this.options.padding[3]);
			this.x.range([0,w]);
			this.y.range([h,0]); // flip the coordinates on the Y axis

			// Create the SVG element
			this.svg = d3.select("#chart").append("svg:svg")
				.attr("width", this.options.width)
				.attr("height", this.options.height)
				.call(d3.behavior.zoom().on("zoom", function(){self.redraw()}))
				.append("svg:g")
				.attr("transform", 'translate('+this.options.padding[1]+','+this.options.padding[0]+')')

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

			this.plotarea = this.svg.append("svg:g")
				.attr('class', 'e2-plot-area');

			// Run the query and plot the result
			this.query(function(q){self.plot(q)});
		},
		
		setup: function() {
			// Setup axes
			var h = this.options.height - (this.options.padding[0] + this.options.padding[2]);
			var w = this.options.width - (this.options.padding[1] + this.options.padding[3]);			
			this.x = d3.scale.linear().domain([0,0]);
			this.y = d3.scale.linear().domain([0,0]);
			this.z = this.options.colors;

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
		
		build_controls: function() {
			// Draw the plot controls
			var t = $(' \
				<ul class="e2-plot-table"> \
					<li><select name="xkey"><option value="">X Parameter</option></select></li> \
					<li><select name="ykey"><option value="">Y Parameter</option></select></li> \
					<li><select name="zkey"><option value="">Z Parameter</option></select></li> \
					<li>X min: <input name="xmin" /></li> \
					<li>X max: <input name="xmax" /></li> \
					<li>Y min: <input name="ymin" /></li> \
					<li>Y max: <input name="ymax" /></li> \
				</ul>');
			this.element.append(t);
		},
		
		redraw: function() {
			// Update the plot
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
		query: function(cb) {
			$.jsonRPC.call('getchildren', [419869], function(recs) {
				$.jsonRPC.call('getrecord', [recs], function(recs) {
					$.updatecache(recs);
					cb(recs);
				})
			});
			return
			var c = [['rectype'], ['ctf_bfactor'], ['ctf_defocus_measured']];
			$.jsonRPC.call('query', [c], function(q) {
				cb(q['recs']);
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

			console.log(this.x.domain());

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
		}
		
		
	});
	
	$.widget('emen2.PlotHistogram', $.emen2.PlotBase, {
		group_bin: function(recs) {
			var self = this;
			var bins = this.group(recs);
			var sbins = {};
			
			// Get sorted ordinal names from date range
			var xks = d3.time[this.options.bin+'s'](d3.time.month(this.options.xmin), this.options.xmax);
			this.options.ymax = 0;
			
			// Setup the histogram
			this.zkeys.map(function(z) {
				sbins[z] = {};
				xks.map(function(x) {
					sbins[z][x] = {x:x, y:0, ysum:0, yoff:0}
				})
				d3.values(bins[z]).map(function(d) {
					var x = d3.time.month(self.fx(d));
					sbins[z][x].y += 1
				});
			});

			// Cumulative
			if (this.options.cumulative) {
				this.zkeys.map(function(z) {
					var ysum = 0;
					xks.map(function(x) {
						ysum += sbins[z][x].y || 0;
						sbins[z][x].ysum = ysum;
					});
					console.log(ysum);
					if (ysum > self.options.ymax) {self.options.ymax = ysum}
				});
			}
			if (this.options.stacked) {
				xks.map(function(x) {
					var yoff = 0;
					self.zkeys.map(function(z) {
						sbins[z][x].yoff = yoff;
						yoff += sbins[z][x].ysum;
					});
					if (yoff > self.options.ymax) {self.options.ymax = yoff}				
				});
			}

			console.log(this.options.ymax);

			return sbins			
		},

		fx: function(d) {
			var bx = new Date(d[this.options.xkey]);
			return d3.time.months(bx);
		},

		plot: function(recs) {
			var bins = this.group_bin(recs);

			// // Add a group for each cause.
			// var groups = this.plotarea.selectAll("g.group")
			// 	.data(this.zkeys)
			// 	.enter().append("svg:g")
			// 	.attr("class", "group")
			// 	.attr('data-bz', function(d,i) {return self.zkeys[i]})
			// 	.style("fill", function(d, i) {return self.z(i)})
			// 	.style("stroke", function(d, i) {return d3.rgb(self.z(i))});			
			
			// Add a rect for each date.
			// var rect = groups.selectAll("circle")
			// 	.data(function(d){return d3.values(bins[d])})
			// 	.enter().append("svg:circle")
			// 	.attr("cx", function(d,i) {return self.x(self.fx(d))})
			// 	.attr("cy", function(d,i) {return self.y(self.fy(d))})
			// 	.attr('data-x', function(d) {return self.fx(d)})
			// 	.attr('data-y', function(d) {return self.fy(d)})					
			// 	.attr('data-z', function(d) {return self.fz(d)})
			// 	.attr("r", 3);			
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