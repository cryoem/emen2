(function($) {
   $.widget('emen2.PlotBase', {
		options: {
			q: null,
			xmin: null,
			xmax: null,
			ymin: null,
			ymax: null,
			zkey: 'rectype',
			xkey: 'creationtime',
			ykey: 'name',
			colors: d3.scale.category10()
		},

		_create: function() {
			this.built = 0;
			this.build();
		},
		
		fx: function(d) {
			return d[this.options.xkey]
		},
		
		fy: function(d) {
			return d[this.options.ykey]
		},
		
		fz: function(d) {
			return d[this.options.zkey]
		},

		build: function() {
			if (this.built) {return}
			var self = this;
			this.built = 1;
			this.element.append('<div id="fig"></div>');
			this.query(function(q){self.plot(q)});
		},
		
		queryfake: function(cb) {
			var count = 1000;
			var data = [];
			var rectypes = ['ccd','stack','micrograph'];
			function next() {
				var month = Math.floor(Math.random()*13);
				var day = Math.floor(Math.random()*30)+1;
				var rectype = rectypes[Math.floor(Math.random()*rectypes.length)];
				var creator = 'ianrees';
				var value = Math.random()*100;
				var creationtime = new Date(2011, month, day);
				return {creationtime:creationtime, rectype: rectype, creator: creator, value:value}
			}
			for (var i=0;i<count;i++) {data.push(next())}
			var q = {'recs':data};
			this.options.q = q;
			// Run the callback
			cb(q);			
		},
		
		query: function(cb) {
			// Run a query
			// var c = [["rectype","is","image_capture*"],["children","name","46604*"],["ctf_bfactor","any",""],["ctf_defocus_measured","any",""]];

			// var c = [['rectype', 'is', 'image_capture*'], ['creationtime']]
			// $.jsonRPC.call('query', {c:c}, function(q) {
			// 	cb(q['recs']);
			// });

			$.jsonRPC.call('getchildren', {names:136}, function(recs){
				$.jsonRPC.call('getrecord', [recs], function(recs){
					cb(recs);					
				});
			});
		},
		
		plot: function(q) {
			// Override this to draw the plot
		},
		
		controls: function() {
			// Override this to draw the plot controls
		},
		
		redraw: function() {
			
		},
		
		group: function(recs) {
			var self = this;
			var bins = {};
			bins.__xkeys = {}; // hack
			bins.__ykeys = {};
			bins.__zkeys = {};
			recs.map(function(d) {
				var bz = self.fz(d);
				var bx = self.fx(d);
				bins.__xkeys[bx] = bx;
				bins.__zkeys[bz] = bz;
				if (bins[bz] == null) {
					bins[bz] = {}
				}
				if (bins[bz][bx] == null) {
					bins[bz][bx] = {x:bx, y:0, ysum:0, yoff:0}
				}
				bins[bz][bx].y += 1
			});
			return bins			
		}
	});	

	$.widget('emen2.PlotScatter', $.emen2.PlotBase, {
		
	});
	
	$.widget('emen2.PlotBar', $.emen2.PlotBase, {

	});
	
	// Plot widgets
	$.widget('emen2.PlotTime', $.emen2.PlotBase, {
		
		fx: function(d) {
			var bx = new Date(d[this.options.xkey]);
			return this.d3x(bx)
		},
		
		redraw: function() {
			var d = this.x.domain();
			var t1 = d[0];
			var year = t1.getFullYear()+1;
			t1.setFullYear(year);
			console.log(d);
			this.x.transition().duration(1000).domain([d[0], d[1]]);
		},
		
		plot: function(recs) {
			// Options
			var self = this;

			// Additional options
			this.options.cumulative = true;
			this.options.bin = 'month';
			// Set formats and interval generator
			if (this.options.bin == 'year') {
				this.d3x = d3.time.year;
				this.d3xs = d3.time.years;
				this.format = d3.time.format("%Y");
			} else if (this.options.bin == 'month') {
				this.d3x = d3.time.month;
				this.d3xs = d3.time.months;
				this.format = d3.time.format("%Y - %m");
			} else if (this.options.bin == 'day') {
				this.d3x = d3.time.day;
				this.d3xs = d3.time.days;
				this.format = d3.time.format("%Y - %m - %d");
			}

			// Bin the data, by zkey, then by xkey
			var bins = this.group(recs);

			// X domain
			var bxs = d3.values(bins.__xkeys);
			bxs.sort(function(a,b){return a-b});
			var xmin = this.d3x(bxs[0]);
			var xmax = bxs[bxs.length-1];			
			bxs = this.d3xs(xmin, xmax); // grumble..
			
			// Y domain
			var bys = d3.values(bins.__ykeys);
			var ymin = 0;
			var ymax = 0;

			// Z domain
			var bzs = d3.values(bins.__zkeys);

			// If cumulative
			bzs.map(function(bz) {
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

			// If stacked
			bxs.map(function(bx) {
				var yoff = 0;
				bzs.map(function(bz) {
					var item = bins[bz][bx];
					if (item) {
						item.yoff = yoff;
						yoff += item.ysum
					}
				});
				if (yoff > ymax) {ymax = yoff}
			});

			// Update options
			// if (this.options.xmin == null) {this.options.xmin = xmin};
			// if (this.options.xmax == null) {this.options.xmax = xmax};
			// if (this.options.ymin == null) {this.options.ymin = ymin};
			// if (this.options.ymax == null) {this.options.ymax = ymax};
			
			var width = this.element.width();
			var height = 600;
			var p = [0,0,0,0];

			this.x = d3.time.scale().domain([xmin, xmax]).range([0,width]);
			this.y = d3.scale.linear().domain([ymin,ymax]).range([0,height]);
			this.z = this.options.colors; 
			
			// Create the SVG element
			this.svg = d3.select("#chart").append("svg:svg")
			    .attr("width", width)
			    .attr("height", height)
		        .attr("pointer-events", "all")
			  .append("svg:g")		

			// Add a group for each cause.
			var cause = this.svg.selectAll("g.cause")
			    .data(bzs)
			  .enter().append("svg:g")
			    .attr("class", "cause")
				.attr('data-bz', function(d,i) {return bzs[i]})
			    .style("fill", function(d, i) { return self.z(i); })
			    .style("stroke", function(d, i) { return d3.rgb(self.z(i))});

			var barwidth = width / d3.time.months(xmin, xmax).length;

			// Add a rect for each date.
			var rect = cause.selectAll("rect")
			    .data(function(d){return d3.values(bins[d])})
			  .enter().append("svg:rect")
			    .attr("x", function(d) { return self.x(d.x) })
			    .attr("y", function(d) { return height-self.y(d.ysum)-self.y(d.yoff) })
			    .attr("height", function(d) { return self.y(d.ysum) })
			    .attr("width", barwidth);
			

		 	this.downx = Math.NaN;
		    this.downscalex;
			this.svg.on("mousedown", function(d) {
				var p = d3.svg.mouse(self.svg[0][0]);
				self.downx = self.x.invert(p[0]);
				self.downscalex = self.x;
			});
			var body = d3.select('body');
			this.svg.on("mousemove", function(d) {
				if (!isNaN(self.downx)) {
					var p = d3.svg.mouse(self.svg[0][0])
					var rupx = p[0];
					if (rupx != 0) {
						//self.x.domain([downscalex.domain()[0],  mw * (downx - downscalex.domain()[0]) / rupx + downscalex.domain()[0]]);
					}
					// self.redraw();
				}
			});
			this.svg.on("mouseup", function(d) {
				self.downx = Math.NaN;
			});			
			
			return
			
			// Add a label per date.
			var label = svg.selectAll("text")
			    .data(xdtest2) //x.domain()
			  .enter().append("svg:text")
				.attr('transform','rotate(90)')
			    .attr("y", function(d) { return -(x(d) + x.rangeBand() / 2) })
			    .attr("x", "3em")
				.attr("dy", "0.31em")
			    .attr("text-anchor", "middle")
			    .text(format);

			// Add y-axis rules.
			var rule = svg.selectAll("g.rule")
			    .data(y.ticks(5))
			  .enter().append("svg:g")
			    .attr("class", "rule")
			    .attr("transform", function(d) { return "translate(0," + -y(d) + ")"; });
				
			rule.append("svg:line")
			    .attr("x2", w - p[1] - p[3])
			    .style("stroke", function(d) { return "#ccc" })
			    .style("stroke-opacity", function(d) { return d ? .7 : null; });
				
			rule.append("svg:text")
			    .attr("x", w - p[1] - p[3] + 6)
			    .attr("dy", ".35em")
			    .text(d3.format(",d"));			


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