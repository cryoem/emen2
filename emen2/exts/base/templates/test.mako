<%inherit file="/page" />

<%block name="css_inline">
path.line {
  fill: none;
  stroke: #666;
  stroke-width: 1.5px;
}

path.area {
  fill: #e7e7e7;
}

.axis {
  shape-rendering: crispEdges;
}
.axis line {
  stroke-opacity: .1;
  stroke: #000;
}
.axis path {
  fill: none;
  stroke: #000;
}

.e2-plot-table {
	list-style:none;
	border:solid red 1px;
	margin:0px;
	padding:0px;
	width:220px;
	float:right;
}


</%block>


<%block name="js_ready">
	${parent.js_ready()}
	var t = 'hist';
	if (t=='hist') {
		$("#chart").PlotHistogram({
			'xkey':'creationtime'
		});
	} else if (t=='scatter') {	
		$("#chart").PlotScatter({
			//'xkey': 'creationtime',
			'xkey':'ctf_defocus_measured',
			'ykey':'ctf_bfactor'
		});
	}
</%block>

<div id="chart"></div>
