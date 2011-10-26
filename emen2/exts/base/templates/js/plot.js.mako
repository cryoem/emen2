(function($) {
   $.widget('emen2.PlotBase', {
		options: {
			q: null,
			xparam: 'ctf_defocus_measured',
			yparam: 'ctf_bfactor',
			groupby: 'rectype'
		},

		_create: function() {
			this.built = 0;
			this.build();
		},

		build: function() {
			if (this.built) {return}
			var self = this;
			this.built = 1;
			this.element.append('<div id="fig">Figure</div>');
			this.query(function(q){self.plot(q)})
		},
		
		query: function(cb) {
			// Run a query
			// var c = [["rectype","is","image_capture*"],["children","name","46604*"],["ctf_bfactor","any",""],["ctf_defocus_measured","any",""]];
			// $.jsonRPC.call('query', {c:c}, function(q) {
			// });
			// Run query and update plot
			// Fake query results..
			var count = 1000;
			var data = [];
			function next() {
				var month = Math.floor(Math.random()*12);
				var day = Math.floor(Math.random()*30)+1;
				var rectype = 'ccd';
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
		
		plot: function(q) {
			// Override this to draw the plot
		},
		
		controls: function() {
			// Override this to draw the plot controls
		}
	});	
	
	// Plot widgets
	$.widget('emen2.Plot_datetime', $.emen2.PlotBase, {
		plot: function(q) {			
			// Bin the data, group by label..
			var data = q['recs'];
			var binned = [];
			var groupby = 'rectype';
			var datekey = 'creationtime';

			// X axis is the datekey
			// Y axis is the count of items for that date
			var groups = {};
			$.each(data, function(i,d) {
				var t = d3.time.month(d[datekey]);
				var v = d[groupby];
				// Create the item
				if (groups[v]==null) {groups[v] = {}}
				// Create the time entry
				if (groups[v][t]==null) {groups[v][t] = {x:t, y:0}}
				// Increment
				groups[v][t].y += 1
			});

			// Setup width, padding, and scales
			var w = 960, // width
			    h = 500, // height
			    p = [20, 50, 30, 20], // padding
			    x = d3.scale.ordinal().rangeRoundBands([0, w - p[1] - p[3]]),
			    y = d3.scale.linear().range([0, h - p[0] - p[2]]),
			    z = d3.scale.ordinal().range(["lightpink", "darkgray", "lightblue"]),
			    format = d3.time.format("%Y/%m");
	

			// Create the SVG element
			var svg = d3.select("#chart").append("svg:svg")
			    .attr("width", w)
			    .attr("height", h)
			  .append("svg:g")
			    .attr("transform", "translate(" + p[3] + "," + (h - p[2]) + ")");
	
			// Transpose the data into layers by cause.
			var test = [];
			var test2 = [];
			for (var i=0;i<5;i++) {
				var d = new Date(2011, i*2, 1);
				var d2 = new Date(2011, i, 1);
				test.push({x:d, y:i});
				test2.push({x:d2, y:i*i});
			}
			var causes = d3.layout.stack()([test,test2]);

			// Compute the x-domain (by date) and y-domain (by top).
			x.domain(causes[0].map(function(d) { return d.x; }));
			y.domain([0, d3.max(causes[causes.length - 1], function(d) { return d.y0 + d.y; })]);
	
			// Add a group for each cause.
			var cause = svg.selectAll("g.cause")
			    .data(causes)
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
	
			// // Add a label per date.
			var label = svg.selectAll("text")
			    .data(x.domain())
			  .enter().append("svg:text")
			    .attr("x", function(d) { return x(d) + x.rangeBand() / 2; })
			    .attr("y", 6)
			    .attr("text-anchor", "middle")
			    .attr("dy", ".71em")
			    .text(format);
			// 	
			// // Add y-axis rules.
			// var rule = svg.selectAll("g.rule")
			//     .data(y.ticks(5))
			//   .enter().append("svg:g")
			//     .attr("class", "rule")
			//     .attr("transform", function(d) { return "translate(0," + -y(d) + ")"; });
			// 	
			// rule.append("svg:line")
			//     .attr("x2", w - p[1] - p[3])
			//     .style("stroke", function(d) { return d ? "#fff" : "#000"; })
			//     .style("stroke-opacity", function(d) { return d ? .7 : null; });
			// 	
			// rule.append("svg:text")
			//     .attr("x", w - p[1] - p[3] + 6)
			//     .attr("dy", ".35em")
			//     .text(d3.format(",d"));			
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