<%inherit file="/page" />

<%block name="css_inline">
.chart rect {
  fill: steelblue;
  stroke: white;
}
</%block>



<%block name="js_ready">
	$("#chart").Plot_datetime();
</%block>

<h1>Date histogram</h1>
<div id="chart"></div>