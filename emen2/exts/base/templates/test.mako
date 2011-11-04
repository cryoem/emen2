<%inherit file="/page" />

<%block name="css_inline">
rect {
  shape-rendering:crispEdges;
}
svg {
	border:solid red 1px;
}
</%block>


<%block name="js_ready">
	${parent.js_ready()}
	var t = 'scatter';
	if (t=='hist') {
		$("#chart").PlotHistogram({
			'xkey':'creationtime'
		});
	} else if (t=='scatter') {	
		$("#chart").PlotScatter({
			'xkey':'ctf_defocus_measured',
			'ykey':'ctf_bfactor',
			'xmin': 0,
			'xmax': 6,
			'ymin': 0,
			'ymax': 600
		});
	}
</%block>

<div id="chart"></div>
