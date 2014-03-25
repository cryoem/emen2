<%page expression_filter="x"/>



<%
project_type_map = {"Technical_Core":"T","Dissemination":"D","Collaboration":"C","Service":"S"}
publication_rectype_map = {"publication":"J", "publication_abstract":"A", "publication_book":"B"}
yes_no_map = {None:"N",0:"N",1:"Y","0":"N","1":"Y"}

state_abbrs = {'wyoming': 'WY', 'colorado': 'CO', 'washington': 'WA', 'hawaii': 'HI', 'tennessee': 'TN', 'wisconsin': 'WI', 'nevada': 'NV', 'maine': 'ME', 'north dakota': 'ND', 'mississippi': 'MS', 'south dakota': 'SD', 'new jersey': 'NJ', 'oklahoma': 'OK', 'delaware': 'DE', 'minnesota': 'MN', 'north carolina': 'NC', 'illinois': 'IL', 'new york': 'NY', 'arkansas': 'AR', 'indiana': 'IN', 'maryland': 'MD', 'louisiana': 'LA', 'idaho': 'ID', 'arizona': 'AZ', 'iowa': 'IA', 'west virginia': 'WV', 'michigan': 'MI', 'kansas': 'KS', 'utah': 'UT', 'virginia': 'VA', 'oregon': 'OR', 'connecticut': 'CT', 'montana': 'MT', 'california': 'CA', 'massachusetts': 'MA', 'rhode island': 'RI', 'vermont': 'VT', 'georgia': 'GA', 'pennsylvania': 'PA', 'florida': 'FL', 'alaska': 'AK', 'kentucky': 'KY', 'nebraska': 'NE', 'new hampshire': 'NH', 'texas': 'TX', 'missouri': 'MO', 'south carolina': 'SC', 'ohio': 'OH', 'alabama': 'AL', 'new mexico': 'NM'}

recs_d = {}
for i in recs:
    recs_d[i.name] = i
users_d = {}
for i in users:
    users_d[i.name] = i


%>

<%def name="iftag(tag, value)"> 
    % if value not in ["None", None, ""]:
    <${tag}>${value}</${tag}>
    % endif
</%def>



<%def name="pub_body(p)"> 
    <%
    body = 'Unknown Publication Type'
    if p.rectype == 'publication':
        body = "%s (%s). %s. %s, %s:%s."%(", ".join(p["author_list"]),p["journal_date"],p["title_publication"],p["name_journal"],p["journal_volume"],p["page_range"])
    elif p.rectype == 'publication_abstract':
        body = "%s (%s). %s. %s. %s."%(", ".join(p.get("author_list",[])),p["year_published"],p["title_publication"],p["name_conference"],p["city_conference"])
    elif p.rectype == 'publication_book':
        body="%s (%s). "%(", ".join(p["author_list"]), p["year_published"])
        if p["name_chapter"] and len(p["name_chapter"])>2 : body+="%s. In:"%p["name_chapter"]
        body+=" %s."%p["name_book"]
        if p["author_editor_list"] and len(p["author_editor_list"])>0 :
            body+=", ".join(p["author_editor_list"])+" (ed)."
        if p["publisher"] : body+=p["publisher"]+'.'
        else: print "Unknown Publisher %d"%i
    %>
    ${body}
</%def>




<P41_Progress_Report xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://sis.ncrr.nih.gov" xsi:schemaLocation="http://sis.ncrr.nih.gov http://APRSIS.NCRR.NIH.GOV/XML/p41_progress_report.xsd">

<Grant_Info>
    <Serial_Number>${str(rec["p41_serial"]).zfill(6)}</Serial_Number>
    <Fiscal_Year>${rec['p41_year']+1}</Fiscal_Year>
    <Reporting_To_Date>${rec["p41_report_end_date"][:10]}</Reporting_To_Date>
    <Reporting_From_Date>${rec["p41_report_start_date"][:10]}</Reporting_From_Date>
    <Project_Title>${rec["p41_title"]}</Project_Title>
    <Recipient_Institution_Name>${rec["institution"]}</Recipient_Institution_Name>
    <Activity_Code>P41</Activity_Code>
    <Director_Person_ID>${users_d.get(rec["grant_pi"]).record}</Director_Person_ID>
    <Patent_Or_Copyright_Award>N</Patent_Or_Copyright_Award>
</Grant_Info>



