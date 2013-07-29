<%! public = True %>
<%inherit file="/page" />

<%
people = [
  {'name':'Wah Chiu', 'photo':None, 'email':'wah@bcm.edu', 'title':'Director', 'current':True},
  {'name': 'Steven Ludtke', 'photo':None, 'email':'sludtke@bcm.edu', 'title':'Co-Director', 'current':True},
  {'name':'Matthew Baker', 'photo':None, 'email':'mlbaker@bcm.edu', 'title':'Instructor', 'current':True},
  {'name':'Ian Rees', 'photo':'http://eofdreams.com/data_images/dreams/cat/cat-06.jpg', 'email':'ian@ianrees.net', 'title':'Post-Doc', 'current':True},
  {'name':'Grant Tang', 'email':'gtang@bcm.bcm.edu', 'title':'Scientific Programmer', 'current':False}
]

current = [i for i in people if i.get('current')]
alumni = [i for i in people if not i.get('current')]

order = set([i.get('title') for i in current])
order.remove('Director')
order.remove('Co-Director')
order = ['Director', 'Co-Director'] + sorted(order)
%>


<%def name="draw_person(person)">
  <div class="ncmi-person">
  <h3>${person.get('name')}</h3>
  <p>
  email: ${person.get('email')}</br >
    % if person.get('photo'):
      <img src="${person.get('photo')}" /></br />
    % endif
  </p>
  </div>
</%def>



% for i in order:
  <h1>${i}</h1>
  % for person in filter(lambda x:x.get('title') == i, current):
    ${draw_person(person)}
  % endfor
% endfor


<h1>Alumni</h1>
% for person in alumni:
  ${draw_person(person)}
% endfor