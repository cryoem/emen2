<%! 
    import markdown 
    import jsonrpc.jsonutil
%>
<%inherit file="/page" />
<%namespace name="buttons" file="/buttons" /> 
<%namespace name="forms" file="/forms"  /> 


<%block name="js_ready">
    ${parent.js_ready()}
    ${buttons.tocache(recorddef)}
    $('#e2-relationships').RelationshipControl({
        edit: ${jsonrpc.jsonutil.encode(edit)}
    });

    $('.e2-tree').TreeControl({'attach':true});
    $('#recorddef-views').TabControl();

</%block>

<%block name="precontent">
    ${parent.precontent()}
    <div class="e2-tree-main" style="overflow:hidden">${parentmap}</div>
</%block>


<form method="post" action="">


<h1>
    ${title}
    <ul class="e2l-actions">
        % if new or edit:
            <li><input type="submit" value="Save">
        % else:
            <li><a class="e2-button" href="${EMEN2WEBROOT}/query/rectype.is.${recorddef.name}/">${buttons.image('query.png', 'Query')} Query</a></li>
            <li><a class="e2-button" href="${EMEN2WEBROOT}/recorddef/${recorddef.name}/edit/">${buttons.image('edit.png', 'Edit')} Edit</a></li>
            <li><a class="e2-button" href="${EMEN2WEBROOT}/recorddef/${recorddef.name}/new/"><img src="${EMEN2WEBROOT}/static/images/edit.png" alt="New" /> New</a></li>
        % endif
    </ul>
        
</h1>




<%buttons:singlepage label='Details'>
    <table class="e2l-kv">
        <tr>    
            <td>Name:</td>
            <td>
                % if new:
                    <input name="name" value="" required="required" />
                % else:
                    ${recorddef.name or ''}
                % endif
            </td>
        </tr>

        <tr>
            <td>Short description:</td>
            <td>
                % if edit:
                    <input name="desc_short" value="${recorddef.desc_short or ''}" required />
                % else:
                    ${recorddef.desc_short or ''}
                % endif
            </td>
        </tr>

        <tr>
            <td>Detailed description:</td>
            <td>
                % if edit:
                    <textarea class="e2l-fw" name="desc_long" required="required" >${recorddef.desc_long or ''}</textarea>
                % else:
                    ${recorddef.desc_long or ''}
                % endif
            </td>
        </tr>
        
        <tr>
            <td>Private:</td>
            <td>
                % if edit:
                    <input type="checkbox" value="True" name="private" ${forms.ifchecked(recorddef.private)} />
                % else:
                    ${recorddef.private}
                % endif
            </td>
        </tr>
        
        
        <tr>
            <td>
                Suggested child records:
            </td>
            <td>
                <ul class="e2l-nonlist">
                % if edit:
                    % for i in recorddef.typicalchld or []:                    
                        <li><input type="text" name="typicalchld" value="${i}" /></li>
                    % endfor
                        <li><input type="text" name="typicalchld" /></li>
                        <li><input type="text" name="typicalchld" /> <input class="e2-typicalchld-addtypicalchld" type="button" value="+" /></li>
                % else:
                    % for i in recorddef.typicalchld or []:
                        <li>${i}</li>
                    % endfor
                % endif
                </ul>
                <input type="hidden" name="typicalchld" value="" />
            </td>
        </tr>        
    </table>
</%buttons:singlepage>






<%buttons:singlepage label='Main Protocol'>
    % if new or (edit and ADMIN):
        <textarea name="mainview" rows="10" required="required">${recorddef.mainview}</textarea>
    % else:
        ${markdown.markdown(recorddef.mainview)}
    % endif
</%buttons:singlepage>






<div class="e2-tab e2-tab-switcher" id="recorddef-views">
    <ul class="e2l-cf">
    
        <%
        v = recorddef.views.items()
        if new or edit:
            v.append(['', ''])
            v.append(['', ''])
            v.append(['', ''])
        %>
    
        % for count, (key, view) in enumerate(v):
            % if count == 0:
                <li class="e2-tab-active" data-tab="${count}">
                    ${key or 'New view'}
                </li>
            % else:
                <li data-tab="${count}">
                    ${key or 'New view'}
                </li>
            % endif
        % endfor
    </ul>


    % for count, (key, view) in enumerate(v):
        % if count == 0:
            <div class="e2-tab-active" data-tab="${count}">
        % else:
            <div data-tab="${count}">
        % endif
            
        % if edit:
            <strong>&nbsp;View name:</strong> <input type="text" name="view_name" value="${key}" /><br />
            <textarea rows="10" name="view_view">${view}</textarea>
        % else:            
            ${markdown.markdown(view)}
        % endif
        </div>
    % endfor
    
    <input type="hidden" name="view_name" value="" />
    <input type="hidden" name="view_view" value="" />
    
</div>





% if not new:
    <%buttons:singlepage label='History'>
        <table class="e2l-kv">
            <tr>
                <td>Created:</td>
                <td><a href="${EMEN2WEBROOT}/user/${recorddef.creator}">${recorddef.creator}</a> @ <time class="e2-localize" datetime="${recorddef.creationtime}">${recorddef.creationtime}</time></td>
            </tr>

            <tr>
                <td>Modified:</td>
                <td><a href="${EMEN2WEBROOT}/user/${recorddef.modifyuser}">${recorddef.modifyuser}</a> @ <time class="e2-localize" datetime="${recorddef.modifytime}">${recorddef.modifytime}</time></td>
            </tr>
        </table>
    </%buttons:singlepage>
% endif





<%buttons:singlepage label='Relationships'>
    <div id="e2-relationships" data-name="${recorddef.name}" data-keytype="${recorddef.keytype}"></div>
</%buttons:singlepage>


</form>