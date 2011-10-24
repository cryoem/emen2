<%inherit file="/page" />

<%block name="css_inline">
.chart {
  margin-left: 42px;
  font: 10px sans-serif;
  shape-rendering: crispEdges;
}

.chart div {
  background-color: steelblue;
  text-align: right;
  padding: 3px;
  margin: 1px;
  color: white;
}

.chart rect {
  stroke: white;
  fill: steelblue;
}

.chart text.bar {
  fill: white;
}
</%block>



<%block name="js_ready">

var w = 280,
    h = 280,
    m = [10, 0, 20, 35], // top right bottom left
    n = 100;

var chart = d3.chart.scatter()
    .width(w)
    .height(h)
    .domain([-.1, 1.1])
    .tickFormat(function(d) { return ~~(d * 100); });

var vis = d3.select("#chart")
  .append("svg:svg")
  .append("svg:g")
    .attr("class", "scatter")
    .attr("transform", "translate(" + m[3] + "," + m[0] + ")")
    .data([{
      x: d3.range(n).map(Math.random),
      y: d3.range(n).map(Math.random),
    }]);

vis.append("svg:rect")
    .attr("class", "box")
    .attr("width", w)
    .attr("height", h);

vis.call(chart);

chart.duration(1000);

window.transition = function() {
  vis.map(randomize).call(chart);
};

function randomize(d) {
  d.x = d3.range(n).map(Math.random);
  d.y = d3.range(n).map(Math.random);
  return d;
}


// Run a query
var c = [["rectype","is","image_capture*"],["children","name","46604*"],["ctf_bfactor","any",""],["ctf_defocus_measured","any",""]];
$.jsonRPC.call('query', {c:c}, function(q) {
	console.log("returned");
	var data = [4, 8, 15, 16, 23, 42];
	var chart = d3.select("body")
	  .append("div")
	     .attr("class", "chart");

	 chart.selectAll("div")
			.data(data)
		.enter().append("div")
			.style("width", function(d) { return d * 10 + "px"; })
			.text(function(d) { return d; });
});

</%block>

Test bar chart!

<div id="#chart">Chart</div>