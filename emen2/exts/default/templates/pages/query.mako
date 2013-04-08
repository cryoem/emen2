<%! import uuid %>

<%def name="table(q, parent=None, rectype=None, qc=True, header=True, controls=True)">
    <%
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
            <div class="e2-tab e2-tab-editbar" data-tabgroup="query" role="tablist">
                <ul class="e2-query-header e2l-cf" role="tab"></ul>
            </div>

            <div class="e2-tab e2-tab-editbar" data-tabgroup="query" role="tabpanel"></div>
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
								<a href="${ctxt.root}/record/${name}/">${q['rendered'][name].get(key)}</a>
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
