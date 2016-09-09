import twisted.python.log
import twisted.application

import emen2.db.log
import emen2.db.config
import emen2.web.server

Options = emen2.web.server.WebServerOptions


def logger():
    emen2.db.log.logger.start()
    return emen2.db.log.logger.emit

def makeService(options):
    # Load the configuration
    import emen2.db.config
    emen2.db.config.UsageParser(options=options)

    # Start the service
    s = twisted.application.service.MultiService()
    server = emen2.web.server.EMEN2WebServer(options)
    server.start(service=s)    
    return s
    
def run_twistd():
    # This is a (somewhat awful hack) based on twistd.

    # Twistd plugins have great difficulty being packaged
    # by distutils, pip, etc., and there is no
    # current workaround. 
    
    # This function basically recreates twistd,
    # and inserts the EMEN2 Service as the only plugin.
    # This gets around having to have twisted/plugins/emen2_plugin.py
    # in a directory without an __init__.py

    # Run:
    # python -m emen2.tap [twistd options] emen2 [emen2 options]

    from twisted.application.service import ServiceMaker
    from twisted.application import app
    from twisted.python.runtime import platformType
    from twisted import plugin

    #### From twisted/plugins/emen2_plugin.py #####
    EMEN2Server = ServiceMaker(
        "EMEN2",
        "emen2.tap",
        ("EMEN2 server"),
        "emen2")

    #### Copied from twisted/scripts/twistd.py #####
    if platformType == "win32":
        from twisted.scripts._twistw import ServerOptions, \
            WindowsApplicationRunner as _SomeApplicationRunner
    else:
        from twisted.scripts._twistd_unix import ServerOptions, \
            UnixApplicationRunner as _SomeApplicationRunner

    #Create an altered ServerOptions that only runs EMEN2.
    class TestOptions(ServerOptions):
        def _getPlugins(self, interface, package=None):
            f = plugin.getPlugins(interface, package=None)
            return list(f) + [EMEN2Server]

    def runApp(config):
        _SomeApplicationRunner(config).run()
    
    app.run(runApp, TestOptions)
    
    

if __name__ == "__main__":
    run_twistd()
    
