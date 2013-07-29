<%!
import collections
import operator
import jsonrpc.jsonutil
%>
<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

<%
year = rec.get("p41_year")
%>


<%block name="js_ready">    
    $('input[name=p41include]').change(function() {
        var yearname = $(this).attr('data-yearname');
        var name = $(this).attr('data-name');
        var year = $(this).attr('data-year');
        var method = "rel.pcunlink";
        if ($(this).attr('checked')) {
            method = "rel.pclink";
        }
        emen2.db(method, [year, name], function() {
            if (method == "rel.pclink") {notify("Added "+name+" to "+yearname+" report")}
            if (method == "rel.pcunlink") {notify("Removed "+name+" from the "+yearname+" report")}                
        });
    })
</%block>        


<h1 id="p41years">Projects and Years Included</h1>

<%
p41_years_sorted = sorted(p41_years.items())
p41_included = []
p41_notincluded = []

for i in p41_index:
    inc = False
    for yrec in p41_years.values():
        if yrec.name in p41_project_parents.get(i):
            inc = True

    if inc:
        p41_included.append(i)
    else:
        p41_notincluded.append(i)
    

%>


<table>
    <thead>
        <th>Project</th>
        % for yrec_year, yrec in p41_years_sorted:
            <th><a href="${ctxt.root}/record/${yrec.name}">${yrec_year}</a></th>
        % endfor
    </thead>
    
    <tbody>
    
    % for count, i in enumerate(sorted(p41_included, key=recnames.get)):
        
        % if count % 2:
            <tr>
        % else:
            <tr class="s">    
        % endif

            <td><a href="${ctxt.root}/record/${i}/">${recnames.get(i)}</a></td>
            
            % for yrec_year, yrec in p41_years_sorted:
                <td>
                    
                    % if yrec.name in p41_project_parents.get(i):
                        <input type="checkbox" name="p41include" checked="checked" data-yearname="${yrec_year}" data-name="${i}" data-year="${yrec.name}" />
                    % else:
                        <input type="checkbox"  name="p41include" data-name="${i}"  data-yearname="${yrec_year}" data-year="${yrec.name}" />
                    % endif
                    
                </td>
            % endfor
        
        </tr>
            
    % endfor


    <tr>
        <td>Projects that do not seem to be included in any year...</td>
    </tr>
    
    % for count, i in enumerate(sorted(p41_notincluded, key=recnames.get)):
        
        % if count % 2:
            <tr>
        % else:
            <tr class="s">    
        % endif

            <td><a href="${ctxt.root}/record/${i}/">${recnames.get(i)}</a></td>
            % for yrec_year, yrec in p41_years_sorted:
                <td>
                    
                    % if yrec.name in p41_project_parents.get(i):
                        <input type="checkbox" name="p41include" checked="checked" data-yearname="${yrec_year}" data-name="${i}" data-year="${yrec.name}" />
                    % else:
                        <input type="checkbox"  name="p41include" data-name="${i}"  data-yearname="${yrec_year}" data-year="${yrec.name}" />
                    % endif
                    
                </td>
            % endfor
        
        </tr>
            
    % endfor
    



    </tbody>

</table>
