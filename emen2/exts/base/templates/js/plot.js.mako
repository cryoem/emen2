(function($) {
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
			// Display
			colors: d3.scale.category10(),
			padding: [50,50,50,50], // top, left, bottom, right
			width: null,
			height: null,
		},

		_create: function() {
			this.built = 0;
			this.options.width = $.checkopt(this, 'width', this.element.width()-2);
			this.options.height = $.checkopt(this, 'height', 500);
			this.setup();			
			this.build();
		},
		
		build: function() {
			if (this.built) {return}
			var self = this;
			this.built = 1;

			// Create the SVG element
			this.svg = d3.select("#chart").append("svg:svg")
				.attr("width", this.options.width)
				.attr("height", this.options.height)
				.append("svg:g")
				.attr("transform", 'translate('+this.options.padding[1]+','+this.options.padding[0]+')');

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

		update_bounds: function(xmin, xmax, ymin, ymax) {
			// Update bounds
			this.options.xmin = (this.options.xmin == null) ? xmin : this.options.xmin;
			this.options.xmax = (this.options.xmax == null) ? xmax : this.options.xmax;
			this.options.ymin = (this.options.ymin == null) ? ymin : this.options.ymin;
			this.options.ymax = (this.options.ymax == null) ? ymax : this.options.ymax;
		},
		
		draw_label: function(axis, format, ticks) {
			// Draw plot lines and labels
			var format = format || d3.format('.3r');
			var ticks = ticks || 10;
			var self = this;
	
			// axis is 'x', 'y'
			var textanchor = 'middle';
			var d1 = 0;
			var d2 = '1.3em';
			var scale = this[axis];
			var otheraxis = 'y';
			var otherscale = this[otheraxis]
			if (axis == 'y') {
				otheraxis = 'x';
				otherscale = this[otheraxis];
				d1 = '0.3em';
				d2 = '0.3em';
				textanchor = '';			
			}
			
			// Draw labels for this axis
			this.svg.selectAll("text.label"+axis)
				.data(scale.ticks(ticks))
				.enter()
				.append("svg:text")
				.attr(axis, function(d) {return scale(d)})
				.attr(otheraxis, otherscale.range()[1])
				.attr('d'+axis, d1)
				.attr('d'+otheraxis, d2)
				.attr('text-anchor', textanchor)
				.text(format)

			this.svg.selectAll("g.tick"+axis)
				.data(scale.ticks(ticks))
				.enter()
				.append("svg:line")
				.attr(axis+"1", function(d) {return scale(d)})
				.attr(axis+"2", function(d) {return scale(d)})
				.attr(otheraxis+"1", 0)
				.attr(otheraxis+"2", otherscale.range()[1])
				.style("stroke", '#eee');

			this.svg.append("svg:line")
				.attr(axis+'1', 0)
				.attr(axis+'2', scale.range()[1])
				.attr(otheraxis+'1', otherscale.range()[1])
				.attr(otheraxis+'2', otherscale.range()[1])
				.style("stroke", 'black');
		}
		
	});	

	$.widget('emen2.PlotScatter', $.emen2.PlotBase, {
		query: function(cb) {
			$.jsonRPC.call('getchildren', [419869], function(recs) {
				$.jsonRPC.call('getrecord', [recs], function(recs) {
					$.updatecache(recs);
					cb(recs);
				})
			});
		},
		
		plot: function(recs) {
			var self = this;
			var h = this.options.height - (this.options.padding[0] + this.options.padding[2]);
			var w = this.options.width - (this.options.padding[1] + this.options.padding[3]);
			
			// Filter the records
			recs = recs.filter(function(d){return (self.fx(d)!=null && self.fy(d)!=null)});
			var bxs = recs.map(function(d) {return self.fx(d)});
			var bys = recs.map(function(d) {return self.fy(d)});
			
			this.update_bounds(d3.min(bxs), d3.max(bxs), d3.min(bys), d3.max(bys))
			
			// Plot
			this.x = d3.scale.linear()
				.domain([this.options.xmin, this.options.xmax])
				.nice()
				.range([0,w]);
			this.y = d3.scale.linear()
				.domain([this.options.ymin, this.options.ymax])
				.nice()
				.range([0,h]);
			this.z = this.options.colors;	

			// Add the labels
			this.draw_label('x');
			this.draw_label('y');
			
			// Add a point for each item.
			var rect = this.svg.selectAll("circle")
				.data(recs)
				.enter().append("svg:circle")
				.attr("cx", function(d,i) { return self.x(self.fx(d))})
				.attr("cy", function(d,i) { return self.y(self.fy(d))})
				.attr('r', 3)
				.attr('data-z', function(d,i) {return self.fz(d)})
				.style('fill', function(d,i) {return self.z(i)})
		}
	});

	// Time bar chart
	$.widget('emen2.PlotTime', $.emen2.PlotBase, {
		setup: function() {
			// Additional options
			this.options.cumulative = true;
			this.options.stacked = true;
			this.options.xlabelorient = 'horizontal';
			this.options.bin = 'month';
			// Set formats and interval generator
			if (this.options.bin == 'year') {
				this.d3x = d3.time.year;
				this.d3xs = d3.time.years;
				this.format = d3.time.format("%Y");
			} else if (this.options.bin == 'month') {
				this.d3x = d3.time.month;
				this.d3xs = d3.time.months;
				this.format = d3.time.format("%Y-%m");
			} else if (this.options.bin == 'day') {
				this.d3x = d3.time.day;
				this.d3xs = d3.time.days;
				this.format = d3.time.format("%Y-%m-%d");
			}			
		},
		
		fx: function(d) {
			var bx = new Date(d[this.options.xkey]);
			return this.d3x(bx)
		},

		group: function(recs) {
			// 1. Group
			var self = this;
			var bins = {};
			var xkeys = {};
			var ykeys = {};
			var zkeys = {};
			recs.map(function(d) {
				var bz = self.fz(d);
				var bx = self.fx(d);
				xkeys[bx] = bx;
				zkeys[bz] = bz;
				if (bins[bz] == null) {
					bins[bz] = {}
				}
				if (bins[bz][bx] == null) {
					bins[bz][bx] = {x:bx, y:0, ysum:0, yoff:0}
				}
				bins[bz][bx].y += 1
			});
			
			// 2. Setup domains
			// 		X domain
			var xkeys = d3.values(xkeys);
			xkeys.sort(function(a,b){return a-b});
			var xmin = this.d3x(xkeys[0]);
			var xmax = xkeys[xkeys.length-1];			
			var bxs = this.d3xs(xmin, xmax); // grumble..
			
			// 		Y domain
			var ykeys = d3.values(ykeys);
			ykeys.sort();
			var ymin = 0;
			var ymax = 0;
			var bys = [];

			// 		Z domain
			var zkeys = d3.values(zkeys);
			// todo: sort by highest total sum to lowest
			// zkeys.sort();
			
			// Temporary, I try to avoid undocumented attributes
			this.xkeys = xkeys;
			this.ykeys = ykeys;
			this.zkeys = zkeys;
			
			// 3. Update sums based on options and min/max
			// 		If cumulative
			if (this.options.cumulative) {
				zkeys.map(function(bz) {
					var ysum = 0;
					bxs.map(function(bx) {
						var item = bins[bz][bx];
						if (item) {
							ysum += item.y;
							item.ysum = ysum;
						} 
						else {
							bins[bz][bx] = {x:bx, y:0, ysum: ysum, yoff:0}
						}
					});
					if (ysum > ymax) {ymax = ysum}
				});
			}
			// 		If stacked
			if (this.options.stacked) {
				bxs.map(function(bx) {
					var yoff = 0;
					zkeys.map(function(bz) {
						var item = bins[bz][bx];
						if (item) {
							item.yoff = yoff;
							yoff += item.ysum
						}
					});
					if (yoff > ymax) {ymax = yoff}
				});	
			}
			
			// 4. Update options
			if (this.options.xmin==null) {this.options.xmin = xmin}
			if (this.options.xmax==null) {this.options.xmax = xmax}
			if (this.options.ymin==null) {this.options.ymin = ymin}
			if (this.options.ymax==null) {this.options.ymax = ymax}
			
			return bins			
		},
		
		plot: function(recs) {
			var self = this;
			var width = this.element.width()-2;
			var height = 600;
			var p = [10,100,100,10]; // top padding, right padding, bottom padding, left padding
			var bins = this.group(recs);
			
			// Plot
			this.x = d3.time.scale().domain([this.options.xmin, this.options.xmax]).range([0,width-p[1]-p[3]]);
			this.y = d3.scale.linear().domain([this.options.ymin, this.options.ymax]).range([0,height-p[0]-p[2]]);
			this.z = this.options.colors; 
			var barwidth = width / d3.time.months(this.options.xmin, this.options.xmax).length;

			// Add a group for each cause.
			var cause = this.svg.selectAll("g.cause")
			    .data(this.zkeys)
			  .enter().append("svg:g")
			    .attr("class", "cause")
				.attr('data-bz', function(d,i) {return self.zkeys[i]})
			    .style("fill", function(d, i) {return self.z(i)})
			    .style("stroke", function(d, i) {return d3.rgb(self.z(i))});

			// Add a rect for each date.
			var rect = cause.selectAll("rect")
			    .data(function(d){return d3.values(bins[d])})
			  .enter().append("svg:rect")
			    .attr("x", function(d) { return self.x(d.x)})
			    .attr("y", function(d) { return height-self.y(d.ysum)-self.y(d.yoff) })
			    .attr("height", function(d) { return self.y(d.ysum) })
			    .attr("width", barwidth);

			// if (this.options.xlabelorient == 'horizontal') {
			// 	label.attr("x", function(d) {return self.x(d)})
			// 		.attr("y", height)
			// 		.attr('dy', '1em')
			// 	    .attr("text-anchor", "middle")				
			// } else if (this.options.xlabelorient == 'vertical'){
			// 	label.attr('transform','rotate(90)')
			// 		.attr("y", function(d) {return -self.x(d)})
			// 		.attr("x", height)
			// 		.attr('dx', 6)
			// }

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