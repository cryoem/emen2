<%inherit file="/record/record" />


<div>

    % if commit:

        <h1>Record hidden</h1>

        <p>
            <a href="${EMEN2WEBROOT}/">Return to the home page.</a>
        <p>
    
    % else:


    <form action="" method="post">

        <h1>Hide this record?</h1>
        
        ## <p>You are considering hiding this record:</p>
        ## <ul style="list-style:none">
        ##    <li>${recnames.get(rec.name)}</li>
        ## </ul>

        <p>
            Records cannot be permanently deleted. 
            Hiding a record removes all parents and permissions, and sets a flag to mark the record as hidden.
            Administrators are still be able to view the hidden records.
        </p>
        
        % if children:
            <p>
                Please note that this record has ${len(orphans)} child records that will no longer be connected to the main record tree after hiding.
                These "orphaned" records will not be marked as hidden, but they may become difficult to find.
            </p>
                    
            <ul style="list-style:none">
                <li><input type="radio" name="childaction" value="none" checked="checked"> Do not hide children</li>
                <li><input type="radio" name="childaction" value="orphaned"> Hide ${len(orphans)} orphaned child records</li>
                <li><input type="radio" name="childaction" value="all"> Hide all ${len(children)} child records, including those connected to other records</li>
            </ul>
            
            <p>Please select carefully -- there is no "undo" action.</p>
        % endif

            <ul class="e2l-controls">
                <li>
                    <a class="e2-button" href="${EMEN2WEBROOT}/record/${rec.name}/">No, cancel</a>&nbsp;&nbsp;
                    <input type="submit" value="Yes, hide this record" />
                    <input type="hidden" name="commit" value="True" />
                </li>
            </ul>

        </form>

    % endif
    
</div>

