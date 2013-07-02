<%! import uuid %>

<%def name="table(q, parent=None, rectype=None, qc=True, header=True, controls=True)">
    <%
        checkbox = q.get('checkbox', False)
        keytype = q.get('keytype', 'record')
        tname = uuid.uuid4().hex
    %>
    <script type="text/javascript">
    //<![CDATA[
        var q${tname} = ${q | n,jsonencode};
        $(document).ready(function() {
            $("#${tname}").TableControl({
                q: q${tname}, 
                rectype: ${rectype | n,jsonencode},
                parent: ${parent | n,jsonencode},
                header: ${header | n,jsonencode},
                controls: ${controls | n,jsonencode},
                qc: ${qc | n,jsonencode}
            })
        });    
    //]]>
    </script>

    <div class="e2-query" id="${tname}">
        
        % if controls:
            <div class="e2-tab e2-tab-query" data-tabgroup="query" role="tablist">
                <ul class="e2-query-header e2l-cf" role="tab"></ul>
            </div>

            <div class="e2-tab e2-tab-query" data-tabgroup="query" role="tabpanel"></div>
        % endif

        ## This form is used for editing table cells
        <form class="e2-query-tableform" method="post" action="${ctxt.reverse('Records/edit')}">
            ## <input type="hidden" name="_redirect" value="" />
            <table class="e2-query-table e2l-shaded" > 

                % if header:
                    <thead>
                        <tr>
                            % for key in q['keys']:
                                <th><div data-name="${key}">${q['keys_desc'].get(key, key)}</div></th>
                            % endfor
                        </tr>
                    </thead>
                % endif

                <tbody>
            
                    % if not q['names']:
                        <tr><td colspan="0">No Records found for this query.</td></tr>
                    % endif

                    % for name in q['names']:
                        <tr>                   
                                                                             
                        % for key in q['keys']:
                            <td>
                                ## Inelegant, but will do for now...
                                % if key == 'thumbnail()':
                                    <a href="${ctxt.root}/${keytype}/${name}/"><img class="e2l-thumbnail" src="${ctxt.root}/${q['rendered'][name].get(key)}" alt="Thumb" /></a>
                                % elif key == 'checkbox()':
                                    <input class="e2-query-checkbox" type="checkbox" checked="checked" name="name" value="${name}" data-name="${name}" />
                                % else:
                                    <a href="${ctxt.root}/${keytype}/${name}/">${q['rendered'][name].get(key)}</a>
                                % endif
							</td>
                        % endfor
                        
                        </tr>
                    % endfor            

                </tbody>

            </table>
        
        </form>
        
    </div>
    
</%def>

${table(q, rectype=rectype, parent=parent, header=header, controls=controls, qc=False)}
