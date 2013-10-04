<%!
import jsonrpc.jsonutil
import collections
%>

<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

<%
recs_d = {}
for i in recs:
    recs_d[i.name] = i
    
year = rec.get('year')

p41_percent_total = 0
for project in p41_projects_included:
    p41_percent_total += recs_d[project].get('p41_percent', 0)

%>


<%def name="istab(tab1, tab2)">
    % if tab1 == tab2:
        class="e2-tab-active"
    % endif
</%def>

<%block name="js_ready">
    ${parent.js_ready()}

    // Intialize the Tab controller
    var tab = $("#e2-tab-record");        
    tab.TabControl({
        'cb': function(page) {
			// edit..
		}    
    });

    $('input.p41_percent').change(function() {
        var total = 0;
        $('input.p41_percent').each(function() {
            var t = parseInt($(this).val());
            total += t;
        });
        $("#p41_percent_total").html(total);
    })
    
</%block>


<div class="e2l-sidebar-sidebar" style="width:400px;"> 
    <ul id="e2-tab-record" class="e2l-cf e2l-sidebar-projectlist" role="tablist" data-tabgroup="record">

        <li role="tab" data-tab="summary-main"><h2 class="e2l-gradient"><a href="#main">Summary</a></h2></li>
        <li role="tab" data-tab="summary-projects"><a href="#summary-projects">Projects summary</a></li>
        <li role="tab" data-tab="summary-included"><a href="#summary-included">Projects included</a></li>
        <li role="tab" data-tab="summary-percent"><a href="#summary-percent">Percent effort</a></li>
        <li role="tab" data-tab="summary-publications"><a href="#summary-publications">Publications</a></li>
        <li role="tab" data-tab="summary-users"><a href="#summary-users">Users</a></li>


        ## Projects
        <li role="tab" ><h2 class="e2l-gradient">Projects</h2></li>
        % for project in p41_projects_included:
            <li role="tab" data-tab="project-${project}" class="project-editor"><a href="#project-${project}">${recnames.get(project)}</a></li>
        % endfor



    </ul>
</div>



<form method="post" action="${ctxt.root}/record/${rec.name}/p41report/save/">