% for user in users:

    <Person Person_ID="${user.record}">
        <%
        address_state = user.userrec.get('address_state', '').lower()
        %>
        
        <Last_Name>${user.userrec['name_last']}</Last_Name>
        <First_Name>${user.userrec['name_first']}</First_Name>
        <Full_Name>${user.displayname}</Full_Name>

        % for degree in user.userrec.get('academic_degrees', []):
            <Academic_Degree>${degree.upper()}</Academic_Degree>        
        % endfor

        ${iftag('Phone_Number', user.userrec.get('phone'))}
        ${iftag('Fax_Number', user.userrec.get('phone_fax'))}
        ${iftag('Email_Address', user.email)}
        ${iftag('Department', user.userrec.get('department'))}

        % if user.userrec.get('institution','').lower() not in ['baylor college of medicine', 'bcm'] and user.userrec.get('institution'):
            ${iftag('Nonhost_Name', user.userrec.get('institution',''))}
                % if user.userrec.get('country', '').lower() in ['us', 'usa'] or user.userrec.get('country', '').lower().startswith('united states'):
                    ${iftag('Nonhost_State', state_abbrs.get(address_state, address_state).upper())}
                    <Nonhost_Country>USA</Nonhost_Country>
                % else:
                    <Nonhost_Country>${user.userrec.get('country')}</Nonhost_Country>
                % endif
        % endif    

    
        % for grant in grants_by_user.get(user.name, []):
            % if grant['grant_source'] == 'NIH':
                <Federal_PHS_Funding>
                    <Organization>${grant['grant_source']}</Organization>
                    % for project in projects_by_grant.get(grant.name, []):
                        <Sub_ID>${project}</Sub_ID>
                    % endfor
                    <Grant_Or_Contract_Number>${grant['grant_number']}</Grant_Or_Contract_Number>
                    <Total_Support_Funds>${grant.get('grant_funds', 0)}</Total_Support_Funds>
                </Federal_PHS_Funding>                                    
            % elif grant['grant_source'] == 'USA_Federal':        
                <Federal_Non_PHS_Funding>
                    <Organization>${grant['grant_source']}</Organization>
                    % for project in projects_by_grant.get(grant.name, []):
                        <Sub_ID>${project}</Sub_ID>
                    % endfor                    
                    <Grant_Or_Contract_Number>${grant['grant_number']}</Grant_Or_Contract_Number>
                    <Total_Support_Funds>${grant.get('grant_funds', 0)}</Total_Support_Funds>
                </Federal_Non_PHS_Funding>                            
            % else:
                <Non_Federal_Funding>
                    % if grant['grant_source_type'] == 'Industry':
                        <Source_Type>IND</Source_Type>
                    % else:
                        <Source_Type>FDN</Source_Type>
                    % endif
                    % for project in projects_by_grant.get(grant.name, []):
                        <Sub_ID>${project}</Sub_ID>
                    % endfor
                    <Organization_Name>${grant['grant_source']}</Organization_Name>
                    <Grant_Or_Contract_Number>${grant['grant_number']}</Grant_Or_Contract_Number>
                    <Total_Support_Funds>${grant.get('grant_funds', 0)}</Total_Support_Funds>
                </Non_Federal_Funding>
            % endif
        % endfor    
    
        
    </Person>

% endfor




% for project in map(recs_d.get, p41_projects_included):

    <%
    ## print "Processing project: ", project.name
    %>

    <Subproject Sub_ID="${project.name}">
        <Subproject_ID>${project['p41_subprojectid']}</Subproject_ID>
        <Title>${project['p41_project_title']}</Title>
        <AIDS_Flag>N</AIDS_Flag>
        <Abstract>${project['p41_abstract']}</Abstract>
        <Type>${project_type_map.get(project['p41_project_type'])}</Type>
        <Progress>${project['p41_progress']}</Progress>

        <Investigator>
            <Person_ID>${users_d[project['p41_project_pi']].record}</Person_ID>
            <Investigator_Type>P</Investigator_Type>
        </Investigator>

        % for investigator in set(project.get("p41_project_investigators", [])):
            % if investigator != project['p41_project_pi']:
                <Investigator>
                    <Person_ID>${users_d[investigator].record}</Person_ID>
                    <Investigator_Type>C</Investigator_Type>
                </Investigator>
            % endif
        % endfor

        % for pub in project.children & publications_included:
            <Publication_ID>${pub}</Publication_ID>
        % endfor

        <Percent_Grant_Dollars>${project.get('p41_percent',0)}</Percent_Grant_Dollars>
    </Subproject>

% endfor






% for pub in map(recs_d.get, publications_included):

    <Publication Publication_ID="${pub.name}">
        <Publication_Type>${publication_rectype_map[pub.rectype]}</Publication_Type>
        <In_Press>N</In_Press>
        ## <In_Press>${yes_no_map[pub.get('publication_in_press')]}</In_Press>        
        <Resource_Acknowledged>Y</Resource_Acknowledged>

        ## if pub.get('pmcid'):
        ##    <PM_UID>${pub['pmcid']}</PM_UID>
        % if pub.get('pmid'):
            <PM_UID>${pub['pmid']}</PM_UID>
        % else:
            <Body>${pub_body(pub)}</Body>
        % endif

    </Publication>

% endfor



</P41_Progress_Report>




