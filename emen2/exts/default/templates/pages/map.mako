<%! import jsonrpc.jsonutil  %>

<%def name="traverse(tree, root, recnames, recurse, mode='children', keytype='record', expandable=True, id='')">
	<%def name="inner(parent, children, depth)">

		## ul for this depth level
		<ul data-depth="${depth}" data-name="${parent}">

			% for child in sorted(children, key=lambda x:(recnames.get(x) or '').lower()):
				## Create a LI for each child.
				<li data-name="${child}">
					<a href="${EMEN2WEBROOT}/${keytype}/${child}/">${recnames.get(child) or child}</a>
					
					% if tree.get(child) and (depth <= recurse or recurse < 0):
						## If we're drawing the next level...
						% if expandable:
							<img class="e2-map-expand e2-map-expanded" alt="${len(tree.get(child, []))} children" src="${EMEN2WEBROOT}/static/images/bg-close.${mode}.png" />
						% endif
						${inner(child, tree.get(child), depth=depth+1)}

					% elif tree.get(child) and depth > recurse and expandable:
						## ... or just show an icon to expand the children
						<img class="e2-map-expand" alt="${len(tree.get(child, []))} children" src="${EMEN2WEBROOT}/static/images/bg-open.${mode}.png" />
					% endif

				</li>
			% endfor			
		</ul>

	</%def>
	
	## The top level container
	<div class="e2-map e2-map-${mode} e2l-cf" data-root="${root}" data-mode="${mode}" data-keytype="${keytype}" id="${id}">
		${inner(None, tree.get(None, [root]), depth=1)}
	</div>
	
</%def>

${traverse(tree, root, recnames, recurse, mode=mode, keytype=keytype, expandable=expandable, id=id)}
