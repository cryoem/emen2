From: ${from_addr}
To: ${to_addr}
Cc: ${from_addr}
Subject: ${TITLE} confirm email address

${to_addr}:

You have requested to the email address on your ${TITLE} account from ${oldemail} to ${email}.

Please follow the link below to confirm the request:

${uri}/auth/email/verify/${name | u}/${email | u}/${secret | u}/

Please keep your current email address up to date, as it is required to reset your password or recover account details.

If you did not issue this request, please contact the ${TITLE} administrator.

Thankyou,

${TITLE} Administrator
${from_addr}
${uri}