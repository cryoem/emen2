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
			datekey: 'creationtime'
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
			// var c = [['children', 'name', '46604*'], ['rectype'], ['creationtime']];
			// $.jsonRPC.call('query', {c:c}, function(q) {
			// 	cb(q['recs']);
			// });
			$.jsonRPC.call('getchildren', [136], function(recs){
				$.jsonRPC.call('getrecord', [recs], function(recs){
					cb(recs);					
				})
			})
		},
		
		plot: function(q) {
			// Override this to draw the plot
		},
		
		controls: function() {
			// Override this to draw the plot controls
		}
	});	
	
	// Plot widgets
	$.widget('emen2.Plot_datetime', $.emen2.PlotBase, {
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
				alert('Unknown bin mode: ', this.options.bin);
				return
			}
			
			// Bin the data, group by label..
			var dates = $.map(recs, function(d){return new Date(d[self.options.datekey])});
			var xmin = this.options.xmin || ft(d3.min(dates));
			var xmax = this.options.xmax || d3.max(dates);
			var iv = fts(xmin, xmax);
			console.log("x domain:", xmin, xmax);

			// Group data
			var groups = {};
			$.each(recs, function(i,d) {
				if (groups[d[self.options.groupby]]==null){groups[d[self.options.groupby]]=[]}
				groups[d[self.options.groupby]].push(d);
			});
			var keys = d3.keys(groups);
			
			// Transform groups into right stack objects
			// For each group...
			var stacks = $.map(groups, function(v,k) {
				var stack = [];
				// ...for interval period...
				for (var i=0;i<iv.length;i++) {
					// ...filter the group
					var found = v.filter(function(d) {
						var dt = ft(new Date(d[self.options.datekey]));
						if ((dt >= iv[i]) && (dt < iv[i+1] || !iv[i+1])) {
							return true
						}
					});
					stack.push({x:iv[i], y:found.length});
				}
				return [stack]
			});

			// Setup width, padding, and scales
			var w = this.element.width(),
			    h = 700, // height
			    p = [10,100,100,10], // padding.. set ranges
			    x = d3.scale.ordinal().rangeRoundBands([0, w - p[1] - p[3]]),
			    y = d3.scale.linear().range([0, h - p[0] - p[2]]),
			    z = d3.scale.ordinal().range(["lightpink", "darkgray", "lightblue"]),
			    format = d3.time.format("%Y-%m");
	
			// var t = $.map(d3.values(groups), function(d){return d3.values(d)});
			var layout = d3.layout.stack()
			var stacks = layout(stacks);

			// var stacks = layout([d3.values(groups.ccd), d3.values(groups.micrograph), d3.values(groups.stack)]);

			// Compute the x-domain (by date) and y-domain (by top).
			x.domain(fts(xmin, xmax));
		  	y.domain([0, d3.max(stacks[stacks.length - 1], function(d) { return d.y0 + d.y; })]);

			// Create the SVG element
			var svg = d3.select("#chart").append("svg:svg")
			    .attr("width", w)
			    .attr("height", h)
			  .append("svg:g")
			    .attr("transform", "translate(" + p[3] + "," + (h - p[2]) + ")");

			// // Add a label per date.
			var label = svg.selectAll("text")
			    .data(x.domain())
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
			    .style("stroke", function(d, i) { return d3.rgb(z(i)).darker(); });

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