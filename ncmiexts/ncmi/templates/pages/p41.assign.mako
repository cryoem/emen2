<%inherit file="/page" />
<%namespace name="buttons" file="/buttons"  /> 

<h1>Assign P41 Subproject IDs</h1>

<p>This shows all P41 projects that have been created anywhere in the system, for all years. The P41 "Subproject ID" is an identifier that carries over year-to-year in their system. Logically, we'd just use EMEN2 record ID's, but the Subproject ID is restricted to 4 characters. This form will allow you to set/edit all Subproject IDs. P41 projects that do not have one assigned will be given the next sequential one available. Hit 'Save' below to commit the changes.</p>

<form method="post" action="">

<table>
    <thead>
        <tr>
            <th>Project</th>
            <th></th>
            <th>Current SID</th>
            <th>New SID</th>
        </tr>
    </thead>
    <tbody>
        % for i in p41_projects:
            <tr>
                <td>${i.name}</td>
                <td>${recnames.get(i.name)}</td>
                <td>${i.get('p41_subprojectid', '')}</td>
                <td><input type="text" name="${i.name}.p41_subprojectid" value="${assign.get(i.name, '')}" /></td>
            </tr>
        % endfor
    </tbody>
</table>

<input type="submit" value="Save" /> 

</form>