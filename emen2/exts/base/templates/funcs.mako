<%! MAXMENU = 8 %>
<%def name="userbox(ctxt,pth)" filter="trim">
	<%
		from random import randrange
		random_id = "admin_%d" % randrange(100)
	%>
   <script type="text/javascript">
      var adminid = '#${random_id}'
      $('body').click(
         function (target) {
            var e = $(adminid);
            if (target.altKey) {
               if (e.css('visibility') == 'hidden') {
                  var x = target.layerX-($(adminid).width()/2)
                  var y = target.layerY-($(adminid).height()/2)
                  e.css('left', x)
                  e.css('top', y)
                  e.css('visibility', 'visible')
               } else if (e.css('visibility') == 'visible') {
                  e.css('visibility', 'hidden');
               }
            }
         });
   </script>
 % if ctxt.get_user():
	<div id='${random_id}' style='border: thin solid black;background: #ccc;position: absolute;visibility:hidden'>
			  Logged in as: ${ctxt.get_user().username}&mdash;&gt;
	        <a href="${ctxt.reverse('Record', name=str(ctxt.get_path_id([]).pop()))}">[Page Admin]</a>
	        <a href="${EMEN2WEBROOT}/auth/logout">[Logout]</a>
			  <div id="userbox" style="display:inline-block;position:absolute;bottom:100%; right: 0px; background: #ccc; border: thin solid black"></div>
 % else:
	<div style='border: thin solid black;padding: 2px 8px;float:right;margin-right:.5em;'>
	  Anonymous User&mdash;&gt;
	  <a href="/auth/login">Login</a>
 % endif
</div>
</%def>
<%def name="breadcrumb(ctxt, path)" filter="trim" cached="True" cache_key="${ context['ctxt'].db.auth.check.context()[0] }" cache_timeout="30" cache_url="breadcrumb">
	<%
		root = ctxt.root
		ctxt.chroot(0)
		menu = ctxt.get_menu()
		children = sorted( ((ctxt.db.record.get(x), y, menu.children[x,y]) for x,y in menu.keys()),
						lambda x,y: cmp(x[0]['weight'], y[0]['weight']))
		ctxt.chroot(root)
	%>
	<div class="breadcrumb">
		<script type="text/javascript">
			function dolink(elem) {
				var node = elem.getElementsByTagName('a')[0];
				window.location = node.href;
			}
			function setstatus(elem) {
				var node = elem.getElementsByTagName('a')[0];
				window.status = node.href;
			}

		</script>
		##<div class='parent breadnav'>
		##	<div>
		##		<div class='menuheading'>${menu.key[1]}</div>
		##		<div class='menu'>
		##			%for child in children:
		##				<div class='breadmenu' onclick='dolink(this)'>
		##					<a href="${ctxt.reverse('ARecord', '%s' % child[1])}">${child[1].capitalize()}</a>
		##				</div>
		##			%endfor
		##		</div>
		##	</div>
		##</div>

			    <!-- --------------------------------------------------------------------------------------------------------------------- -->
		% for rec, key, tree in children:
			<div class='breadnav child'>
				<div class='menuheading'>
					<a href="${ctxt.reverse('ARecord', '%s' % key)}">
						<div>${key.capitalize()}</div>
					</a>
				</div>
	 			<%
					subchildren = sorted( ((ctxt.db.record.get(x)['weight'], y) for x,y in tree.keys()),
						lambda x,y: cmp(x[0], y[0]))
				%>

				<div class='menu'>
					%for _ , subkey in subchildren:
						<div class='breadmenu' onclick='dolink(this)'>
							<%
								url = ctxt.reverse('ARecord', '%s/%s' % (key, subkey))
								if not url.endswith('/'): url = '%s/' % url
							%>
							<a href="${url}">${subkey}</a>
						</div>
					%endfor
				</div>

			</div>
		% endfor
		<!-- --------------------------------------------------------------------------------------------------------------------- -->

	</div>
</%def>


<%def name="person(name, ctxt)">
	<% child = ctxt.db.record.get(name) %>
	<% if child['username'] == 'root': return %>
	<div class="person_box">
		% if child['person_photo']:
				  <img src="${EMEN2WEBROOT}/download/${child['person_photo'][4:]}/${child['username']}" class="person_image" alt="Photo" />
		% else:
					<div style="width: 70px"/>
		% endif
		<div class="person_info">
			<div class="home_userinfo">
				<div class="home_userinfo_name">
					${extract(child, 'name_first', 'First Name')} ${extract(child,'name_middle','')}
					${extract(child, 'name_last', 'Last Name')}
##					<span class="e2l-small">${u' '.join(child.get('academic_degrees', []))}</span>
				</div><!-- .end home_userinfo_name -->

				<p>
					<% email = extract(child,'email') %>
					%if email:
						<a href="mailto:${email}"><em>${email}</em></a>
					%endif
				</p>

				<p>
					ph: <em>${extract(child, 'phone_voice', 'Phone')}</em> <br>
					fax: <em>${extract(child, 'phone_fax', 'Fax')}</em> <br>
					web: <em>${extract(child, 'website', 'Website')}</em>
				</p>
			</div>
		</div>
	</div>
</%def>


<%def name="extract(record, key, default=None)">
	%if record[key]:
		${record[key]}
	%else:
		${default}
	%endif
</%def>
