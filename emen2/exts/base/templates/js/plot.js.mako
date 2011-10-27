(function($) {
   $.widget('emen2.PlotBase', {
		options: {
			q: null,
			xparam: 'ctf_defocus_measured',
			yparam: 'ctf_bfactor',
			xmin: null,
			xmax: null,
			ymin: null,
			ymax: null,
			groupby: 'rectype',
			datekey: 'creationtime',
			colors: d3.scale.category10()
		},

		_create: function() {
			this.built = 0;
			this.build();
		},

		build: function() {
			if (this.built) {return}
			var self = this;
			this.built = 1;
			this.element.append('<div id="fig"></div>');
			this.query(function(q){self.plot(q)})
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
			var c = [['rectype', 'is', 'image_capture*'], ['creationtime']]
			$.jsonRPC.call('query', {c:c}, function(q) {
				cb(q['recs']);
			});
			// $.jsonRPC.call('getchildren', {names:[114], recurse:-1, rectype:'image_capture*'}, function(recs){
			// 	$.jsonRPC.call('getrecord', [recs], function(recs){
			// 		cb(recs);					
			// 	});
			// });
		},
		
		plot: function(q) {
			// Override this to draw the plot
		},
		
		controls: function() {
			// Override this to draw the plot controls
		}
	});	
	
	// Plot widgets
	$.widget('emen2.PlotBar', $.emen2.PlotBase, {
		plot: function(recs) {
			// Options
			var self = this;
			this.options.bin = 'month';
			
			if (this.options.bin == 'year') {
				var ft = d3.time.year;
				var fts = d3.time.years;								
			} else if (this.options.bin == 'month') {
				var ft = d3.time.month;
				var fts = d3.time.months;				
			} else if (this.options.bin == 'day') {
				var ft = d3.time.day;
				var fts = d3.time.days;
			} else {
				var ft = function(i){return i}
				var fts = function(i){return i}
			}

			// Bin the data, by groupby, then by datekey
			var bins = {};
			var bxs = []; // javascript is stupid, keys are strings
			// var dates = $.map(recs, function(d){
			recs.map(function(d) {
				var bg = d[self.options.groupby];
				var bx = new Date(d[self.options.datekey]);
				bx = ft(bx);
				if (bins[bg] == null) {
					bins[bg] = {}
				}
				if (bins[bg][bx] == null) {
					bxs.push(bx);
					bins[bg][bx] = 0;
				}
				bins[bg][bx] += 1;
			});
			var keys = d3.keys(bins);
			var xmin = (this.options.xmin == null) ? d3.min(bxs) : this.options.xmin;
			xmin = ft(xmin);
			var xmax = (this.options.xmax == null) ? d3.max(bxs) : this.options.xmax;
			var bxs = fts(xmin, xmax);

			// d3 wants lists, not dicts
			var stacks = [];
			keys.map(function(bg) {
				var stack = [];
				bxs.map(function(bx) {
					stack.push({x:bx, y:(bins[bg][bx] || 0)});
				});
				stacks.push(stack);
			});


			// Setup width, padding, and scales
			var w = this.element.width(),
			    h = 700, // height
			    p = [10,100,100,10], // padding.. set ranges
			    x = d3.scale.ordinal().rangeRoundBands([0, w - p[1] - p[3]]),
			    y = d3.scale.linear().range([0, h - p[0] - p[2]]),
				//z = d3.scale.ordinal().range(this.options.colors),
			    z = this.options.colors; 
			    format = d3.time.format("%Y - %b");
	
			var layout = d3.layout.stack()
			var stacks = layout(stacks);

			// Compute the x-domain (by date) and y-domain (by top).
			x.domain(fts(xmin, xmax));
		  	y.domain([0, d3.max(stacks[stacks.length - 1], function(d) {return d.y0 + d.y})]);

			// *** Draw! *** //

			// Create the SVG element
			var svg = d3.select("#chart").append("svg:svg")
			    .attr("width", w)
			    .attr("height", h)
			  .append("svg:g")
			    .attr("transform", "translate(" + p[3] + "," + (h - p[2]) + ")");

			// Reduce the number of labels....
			var xdtest = x.domain();
			var xdtest2 = [];
			for (var i=0;i<xdtest.length;i++) {
				if (i%4==1) {
					xdtest2.push(xdtest[i]);
				}
			}

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

			// Add a group for each cause.
			var cause = svg.selectAll("g.cause")
			    .data(stacks)
			  .enter().append("svg:g")
			    .attr("class", "cause")
			    .style("fill", function(d, i) { return z(i); })
			    .style("stroke", function(d, i) { return d3.rgb(z(i))}); // .darker()

			// Add a rect for each date.
			var rect = cause.selectAll("rect")
			    .data(Object)
			  .enter().append("svg:rect")
			    .attr("x", function(d) { return x(d.x); })
			    .attr("y", function(d) { return -y(d.y0) - y(d.y); })
			    .attr("height", function(d) { return y(d.y); })
			    .attr("width", x.rangeBand());

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