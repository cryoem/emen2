import smtplib
import email.MIMEText

import emen2.db.config
g = emen2.db.config.g()


def sendmailtemplate(recipient,template,ctxt=None):
	if ctxt==None: ctxt={}
	ctxt["recipient"] = recipient
	ctxt["MAILADMIN"] = g.MAILADMIN

	msg = g.templates.render_template(template, ctxt)
	sendmailraw(recipient,msg)



def sendmail(recipient,subject,msgtxt, db=None):

	msg=email.MIMEText.MIMEText(msgtxt)
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
	if g.MAILHOST:
		try:
			s = smtplib.SMTP(g.MAILHOST)
			s.set_debuglevel(1)
			s.sendmail(g.MAILADMIN, [recipient], content)
			g.log('mail sent %r' %content)
		except Exception, e:
			g.log('LOG_ERROR','Email sending error: %s'%e)
	else:
		g.log('LOG_INFO','Email subsysstem not configured')

