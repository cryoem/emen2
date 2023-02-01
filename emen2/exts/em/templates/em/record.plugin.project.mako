<%! import emen2.util.listops %>

<%namespace name="buttons" file="/buttons"  /> 

<%
recorddefs_d = emen2.util.listops.dictbykey(recorddefs, 'name')
%>

<script type="text/javascript">
    $(document).ready(function() {

        ## Recent activity viewer
        var q = ${recent_activity | n,jsonencode}; 
        $('#recent_activity').PlotHistogram({
            q:q,
            pan: false,
            height:200,
        });

        ## New record controls
        $('.e2-record-new').RecordControl({});
        $('.e2-record-edit').RecordControl({});    
    });
</script>    


<h1>Recent activity</h1>

<div id="recent_activity">
    <div class="e2-plot"></div>
</div>

<h1>
    Sub-projects (${len(subprojects)})
    <ul class="e2l-actions">
        <li><a href="" class="e2-button e2-record-new" data-rectype="project" data-parent="${name}">${buttons.image('edit.png')} New</a></li>
    </ul>
</h1>

<ul>
% for subproject in subprojects:
    <li><a href="${ROOT}/record/${subproject}/">${recnames.get(subproject, subproject)}</a></li>
% endfor
</ul>

<h1>In this project...</h1>

<table class="e2l-shaded" >
    
    ## Ugly; make the comparison key a function
    % for rectype,items in sorted(children_grouped.items(), key=lambda x:recorddefs_d.get(x[0], dict()).get('desc_short')):
        <tbody>

            <tr>
                <td colspan="2"  class="e2l-gradient">
                    <strong style="display:inline-block;padding:8px;padding-left:0px;">
                        ${recorddefs_d.get(rectype, dict()).get('desc_short')} (${len(items)})
                    </strong>
                        <ul class="e2l-actions">
                            <li><span class="e2-button e2-record-new" data-rectype="${rectype}" data-parent="${name}">${buttons.image('edit.png')} New</span></li>
                            <li><a class="e2-button" href="${ROOT}/query/children.is.${name}*/rectype.is.${rectype}/">View all</a></li>
                        </ul>

                </td>
            </tr>

            % for item in sorted(items & recent, reverse=True):
                <tr class="e2l-shaded-indent">
                    <td>
                        <a href="${ROOT}/record/${item}/">${recnames.get(item, item)}</a>
                    </td>
                    <td>
                        <a href="${ROOT}/record/${item}/">${rendered_thumb.get(item,'')}</a>
                    </td>
                </tr>
            % endfor
            
            % if len(items) > 3:
                <tr class="e2l-shaded-indent">
                    <td colspan="2">
                        <a href="${ROOT}/query/children.is.${name}*/rectype.is.${rectype}/">... more</a>
                    </td>
                </tr>
            % endif

        </tbody>
    % endfor

</table>
