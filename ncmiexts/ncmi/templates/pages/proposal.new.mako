<%inherit file="/page" />

% if user==None:

<p>You must request a <a href="${ctxt.root}/users/new/">new user account</a> to begin the proposal process. Please enter all contact information.</p>

<p>If you have created your account, please <a href="${ctxt.root}/login/?uri=${ctxt.root}/proposals/new/">login to begin</a>.</p>

% else:


<h1>${ctxt.title}</h1>

    
<form action="${ctxt.root}/proposals/new/" method="post"  enctype="multipart/form-data">

<p></p>

<h2>Overview</h2>

<p>
    <span class="e2l-label">Project Title:</span>
    <input type=text  name=project_title  size="50">
</p>


<p>                           
    <span class="e2l-label">Proposed Dates of Experiments:</span>
    <input type=text name=date_of_experiments size="50">
</p>



<h2>Research Grant Support</h2>


<p>
    <span class="e2l-label">Name of Agency:</span>
    <input type=text name="grant_agency" size="50" value=''>
</p>

<p>
    <span class="e2l-label">Grant No:</span>
    <input type=text name="grant_no" size="50" value=''>
</p>

<p>
    <span class="e2l-label">Title of Grant:</span>
    <input type=text name="grant_title" size="50" value=''>
</p>


<p>
    <span class="e2l-label">Duration of Grant:</span>
    <input type=text name="grant_duration" size="50" value=''>
</p>

<p>               
    <span class="e2l-label">Annual Total Cost:</span>
    <input type=text name="grant_amount" size="50" value=''>
</p>

<p>
    <span class="e2l-label">Project Type (required):</span>
            
    <input type="radio" name="projectMode" value="collaborative">Collaborative 
    <input type="radio" name="projectMode" value="service">Service
</p>                    

<p>               
    <strong>Collaborative project</strong> will involve extensive resource staff participation and result in joint publications <br />
    <b>Service project</b> will require minimum resource staff assistance and need to acknowledge NIHP41RR02250 in all publications
</p>

<p>
    A short annual report due August 15 every year is required regardless of the nature of the project using NCMI facilities.
</p>       
        
        
        
<h3>Project Description</h3>

<p>
upload from local disk <input type="file" name="desfile" size="40">                    
</p>

<p>                    
<textarea cols=100 rows=30 name=project_description wrap=physical>In less than 1,000 words, describe the long and short-term research goals, biomedical significance, preliminary data, sample purity and quantity, and proposed experiments (include full literature citations).</textarea>
</p>
                        
                    
<p>
    <span class="e2l-label">Molecular Mass, kDa (required):</span>
    <input type="text" name="molecularmass" size="50" value="">
</p>
            
       
<p>
    <span class="e2l-label">Molecular Size (required):</span>
    <input type="text" name="molecularsize" size="50" value="">
</p>        


<h3>Other investigators</h3>
            
           
<table>
    
    <tr>
        <th colspan="4" />
        <th colspan="2">Experience</th>
    </tr>

    <tr>
        <th>Last Name</th>
        <th>First Name</th>
        <th>Email</th>
        <th>Degree</th>
        <th>CryoEM</th>
        <th>Image Processing</th>
        <th>Comments</th>
    </tr>
    
    % for i in range(5):
        <tr>

            <td><input type="text" name="lastname___${i}" /></td>

            <td><input type="text" name="firstname___${i}" /></td>

            <td><input type="text" name="email___${i}" /></td>

            <td>
                <select name="degree___${i}">
                    <option value="BS">BS</option>
                    <option value="BA">BA</option>
                    <option value="MA">MA</option>
                    <option value="MS">MS</option>                    
                    <option value="PHD">PhD</option>
                    <option value="MD">MD</option>
                    <option value="MDPHD">MD / PhD</option>
                    <option value="OTH">Other</option>            
                </select>
            </td>

            <td>
                <select name="cryoem___${i}">
                    <option value="0">No</option>
                    <option value="1">Yes</option>
                </select>        
            </td>

            <td>
                <select name="imageproc___${i}">
                    <option value="0">No</option>
                    <option value="1">Yes</option>
                </select>                        
            </td>

            <td><input type="text" name="comments___${i}" /></td>            
        </tr>
        
    % endfor
</table>


<h3>Supporting Documents</h3>

<p>
    4 page NIH format CV (<a href="http://grants1.nih.gov/grants/funding/phs398/phs398.html">see here</a>)
    <input type="file" name="cvFile" size="40">
</p>
          
<p>
    Reprints/Publications <br />
  <textarea cols=100 rows=10 name="reprints">Please enter PubMed IDs or describe documents, one per line</textarea>
</p>

                     
<input type=submit value=" Save ">
   
</form>


% endif
