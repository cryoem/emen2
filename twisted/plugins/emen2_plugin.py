from twisted.application.service import ServiceMaker

# Provide a twistd service.
EMEN2Server = ServiceMaker(
    "EMEN2",
    "emen2.tap",
    ("EMEN2 server"),
    "emen2")

