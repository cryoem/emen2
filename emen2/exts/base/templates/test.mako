<%inherit file="/page" />

<%block name="css_inline">
.chart rect {
  fill: steelblue;
  stroke: white;
}
</%block>



<%block name="js_ready">

var count = 50;
var width = 800;
var height = 500;

var data = []
function next() {
	var month = Math.floor(Math.random()*0.9);
	var rectype = 'ccd';
	var creator = 'ianrees';
	var value = Math.random()*100;
	return {creationtime:'2011/0'+month, rectype: rectype, creator: creator, value:value}
}
for (var i=0;i<count;i++) {data.push(next())}

var w = width/count,
	h = height;


var x = d3.scale.linear()
	.domain([0, 1])
	.range([0, w]);

var y = d3.scale.linear()
	.domain([0, 100])
	.rangeRound([0, h]);

var chart = d3.select("#chart")
  .append("svg:svg")
    .attr("class", "chart")
    .attr("width", width+100)
    .attr("height", height+100);

// Ticks
chart.selectAll("line")
    .data(y.ticks(10))
  .enter().append("svg:line")
    .attr("x1", 0)
    .attr("x2", width)
    .attr("y1", y)
    .attr("y2", y)
    .attr("stroke", "#ccc");



// Draw items
chart.selectAll("rect")
    .data(data)
  .enter().append("svg:rect")
    .attr("x", function(d, i) { return x(i) - .5; })
    .attr("y", function(d) { return h - y(d.value) - .5; })
    .attr("width", w)
    .attr("height", function(d) { return y(d.value); });


// X axis
chart.append("svg:line")
	.attr('y1', height-1)
	.attr('y2', height-1)
    .attr("x1", 0)
    .attr("x2", width)
    .attr("stroke", "#000");


chart.selectAll("text.rule")
    .data(y.ticks(10))
  .enter().append("svg:text")
    .attr("class", "rule")
    .attr("x", width)
    .attr("y", y)
	.attr('dx', 30)
    .attr("dy", 3)
    .attr("text-anchor", "middle")
    .text(String);




// Run a query
// var c = [["rectype","is","image_capture*"],["children","name","46604*"],["ctf_bfactor","any",""],["ctf_defocus_measured","any",""]];
// $.jsonRPC.call('query', {c:c}, function(q) {
// });

</%block>

Test bar chart!

<div id="chart"></div>