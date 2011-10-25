<%inherit file="/page" />

<%block name="css_inline">
.chart rect {
  fill: steelblue;
  stroke: white;
}
</%block>



<%block name="js_ready">

// Fake query results..
var count = 100;
var data = [];
function next() {
	var month = Math.floor(Math.random()*12);
	var day = Math.floor(Math.random()*30)+1;
	console.log(month, day)
	var rectype = 'ccd';
	var creator = 'ianrees';
	var value = Math.random()*100;
	var creationtime = new Date(2011, month, day);
	return {creationtime:creationtime, rectype: rectype, creator: creator, value:value}
}
for (var i=0;i<count;i++) {data.push(next())}

// Prepare the date intervals..
var a = $.map(data, function(d) {return d.creationtime});
var min = d3.min(a);
var first = d3.time.month(min);
var max = d3.max(a);
var iv = d3.time.months(first, max);
console.log('intervals:', iv);

// Bin the data, group by label..
var binned = [];
var groupby = 'rectype';
var datekey = 'creationtime';

// This should be done by a quick first pass of data
var groups = ['ccd','scan','micrograph']

// Count items in each interval
for (var i=0;i<iv.length;i++) {
	var m1 = iv[i];
	var m2 = iv[i+1];
	// Extend using groups
	var item = {'creationtime':m1, 'ccd':0, 'scan':5, 'micrograph':10};
	for (var j=0;j<data.length;j++) {
		var d = data[j];
		// Last item will be unbounded; check for that..
		if ((d[datekey] > m1 || m1 == null) && (d[datekey] <= m2 || m2 == null)) {
			item[d[groupby]] += 1;
		}
	}
	binned.push(item);
}

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
var causes = d3.layout.stack()(groups.map(function(cause) {
  return binned.map(function(d) {
    return {x: d.creationtime, y: +d[cause]};
  });
}));

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

// Add a label per date.
var label = svg.selectAll("text")
    .data(x.domain())
  .enter().append("svg:text")
    .attr("x", function(d) { return x(d) + x.rangeBand() / 2; })
    .attr("y", 6)
    .attr("text-anchor", "middle")
    .attr("dy", ".71em")
    .text(format);

// Add y-axis rules.
var rule = svg.selectAll("g.rule")
    .data(y.ticks(5))
  .enter().append("svg:g")
    .attr("class", "rule")
    .attr("transform", function(d) { return "translate(0," + -y(d) + ")"; });

rule.append("svg:line")
    .attr("x2", w - p[1] - p[3])
    .style("stroke", function(d) { return d ? "#fff" : "#000"; })
    .style("stroke-opacity", function(d) { return d ? .7 : null; });

rule.append("svg:text")
    .attr("x", w - p[1] - p[3] + 6)
    .attr("dy", ".35em")
    .text(d3.format(",d"));


// Run a query
// var c = [["rectype","is","image_capture*"],["children","name","46604*"],["ctf_bfactor","any",""],["ctf_defocus_measured","any",""]];
// $.jsonRPC.call('query', {c:c}, function(q) {
// });

</%block>

<h1>Date histogram</h1>
<div id="chart"></div>