<div class="e2-tab e2-tab-record e2l-sidebar-main" data-tabgroup="record" role="tabpanel" style="margin-left:400px">

    ## This section comes first, so values in the summary pages will override
    % for project in p41_projects_included:
        <div data-tab="project-${project}">
            <div data-edit="true" data-name="${project}" data-viewname="mainview" class="e2-view">
                ${rendered.get(project)}
            </div>
            <ul class="e2l-actions">
                <li><input type="submit" value="Save edited projects" /></li>
            </ul>
        </div>
    % endfor



    
    <div data-tab="summary-main" class="e2-tab-active">
        <h1>P41 Report Summary</h1>    

        <table class="e2l-kv" >
            <tbody>
                <tr><td>Report year</td><td>${rec.get('p41_year')}</td></tr>
                <tr><td>Projects</td><td>${len(p41_projects_included)}</td></tr>
                <tr><td>Publications</td><td>${len(publications_included)}</td></tr>
                <tr><td>Users</td><td>${len(users)}</td></tr>
                <tr><td>Total % effort</td><td>${p41_percent_total}</td></tr>
            </tbody>
        </table>

        <p>
            <strong>Notes:</strong>
            Publications and users sections of this form will be done Monday.
        </p>


        <ul class="e2l-actions">
            <li><a class="e2-button" href="${ctxt.root}/record/${rec.name}/p41report/xml/">Export XML</a></li>
        </ul>

    </div>



    <div data-tab="summary-projects">    
        <%
            projects = map(recs_d.get, p41_projects_included)
            projects_type_percent = collections.defaultdict(list)
            for project in projects:
                projects_type_percent[project.get('p41_project_type')].append(project.get('p41_percent', 0))
        %>

        <h1>Projects summary</h1>
        
        <table class="e2l-shaded" >
            <thead>
                <th>Project Type</th>
                <th>Count</th>
                <th>% of Projects</th>
                <th>% of Effort</th>
            </thead>

            <tbody>
                % for k,v in projects_type_percent.items():
                    <tr>
                        <td>${k}</td>
                        <td>${len(v)}</td>
                        <td>${"%0.1f"%(len(v) / float(len(p41_projects_included)))} % </td>
                        <td>${sum(v)}</td>
                    </tr>
                % endfor
            </tbody>
        </table>
        
    </div>
    
    
    <div data-tab="summary-included">
        <%
            reports = map(recs_d.get, p41_reports)
            reports = sorted(reports, key=lambda x:x.get('p41_year'))
        %>
        
        <h1>Projects included</h1>
    
        <table class="e2l-shaded" >
            <thead>
                <tr>
                    <th>Project</th>
                    % for report in reports:
                        <th>${report.get('p41_year')}</td>
                    % endfor
                </tr>
            </thead>
            <tbody>
                % for project in sorted(p41_projects, key=lambda x:recnames.get(x,'').lower()):
                    <%
                    r = recs_d[project]
                    if not r.parents or r.get('hidden'):
                    	continue
                    %>
                  <tr>
                        <td>${recnames.get(project)} (${project})</td>
                        % for report in reports:
                            <%
                                disabled = ""
                                if report.name != rec.name:
                                    disabled = 'disabled="disabled"'
                                checked = ""
                                if project in report.children:
                                    checked = 'checked="checked"'
                            %>
                            <td>
                                <input type="hidden" name="linked_all" value="${project}" />
                                <input type="checkbox" name="linked" value="${project}" ${checked} ${disabled} />
                            </td>
                        % endfor
                    </tr>
                % endfor
            </tbody>
        </table>
        <br /><br />
        <ul class="e2l-actions">
            <li><input type="submit" value="Save included projects" /></li>
        </ul>
    </div>
    
    
    
    <div data-tab="summary-percent">
        <h1>Percent effort allocation: total <span id="p41_percent_total">${p41_percent_total}</span> % </h1>
    
        <table class="e2l-shaded" >
            <thead>
                <tr>
                    <th>Project</th>
                    <th>Percent effort %</th>
                </tr>
            </thead>
            <tbody>
                % for project in p41_projects_included:
                    <tr>
                        <td>${recnames.get(project)}</td>
                        <td>
                            <input type="text" name="${project}.p41_percent" value="${recs_d[project].get('p41_percent', 0)}" class="p41_percent" autocomplete="off" />
                        </td>
                    </tr>
                % endfor
            </tbody>
        </table>
        <br /><br />
        <ul class="e2l-actions">
            <li><input type="submit" value="Save percent effort" /></li>
        </ul>        
    </div>
    
    

    <div data-tab="summary-publications">
        <h1>Publications (${len(publications_included)})</h1>
        
        <%
        pubtypes = collections.defaultdict(set)
        for i in map(recs_d.get, publications_included):
            pubtypes[i.rectype].add(i.name)
        %>
        <table class="e2l-shaded">
            <thead>
                <tr>
                    <th>Type</th>
                    <th>Count</th>
                </tr>
            </thead>
            <tbody>
            % for k,v in pubtypes.items():
                <tr>
                    <td>${k}</td>
                    <td>${len(v)}</td>
                </tr>
            % endfor
            </tbody>
        </table>
        
        % for k,v in pubtypes.items():
        <h2>${k}</h2>
        <ul>
            % for i in sorted(v, key=lambda x:recnames.get(x,x).lower()):
                <li>${recnames.get(i,i)}</li>
            % endfor
        </ul>
        % endfor

    </div>


    
    <div data-tab="summary-users">
        <h1>Users (${len(users)})</h1>
        % for user in users:
            ${buttons.infobox(user, autolink=True)}
        % endfor

        ## <ul>
        ## % for user in users:
        ##    <li>${user.displayname}</li>
        ## % endfor
        ## </ul>
    </div>





</div>

</form>
