#standard emen2 imports
from emen2.emen2config import *
import smtplib
from email.MIMEText import MIMEText
#from email.mime.text import MIMEText

import emen2.globalns
g = emen2.globalns.GlobalNamespace('')

def sendmailtemplate(recipient,template,ctxt=None):
	if ctxt==None: ctxt={}
	ctxt["recipient"]=recipient
	ctxt["MAILADMIN"]=g.MAILADMIN


	msg = g.templates.render_template(template, ctxt)
	sendmailraw(recipient,msg)




def sendmail(recipient,subject,msgtxt, db=None):

	msg=MIMEText(msgtxt)
	msg['Subject'] = subject
	msg['From'] = g.MAILADMIN
	msg['To'] = recipient

	#return
	# Send the message via our own SMTP server, but don't include the
	# envelope header.

	s = smtplib.SMTP(g.MAILHOST)
	s.set_debuglevel(1)
	s.sendmail(g.MAILADMIN, [recipient], msg.as_string())




def sendmailraw(recipient,content):
	#return
	s = smtplib.SMTP(g.MAILHOST)
	s.set_debuglevel(1)
	s.sendmail(g.MAILADMIN, [recipient], content)
	g.debug('mail sent %r' %content)



# Re-implement more of these features

# def sendmsg(mailfrom, mailto, subject, msg, debug=0):
#     '''All arguments are strings except debug. mailto can be several
#     addresses, separated by spaces or commas.'''
#     m = email.message_from_string(msg)
#     moff, hoff = math.modf(-time.timezone / 3600.0)
# #moff, hoff = math.modf(int(5.5*3600) / 3600.0)
#     hoff = int(hoff)
#     moff = int(moff * 60)
#     t = time.localtime()
#     hoff += (t[-1] != 0)
#
#     m['Date'] = time.strftime("%a, %d %b %Y %H:%M:%S ", t) + \
#                 "%+03d%02d" % (hoff, moff)
#     m['From'] = mailfrom
#     m['To'] = ', '.join(re.split('[ ,]+', mailto))
#     m['Subject'] = subject
# #    m.add_header('User-Agent', 'Python 2.4.1 (#2, Aug 29 2005, 20:13:14)')
#     m.add_header('User-Agent',
#                  'Python %s [%s %s]' % \
#                   (sys.version[ :sys.version.find('\n')].rstrip(), \
#                    sys.platform, sys.arch))
#     m.add_header('MIME-Version', '1.0')
#     m.add_header('Content-Type', 'text/plain', charset='us-ascii')
#     m.add_header('Content-Transfer-Encoding', '7bit')
#     if debug > 1:
#         print m.items(), '\n------------\n', m.as_string(1)
#     else:
#         server = smtplib.SMTP('smtp.bcm.tmc.edu')
#         server.set_debuglevel(debug)
#         ret = server.sendmail(mailfrom, re.split('[ ,]+', mailto),
#                               m.as_string(1))
#         server.quit()


