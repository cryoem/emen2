<%inherit file="/recdef/recdef" />
<%namespace file="/recdef/publication" import="publication" />
<%def name="header()">
	<style>
		div.content pre{
			overflow: hidden;
		}

		.frame {
		    display: block;
		    overflow: hidden;
		    position: absolute;
		    left: 0px;
		    top: 0px;
		    right: 0px;
		    bottom: 0px;
		    border: black 3px ridge;
		    background: #ccc;
		    text-align: center;
		}   
		.frame img {
		    height: 100%;
		    border: medium ridge;
		}   
		
		body {
		    position: relative;
		}   
		
		#cont {
		    background: #ccc;
		    position: absolute;
		    left: 25%;
		    right: 25%;
		    top: 0px;
		    bottom: 3px;
		    border: black ridge 3px;
		    text-align: center;
		    overflow: auto;
		}   
		
		.controls {
			overflow: hidden;
			bottom: 3px;
		 	top:0px;
		 	position: absolute;
		 	right:75%;
		 	background-color: #333;
		 	color: #ccc; 
		 	border: ridge 3px #888;
		 	overflow: auto; 
		 	text-align: center;
		}
		.controls div { 
			padding: 0px 10px;
			padding-right: 25px;
			cursor: pointer;
		}
		.controls div:hover { 
			background: #ccc;
			color: black !important;
			cursor: pointer;
		}
		.red { background: red; }
		.blue { background: blue; }
		.yellow { background: yellow; }
		.green { background: #008800; }
		.black { background: black; }
		
		#frame {
		    position: relative;
		    height: 200px;
		    overflow: hidden;
		}   
	</style>
##	<script type="text/javascript" src="/static/js/slideshow.js"></script>
##	<script type="text/javascript">
##		$('#cont').ready(function() {
##			a = $('#cont')
##			x = $(a.parents()[0]);y=$('<div class="controls"></div>');x.append(y)
##			y.css({})
##			b = a.slideshow({controls: y, name: 'b'})
##			b.start();
##		})
##	</script>
</%def>

##<div id="frame">
##</div>

% if children:
	<h2>Children:</h2>
	% for rec in ctxt.getrecord(children):
		<a href='${rec.name}'>${repr(rec) | h}
		<% a = rec['%s_name' % (rec.rectype)] %>
		%if a:
			${rec.rectype.capitalize()} Name: ${a}
		%endif
		</a>
		<br />
	% endfor
% endif

<pre>
<h2>Record</h2>
${ record | h }
<h2>RecordDef</h2>
<% rectype = ctxt.db.getrecorddef(record.rectype) %>
${rectype | h}

</pre>


<% parents = ctxt.get_parents() %>
% if parents:
	<h2>Parents:</h2>
	% for rec in ctxt.db.getrecord(parents):
		${repr(rec) | h
		}<% a = rec['%s_name' % (rec.rectype)] %>
		%if a:
		  <% root=ctxt.root;ctxt.chroot(0) %>
		  ${rec.rectype.capitalize()} Name: ${a}
		  <% ctxt.chroot(root) %>
		%endif
		<br />
	% endfor
% endif
