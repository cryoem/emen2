<%inherit file="/page" />

<%block name="css_inline">
.chart rect {
  fill: steelblue;
  stroke: white;
}
</%block>


<%block name="js_ready">
	$("#chart").PlotTime({});
</%block>

<h1 style="text-align:center">Total NCMI Projects</h1>
<div id="chart"></div>
