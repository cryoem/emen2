<%! import jsonrpc.jsonutil  %>

<%def name="traverse(tree, root, recnames, recurse, mode='children', keytype='record', expandable=True)">
	<%def name="inner(parent, children, depth)">
		<ul data-depth="${depth}">
			% for child in sorted(children, key=lambda x:(recnames.get(x) or '').lower()):						
				<li>
					% if parent != None:
						<a data-key="${child}" data-parent="${parent}" href="${EMEN2WEBROOT}/${keytype}/${child}/">${recnames.get(child) or child}</a>
					% else:
						<a data-key="${child}" href="${EMEN2WEBROOT}/${keytype}/${child}/">${recnames.get(child) or child}</a>					
					% endif
					
					% if tree.get(child) and (depth <= recurse or recurse < 0):
						% if expandable:
							<img class="e2-map-expand e2-map-expanded" alt="${len(tree.get(child, []))} children" src="${EMEN2WEBROOT}/static/images/bg-close.${mode}.png" />
						% endif
						${inner(child, tree.get(child), depth=depth+1)}
					% elif tree.get(child) and depth > recurse and expandable:
						<img class="e2-map-expand" alt="${len(tree.get(child, []))} children" src="${EMEN2WEBROOT}/static/images/bg-open.${mode}.png" />
					% endif

				</li>
			% endfor			
		</ul>

	</%def>
	
	<div class="e2-map e2-map-${mode} e2l-clearfix" data-root="${root}" data-mode="${mode}" data-keytype="${keytype}">
		${inner(None, tree.get(None, [root]), depth=1)}
	</div>
	
</%def>

${traverse(tree, root, recnames, recurse, mode=mode, keytype=keytype, expandable=expandable)}
