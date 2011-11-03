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
	// console.log(t);
	if (t=='time') {
		$("#chart").PlotTime({
			'xkey':'creationtime',
			'ykey':''		
		});
	} else if (t=='scatter') {	
		$("#chart").PlotScatter({
			//'xmin': 200,
			//'xmax': 300,
			//'ymin': 2.4,
			//'ymax': 3.0,
			'xkey':'ctf_bfactor',
			'ykey':'ctf_defocus_measured'
		});
	}
</%block>

<div id="chart"></div>
