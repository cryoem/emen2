From: ${from_addr}
To: ${to_addr}
Cc: ${from_addr}
Subject: ${TITLE} password reset

${to_addr}:

A request for a password reset has been submitted for this account on ${TITLE}.

To complete your request, please follow this link:

${uri}/auth/password/reset/${name | u}/${secret | u}/

If you did not request a new password, please contact the ${TITLE} administrator, ${from_addr}

Thankyou,

${TITLE} Administrator
${from_addr}
${uri}