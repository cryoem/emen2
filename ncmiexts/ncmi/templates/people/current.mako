<%! public = True %>
<%inherit file="/page" />

<%
people = [
{'name':'Wah Chiu', 'photo':'http://ncmi.bcm.edu/ncmi/images/wah_jpg', 'email':'wah@bcm.edu', 'title':'Director', 'current':True},
{'name':'Michael Schmid', 'photo':'http://ncmi.bcm.edu/ncmi/images/mikes_jpg', 'email':'gtang@bcm.bcm.edu', 'title':'Co-Director', 'current':True},
{'name':'Steven Ludtke', 'photo':'http://ncmi.bcm.edu/ncmi/images/steve_jpg', 'email':'sludtke@bcm.edu', 'title':'Co-Director', 'current':True},
{'name':'Irina Serysheva', 'photo':'http://ncmi.bcm.edu/ncmi/images/irina_jpg', 'email':'irinas@bcm.bcm.edu', 'title':'Associate Professor', 'current':True},
{'name':'Matthew Baker', 'photo':'http://ncmi.bcm.edu/ncmi/people/people/people_33/photo', 'email':'mlbaker@bcm.edu', 'title':'Instructor', 'current':True},
{'name':'Grant Tang', 'photo':'http://ncmi.bcm.edu/ncmi/images/irina_jpg', 'email':'gtang@bcm.bcm.edu', 'title':'Scientific Programmer', 'current':False},
{'name':'Philip Baldwin', 'photo':'http://ncmi.bcm.edu/ncmi/people/people/people_94/photo', 'email':'pbaldwin@bcm.bcm.edu', 'title':'Scientific Programmer', 'current':True},
{'name':'Donghua Chen', 'photo':'http://ncmi.bcm.edu/ncmi/people/people/people_24/photo', 'email':'dchen@bcm.bcm.edu', 'title':'Scientific Programmer', 'current':True},  
{'name':'Bo Chen', 'photo':'http://ncmi.bcm.edu/ncmi/people/people/people_101/photo', 'email':'bchen@bcm.bcm.edu', 'title':'Graduate Student', 'current':True},
{'name':'Wei Dai',  'photo':'http://ncmi.bcm.edu/ncmi/people/people/people_104/photo','email':'wei.dai@bcm.bcm.edu', 'title':'Postdoctoral Associate', 'current':True}, 
{'name':'Matt Dougherty',  'photo':'http://ncmi.bcm.edu/ncmi/people/people/people_21/photo', 'email':'matthewd@bcm.bcm.edu', 'title':'Sr Scientific Programmer', 'current':True},  
{'name':'Caroline Fu',  'photo':'http://ncmi.bcm.edu/ncmi/people/people/people_93/photo','email':'cjfu@bcm.bcm.edu', 'title':'Research Technician III', 'current':True},
{'name':'Jesus Galaz-Montoya',  'photo':'http://ncmi.bcm.edu/ncmi/people/people/people_109/photo', 'email':'jgmontoy@bcm.bcm.edu', 'title':'Graduate Student', 'current':True},  
{'name':'Preeti Gipson',  'photo':'http://ncmi.bcm.edu/ncmi/people/people/people_122/photo', 'email':'pgipson@bcm.bcm.edu', 'title':'Postdoc Fellow', 'current':True},  
{'name':'Corey Hecksel',  'photo':'http://ncmi.bcm.edu/ncmi/people/people/people_117/photo', 'email':'hecksel@bcm.bcm.edu', 'title':'Graduate Student', 'current':True},  
{'name':'Chuan Hong',  'photo':'http://ncmi.bcm.edu/ncmi/people/people/people_105/photo', 'email':'ch2@bcm.bcm.edu', 'title':'Graduate Student', 'current':True},  
{'name':'Corey Hryc',  'photo':'http://ncmi.bcm.edu/ncmi/people/people/people_115/photo', 'email':'hryc@bcm.bcm.edu', 'title':'Research Technician I', 'current':True},  
{'name':'Rossitza (Rossi) Irobalieva', 'photo':'http://ncmi.bcm.edu/ncmi/people/people/people_113/photo', 'email':'irobalie@bcm.bcm.edu', 'title':'Graduate Student', 'current':True},  
{'name':'Joanita Jakana',  'photo':'http://ncmi.bcm.edu/ncmi/people/people/people_17/photo', 'email':'jjakana@bcm.edu', 'title':'Dir, Laboratory, Asst', 'current':True},  
{'name':'Alexey Koyfman',  'photo':'http://ncmi.bcm.edu/ncmi/people/people/people_98/photo', 'email':'koyfman@bcm.bcm.edu', 'title':'Postdoctoral Fellow', 'current':True},  
{'name':'Edward Langley',  'photo':'http://ncmi.bcm.edu/ncmi/people/people/people_118/photo', 'email':'langley@bcm.bcm.edu', 'title':'Microcomputer Technician', 'current':True},  
{'name':'Wilson Lau',  'photo':'http://ncmi.bcm.edu/ncmi/people/people/people_125/photo', 'email':'wlau@bcm.edu', 'title':'Postdoctoral Associate', 'current':True},  
{'name':'Xiangan Liu',  'photo':'http://ncmi.bcm.edu/ncmi/people/people/people_53/photo', 'email':'xianganl@bcm.bcm.edu', 'title':'Instructor', 'current':True},  
{'name':'Stephen Murray',  'photo':'http://ncmi.bcm.edu/ncmi/people/people/people_120/photo', 'email':'scmurray@bcm.bcm.edu', 'title':'Graduate Student', 'current':True},  
{'name':'Grigore Dimitrie (Greg) Pintilie',  'photo':'http://ncmi.bcm.edu/ncmi/people/people/people_107/photo', 'email':'pintilie@bcm.bcm.edu', 'title':'Scientific Programmer I', 'current':True},  
{'name':'Ian Rees', 'photo':'http://eofdreams.com/data_images/dreams/cat/cat-06.jpg', 'email':'ian@ianrees.net', 'title':'Post-Doc', 'current':True},
{'name':'Ryan Rochat',  'photo':'http://ncmi.bcm.edu/ncmi/people/people/people_102/photo', 'email':'rochat@bcm.bcm.edu', 'title':'Medical Student', 'current':True},  
{'name':'Soung-Hun Roh',  'photo':'http://ncmi.bcm.edu/ncmi/people/people/people_124/photo', 'email':'sroh@bcm.bcm.edu', 'title':'Graduate Student', 'current':True},
{'name':'Sarah Shahmoradian', 'photo':'http://ncmi.bcm.edu/ncmi/people/people/people_96/photo', 'email':'shahmora@bcm.bcm.edu', 'title':'Graduate Student', 'current':True},  
{'name':'Rui Wang',  'photo':'http://ncmi.bcm.edu/ncmi/people/people/people_99/photo', 'email':'ruiw@bcm.edu', 'title':'Graduate Student', 'current':True},  
{'name':'Zhao Wang',  'photo':'http://ncmi.bcm.edu/ncmi/people/people/people_106/photo', 'email':'zhaow@bcm.edu', 'title':'Postdoctoral Fellow', 'current':True},
{'name':'Agustin Avila-Sakar',  'photo':'', 'email':'', 'title':'', 'current':False},
{'name':'Chris Booth',  'photo':'', 'email':'christopher.booth@gmail.com', 'title':'', 'current':False},
{'name':'Jaap Brink',  'photo':'', 'email':'jbrink@jeol.com', 'title':'', 'current':False},
{'name':'Richard Byrd',  'photo':'', 'email':'', 'title':'', 'current':False},
{'name':'Yao Cong',  'photo':'', 'email':'cong@sibcb.ac.cn', 'title':'', 'current':False},
{'name':'Angela Cruciano',  'photo':'', 'email':'', 'title':'', 'current':False},
{'name':'Hari Damodaran',  'photo':'', 'email':'', 'title':'', 'current':False},
{'name':'John DeGoes',  'photo':'', 'email':'', 'title':'', 'current':False},
{'name':'Glenn Decker',  'photo':'', 'email':'', 'title':'', 'current':False},
{'name':'An Dinh',  'photo':'', 'email':'', 'title':'', 'current':False},
{'name':'John Francis Flanagan IV',  'photo':'', 'email':'jfflanag@gmail.com', 'title':'', 'current':False},
{'name':'Mikyung Han',  'photo':'', 'email':'hanmikyung@gmail.com', 'title':'', 'current':False},
{'name':'Ian Hogue',  'photo':'', 'email':'', 'title':'', 'current':False},
{'name':'Wen Jiang',  'photo':'', 'email':'jiang12@purdue.edu', 'title':'', 'current':False},
{'name':'Jennifer Jordan',  'photo':'', 'email':'jenniferjordan@hotmail.com', 'title':'', 'current':False},
{'name':'Kelsey Mavis',  'photo':'', 'email':'', 'title':'', 'current':False},
{'name':'Jeff Lawton',  'photo':'', 'email':'', 'title':'', 'current':False},
{'name':'Zongli Li',  'photo':'', 'email':'zongli_li@hms.harvard.edu', 'title':'', 'current':False},
{'name':'Mike Marsh',  'photo':'', 'email':'mike.marsh@vsg3d.com', 'title':'', 'current':False},
{'name':'Amy McGough',  'photo':'', 'email':'', 'title':'', 'current':False},
{'name':'Frederic Metoz',  'photo':'', 'email':'', 'title':'', 'current':False},
{'name':'Sharmila Mukherjee',  'photo':'', 'email':'', 'title':'', 'current':False},
{'name':'Laurie Nason',  'photo':'', 'email':'laurie.nason@maf-europe.org', 'title':'', 'current':False},
{'name':'Elena Orlova',  'photo':'', 'email':'', 'title':'', 'current':False},
{'name':'Angel Paredes',  'photo':'', 'email':'Angel.Paredes@uth.tmc.edu', 'title':'', 'current':False},
{'name':'Liwei Peng',  'photo':'', 'email':'liwei.peng@gmail.com', 'title':'', 'current':False},
{'name':'Gary Ren',  'photo':'', 'email':'gren@lbl.gov', 'title':'', 'current':False},
{'name':'Jonathan Respress',  'photo':'', 'email':'respress@bcm.edu', 'title':'', 'current':False},
{'name':'Ali Saad',  'photo':'', 'email':'asaad64@yahoo.com', 'title':'', 'current':False},
{'name':'Michael Sherman',  'photo':'', 'email':'mbsherma@UTMB.edu', 'title':'', 'current':False},
{'name':'Naomi Silver',  'photo':'', 'email':'', 'title':'', 'current':False},
{'name':'Lia Stanciu',  'photo':'', 'email':'', 'title':'', 'current':False},
{'name':'Pam Thurman-Commike',  'photo':'', 'email':'', 'title':'', 'current':False},
{'name':'Haili Tu',  'photo':'', 'email':'haili_tu@hotmail.com', 'title':'', 'current':False},
{'name':'Yi Wang',  'photo':'', 'email':'', 'title':'', 'current':False},
{'name':'Zhixian Zhang',  'photo':'', 'email':'', 'title':'', 'current':False},
{'name':'Wei Zhang',  'photo':'', 'email':'wzhang2@bcm.edu', 'title':'', 'current':False},
{'name':'Qinfen Zhang',  'photo':'', 'email':'qinfenz@gmail.com', 'title':'', 'current':False},
{'name':'Dongming Zhang',  'photo':'', 'email':'', 'title':'', 'current':False},
]

current = [i for i in people if i.get('current')]
alumni = [i for i in people if not i.get('current')]

order = set([i.get('title') for i in current])
order.remove('Director')
order.remove('Co-Director')
order = ['Director', 'Co-Director'] + sorted(order)
%>


<%def name="draw_person(person)">
  <div class="ncmi-person e2l-cf">
  <h3>${person.get('name')}</h3>
  <p>
    % if person.get('photo'):
          <img src="${person.get('photo')}" /></br />
    % endif

	  <strong>${person.get('title')}</strong> <br />
	  email: ${person.get('email')}<br />

  </p>
  </div>
</%def>



% for i in order:
  % for person in filter(lambda x:x.get('title') == i, current):
    ${draw_person(person)}
  % endfor
% endfor


## <h1>Alumni</h1>
## % for person in alumni:
##  ${draw_person(person)}
## % endfor




