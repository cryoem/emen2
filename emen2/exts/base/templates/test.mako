<%inherit file="/page" />

<%block name="css_inline">


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
