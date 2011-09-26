function testplot() {
	
	var xparam = 'ctf_defocus_measured';
	var yparam = 'ctf_bfactor';
	var groupby = 'rectype';
	var data = q['recs'];
	
	var xmin = pv.min(data, function(d) d[xparam]);
	var xmax = pv.max(data, function(d) d[xparam]);
	var ymin = pv.min(data, function(d) d[yparam]);
	var ymax = pv.max(data, function(d) d[yparam]);

	var w = 300,
	    h = 300,
	    kx = (xmax-xmin)/2,
	    ky = (ymax-ymin)/2,
	    x = pv.Scale.linear(xmin, xmax).range(0, w),
	    y = pv.Scale.linear(ymin, ymax).range(0, h);

	/* The root panel. */
	var vis = new pv.Panel()
		.canvas("fig")
		.width(w)
		.height(h)
		.top(30)
		.left(40)
		.right(20)
		.bottom(20)
		.strokeStyle("#aaa");

	/* X-axis and ticks. */
	vis.add(pv.Rule)
		.data(function() x.ticks())
		.strokeStyle(function(d) d ? "#ccc" : "#999")
		.left(x)
		.anchor("bottom").add(pv.Label)
		.text(x.tickFormat);


	/* Y-axis and ticks. */
	vis.add(pv.Rule)
		.data(function() y.ticks())
		.strokeStyle(function(d) d ? "#ccc" : "#999")
		.bottom(y)
		.anchor("left").add(pv.Label)
		.text(y.tickFormat);


	/* The dot plot! */
	vis.add(pv.Panel)
		.overflow("hidden")
		.add(pv.Dot)
		.data(data)
		.left(function(d) x(d[xparam]))
		.bottom(function(d) y(d[yparam]))
		.fillStyle(pv.rgb(121, 173, 210, .5))
		.radius(function() 5 / this.scale)
		;

	vis.add(pv.Panel)
	    .events("all")
	    .event("mousedown", pv.Behavior.pan())
	    .event("mousewheel", pv.Behavior.zoom())
	    .event("pan", transform)
	    .event("zoom", transform);	
		
	vis.render();

	function transform() {
		var t = this.transform().invert();
		//t.y = -t.y;
		x.domain(t.x / w * 2 * kx - kx, (t.k + t.x / w) * 2 * kx - kx);
		y.domain(t.y / h * 2 * ky - ky, (t.k + t.y / h) * 2 * ky - ky);
		vis.render();
	}

}

<%!
public = True
headers = {
	'Content-Type': 'application/javascript',
	'Cache-Control': 'max-age=86400'
}
%>