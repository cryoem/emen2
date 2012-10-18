From: ${from_addr}
To: ${to_addr}
Cc: ${from_addr}
Subject: ${TITLE} Verify Email

${to_addr}:

You have recently added this email address, ${to_addr}, to your ${TITLE} account. Please follow the link below to verify this email account:

${uri}/auth/email/verify/${to_addr}/${secret}/

Please keep your current email address up to date, as it is required to reset your password or recover account details.

If you did not issue this request, please contact the ${TITLE} administrator.

Thankyou,

${TITLE} Administrator
${from_addr}
${uri}