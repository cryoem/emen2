<%inherit file="/page" />

<%!
   import itertools
   import jsonrpc.jsonutil
   import collections
   readable_mapping = dict(
      username="User",
      ctxid="ctxid",
      response_code="Response Code",
      rtime='Time'
   )
   skipped = set(['host', 'resource', 'cputime', 'request'])
   get_readable = lambda key: readable_mapping.get(key, key.capitalize())
   def group_dict(d, func):
      out = collections.defaultdict(list)
      for k,v in d.iteritems():
         out[func(k)].extend(v)
      return out
%>

<!-- tmp -->
<%def name="th(field)" filter="trim">
   %if field != name:
      <th class='${field}'>${get_readable(field)}</div></th>
   %endif
</%def>
<%def name="element(data, elem, align)" filter="trim">
   %if elem != name:
      <td class='${align} ${elem}' style="position:relative">
           ${str(data[elem])}</td>
   %endif
</%def>

<%def name="layoutdata(data)" filter="trim">
   <div id="accordion">
        <%
         counter = 0
      %>
      %for key, values in sorted(group_dict(data, norm.norm).items(), lambda x,y:(cmp(y,x) if viewargs['reverse'] else cmp(x,y))):
           <%
               counter += 1
               ke = norm.unnorm(key)
            %>
            <h3 id="key"><a href="#${(str(key) or '').replace(' ','')}">${ke}</a></h3>
            <div class='databox' data-key="${ke}">
               <table id="dataset_${counter}" class="dataset" style="width:100%;">
                  <thead>
                     <tr>
                        % for v,_ in values[0].order:
                           % if v not in skipped:
                              <%self:th field='${v}' />
                           % endif
                        % endfor
                        <th>Request</th>
                     </tr>
                  </thead>
                  <tbody>
                     %for value in values:
                        ${caller.body(value=value, skip=data_name, rclass="")}
                     %endfor
                  </tbody>
                  <tfoot></tfoot>
               </table>
         </div>
      %endfor
   </div>
</%def>

<%def name='head()'>
   ${parent.head()}
   <script>

      jQuery('body').ready(function() {

         var x = $('#buttons_main .button').last();
         $('#menu').css('left', x.position().left + x.outerWidth());

         $('.btn').button();

         function keydown(event) {
            var keyCode = $.ui.keyCode;
            if (!event.altKey && !event.ctrlKey) {
               switch (event.keyCode) {
                  case keyCode.ENTER:
                  case keyCode.SPACE:
                     $(event.target).trigger('click');
                     break;
               }
            };
         }

         $('.paginate_button').attr('tabIndex', '0')
                              .bind('keydown', function(event) {keydown(event)});

         /*table = $('.dataset').dataTable({
            'bPaginate': true, 'bJQueryUI': true,
            'oSearch': {'sSearch': ${jsonrpc.jsonutil.encode(filter_str)}},
            "sScrollX": "100%",
            "sScrollXInner": "110%"

            //'bAutoWidth': false
         }); */

         $('#accordion').accordion1({
            'autoHeight': false, 'navigation': true,
            'collapsible': true, 'helpDialog': $('#help'),
            'helpTrigger': '.showhelp'
         });

         $('#submitS').click( function () {
            var data = $('#search input').serializeArray(),
                  o = "";
            window.location.pathname += o;
         });

       });
   </script>


  <style type="text/css">
      table {
         max-width: 100%;
      }

      .dataset, .dataset td {
         border-spacing: 0px;
         border-collapse: collapse;
         border: 1px #BBD9EE solid;
         border-bottom: 0px;
      }

      td, .dataset td {
         vertical-align: middle;
         border-left: 0px;
         border-right: 0px;
         overflow: auto;
      }
      
      .dataset td {
         max-width: 23em;
      }

      th { 
        text-align: center;
        vertical-align: middle;
        white-space: nowrap;
      }

      .right { text-align: right; }
      .left { text-align: left; }
      .center { text-align: center; }

      .css_right { 
         width: 16px;
         float: right;
         margin-left: .1em;
         display: block;
      }

      .dataTables_length { float: right; }
      .dataTables_filter { float: right; }
      .dataTables_info { float: left; }
      .dataTables_paginate { float: right; }
      .fg-button {
         float: left;
         background:transparent;
         margin: .25em;
      }
      .fg-button + .fg-button {
         margin-left:0
      }

      .even { background: #F0F2FF; }

      .ui-button {
         background: #F0F2FF;
         border: thin #efe1ee solid;
         padding: 0em .1em;
         margin: 0em .1em;
         font-size: 10pt;
      }

      .databox {
         overflow: hidden
      }

      ##.request { white-space: nowrap}
   </style>
</%def>

<h3>Grouped by: ${get_readable(name)}</h3>

<div id="menu" style="">
   <%! kinds = set(['host', 'rtime', 'username', 'response_code', 'size', 'ctxid', 'request', 'resource']) %>
   %for kind in kinds - skipped:
      <a class='btn' href="${ctxt.reverse('LogAnalysis/access', dataset=kind, **viewargs)}">${get_readable(kind)}</a>
   %endfor
   <a href="javascript:null" style="margin-left:.1em" class="btn showhelp">Press '?' for help</a>
   <br/>
   <div id="search">
      <label for="username">User</label><input name="username" type="text" />
      <div class="btn" id="submitS">Search...</div>
   </div>
   <a href="javascript:null" id="tmpbtn" class="btn">Some text</a>
</div>

<hr/>

<div>
  <%self:layoutdata data="${dataset}" args="value,skip,rclass">
         <tr class="value">
            <% align = dict(host='left', username='left', request='left', size='right') %>
            % for v,_ in value.order:
               % if v not in skipped:
                  <%self:element data='${value}' elem='${v}' align='${align.get(v, "center")}' />
               % endif
            % endfor
            <%self:element data='${value}' elem='request' align='${align.get("request", "center")}' />
         </tr>
   </%self:layoutdata>
   <hr/>
</div>

% if errors:
   <div id="errors">
   <h2>Unparseable lines:</h2>
   <ul>
      %for line in errors:
         <li>${line}</li>
      %endfor
   </ul>
   </div>
% endif

<div id="help"> </div>

