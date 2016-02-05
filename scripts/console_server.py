from twisted.internet.protocol import Protocol, Factory
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor
from twisted.protocols import basic
import subprocess
import os, time

class ObstinateProtocol(basic.LineReceiver):

    zeroized = True
    bootStrapped = False
    passwordSetInit = False
    passwordSetInit2 = False
    passwordSet = False

    def connectionMade(self):
        print("CONNTECTED")

    def isLoginScreen(self, data):
        if "Amnesiac" in data:
            return True

    def isCommandLineReady(self, data):
        if "root>" in data or "root#" in data:
            return True
        return False

    def lineReceived(self, data):
        print data
        # if self.bootStrapped is True and "root>" in data:
        #     os._exit(0)


        # Initial login and zeroizing
        if self.isLoginScreen(data) and self.zeroized is False:
            self.sendLine('root') #Send Username
            self.sendLine('cli')
            self.sendLine('request system zeroize\ryes')
            self.zeroized = True
            return


        # Secondary login, so push bootstrap configuration (root password, management IP address, static default route)
        if self.isLoginScreen(data) and self.zeroized is True:
            self.sendLine('root') #Send Username
            self.sendLine('cli')
            self.sendLine('edit')
            self.sendLine('set system services netconf ssh')
            self.sendLine('set system root-authentication plain-text-password')
            self.passwordSetInit = True

            return

        if self.passwordSetInit is True:
            time.sleep(1)
            self.sendLine('juniper123')



            self.passwordSetInit = False
            self.passwordSetInit2 = True
            return

        if self.passwordSetInit2 is True:
            time.sleep(1)
            self.sendLine('juniper123')
            self.passwordSet = True
            self.passwordSetInit2 = False
            return

        if self.passwordSet is True:
            time.sleep(0.2)
            self.sendLine('\r')
            self.sendLine('commit and-quit')
            self.passwordSet = False
            self.bootStrapped = True
            self.passwordSetInit2 = False
            return



factory = Factory()
factory.protocol = ObstinateProtocol
endpoint = TCP4ServerEndpoint(reactor, 13370)
endpoint.listen(factory)
reactor.run()

#
# from twisted.internet import reactor, protocol
# import os
# import time
#
# class ConsoleServer(protocol.Protocol):
#
#     zeroized = False
#     bootStrapped = False
#     def dataReceived(self, data):
#         print data
#
#         if self.bootStrapped is True:
#             os._exit(0)
#
#         # Initial login and zeroizing
#         if "login:" in data and self.zeroized is False:
#             self.sendLine('root\r\n') #Send Username
#             self.sendLine('\r\n') #Send Password
#             self.sendLine('cli\r\n')
#             self.sendLine('request system zeroize\r\nyes\r\n')
#             self.zeroized = True
#             print "yes"
#             return
#
#         # Secondary login, so push bootstrap configuration (root password, management IP address, static default route)
#         if "login:" in data and self.zeroized is True:
#             print "second"
#             self.sendLine('root\r\n') #Send Username
#             self.sendLine('\r\n') #Send Password
#             self.sendLine('cli\r\n')
#             self.sendLine('edit\r\n')
#             self.sendLine('set system root-authentication plain-text-password\r\n')
#             self.sendLine('$NEWPASSWORDHERE\r\n')
#             self.sendLine('$NEWPASSWORDHERE\r\n')
#             self.sendLine('set system services netconf ssh\r\n')
#             self.sendLine('set interfaces ge-0/0/0 unit 0 family inet address $IPADDRESSHERE\r\n')
#             self.sendLine('set routing-options static route 0.0.0.0/0 next-hop 10.180.20.254\r\n')
#             self.sendLine('commit and-quit\r\n')
#             self.sendLine('exit')
#             self.bootStrapped = True
#
#             return
#
# class ConsoleServerFactory(protocol.Factory):
#     protocol = ConsoleServer
#
# factory = ConsoleServerFactory()
# reactor.listenTCP(1337, factory)
# reactor.run()
#


