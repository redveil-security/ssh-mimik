#!/usr/bin/env python3

import sys
from zope.interface import implementer
from twisted.conch import avatar
from twisted.conch.checkers import InMemorySSHKeyDB, SSHPublicKeyChecker
from twisted.conch.ssh import connection, factory, keys, session, userauth
from twisted.conch.ssh.transport import SSHServerTransport
from twisted.cred import portal
from twisted.cred.checkers import InMemoryUsernamePasswordDatabaseDontUse
from twisted.internet import protocol, reactor
from twisted.python import components, log


# May break
from twisted.cred import checkers, credentials


import docker
import random
import string
import json
import logging
import argparse
from datetime import datetime
import os

#log.startLogging(sys.stderr)



# Path to RSA SSH keys used by the server.
SERVER_RSA_PRIVATE = "ssh_host_key_rsa"
SERVER_RSA_PUBLIC = "ssh_host_key_rsa.pub"

# Path to RSA SSH keys accepted by the server for authentication.
#CLIENT_RSA_PUBLIC = "ssh-keys/client_rsa.pub"

class JSONLogObserver:
    def __init__(self, logfile):
        self.logfile = logfile

    def __call__(self, eventDict):
        if eventDict.get("isError"):
            text = log.formatFailure(eventDict)
        else:
            text = eventDict.get("message")
            if isinstance(text, (list, tuple)):
                text = " ".join(str(m) for m in text)

        log_entry = {
                #"timestamp": eventDict.get("time"),
                "timestamp": datetime.utcfromtimestamp(eventDict.get("time")).strftime("%Y-%m-%d %H:%M:%S"),
                "system": eventDict.get("system"),
                "level": "ERROR" if eventDict.get("isError") else "INFO",
                "message": text
        }

        self.logfile.write(json.dumps(log_entry) + "\n")
        self.logfile.flush()





class ExampleAvatar(avatar.ConchUser):
    def __init__(self, username):
        avatar.ConchUser.__init__(self)
        self.username = username
        self.channelLookup.update({b"session": session.SSHSession})


@implementer(portal.IRealm)
class ExampleRealm:
    def requestAvatar(self, avatarId, mind, *interfaces):
        return interfaces[0], ExampleAvatar(avatarId), lambda: None
        

class EchoProtocol(protocol.Protocol):
    def connectionMade(self):
        self.commandBuffer = b""
        self.transport.write("OpenSSH Server")
        self.showPrompt()
        #self.buffer = b""
        print(f"[+] Deploying temporary container...")
        self.container, self.containerName = deployTmpContainer()



    def showPrompt(self):
        self.transport.write(b"$ ")

    def dataReceived(self, data):
        # Modify so entered command is logged, not just every keypress
        #self.transport.write(data)
        #self.commandBuffer += data
        
        # Handle ctrl + c     
        if data == b"\x03":
            self.transport.write(b"^C")
            self.commandBuffer = b""
            self.showPrompt()
            return

        # Handle ctrl+l
        if data == b"\x0c":
            self.transport.write(b"\x1b[2J\x1b[H")
            self.showPrompt()
            return


        # Handle backspace
        if data in [b"\x08", b"\x7f"]:
            if self.commandBuffer:
                self.commandBuffer = self.commandBuffer[:-1]
                self.transport.write(b"\b \b")
            return


        self.transport.write(data)
        self.commandBuffer += data

        if data in (b"\r", "\n"):
            #command = self.commandBuffer.strip().decode()
            command = self.commandBuffer.decode().strip()
            self.commandBuffer = b""

            if command.lower() == "exit":
                # Close container
                print(f"[+] Shutting {self.containerName} down...")
                client = docker.from_env()
                containerHandle = client.containers.get(self.containerName)
                containerHandle.stop()
                containerHandle.remove()

                self.transport.loseConnection()
                
            else:
                # Here is where we take a cmd & process it in a docker container
                #response = f"\r\nCommand: {command}\r\n"
                #print("[+] Deploying tmp container...")
                #container = deployTmpContainer()
                #print("[+] Container deployed!")
                log.msg(f"[+] Command ran: {command}")
                exitCode, out = self.container.exec_run(f"/bin/bash -c \"{command}\"", tty=True)
                shellResp = out.decode("utf-8")

                self.transport.write(f"\n{shellResp}")
                #self.transport.write(response.encode())
                


            self.showPrompt()


# Deploy container with random name
def deployTmpContainer():
    # Generate random docker container name
    alphabet = string.ascii_letters + string.digits
    containerName = ''.join(random.choice(alphabet) for _ in range(10))
    
    print(f"[+] Spawning container {containerName}")
    
    # Deploy container based on if dockerfile was passed
    if args.docker_file is not None:
        # Ensure file exists
        if os.path.isfile(args.docker_file):
            log.msg(f"[+] Building & deploying docker file: {args.docker_file}...")
            client = docker.from_env()

            image, logs = client.images.build(
                path=".",
                dockerfile=args.docker_file,
                tag=containerName.lower(), # fun fact: Docker image tags must be lowercase so this caused me major issues first time around 
            )
      
            container = client.containers.run(
                containerName.lower(),
                command="bash",
                tty=True,
                detach=True
            )
            return container, containerName
        else:
            log.msg(f"[!] Fatal error! Dockerfile was passed but doesn't exist: {args.docker_file}!")
            quit()
    else:
        client = docker.from_env()
        client.images.pull("ubuntu:latest")
        container = client.containers.run(
                "ubuntu:latest",
                command="bash",
                name=containerName,
                tty=True,
                detach=True,
                )
        print("[+] Tmp conainer started!")
        return container, containerName


@implementer(session.ISession, session.ISessionSetEnv)
class ExampleSession:
    def __init__(self, avatar):
        self.avatar = avatar

    def getPty(self, term, windowSize, attrs):
        log.msg("[+] PTY requested")

    def setEnv(self, name, value):
        log.msg(f"[+] ENV set: {name}={value}")

    def execCommand(self, proto, cmd):
        log.msg(f"[+] Executing {cmd}...")
        raise Exception("Command execution is disabled")

    def openShell(self, transport):
        log.msg("[+] Opening shell...")
        protocol = EchoProtocol()
        protocol.makeConnection(transport)
        transport.makeConnection(session.wrapProtocol(protocol))
        log.msg("[+] Shell session started")

    def eofReceived(self):
        log.msg("[+] EOF received")

    def closed(self):         
        log.msg("[+] Session closed")

components.registerAdapter(
    ExampleSession, ExampleAvatar, session.ISession, session.ISessionSetEnv
)

class ExampleFactory(factory.SSHFactory):
    protocol = SSHServerTransport
    services = {
        b"ssh-userauth": userauth.SSHUserAuthServer,
        b"ssh-connection": connection.SSHConnection,
    }

    def __init__(self):
        passwdDB = InMemoryUsernamePasswordDatabaseDontUse(user=b"password")
        #sshDB = SSHPublicKeyChecker(
         #   InMemorySSHKeyDB({b"user": [keys.Key.fromFile(CLIENT_RSA_PUBLIC)]})
        #)
        self.portal = portal.Portal(ExampleRealm(), [passwdDB])

    def getPublicKeys(self):
        return {b"ssh-rsa": keys.Key.fromFile(SERVER_RSA_PUBLIC)}

    def getPrivateKeys(self):
        return {b"ssh-rsa": keys.Key.fromFile(SERVER_RSA_PRIVATE)}

# Usage: sudo python3 serve.py -p 22 -l /splunk/log/folder
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", help="Port to run SSH server on", required=True, type=int)
    parser.add_argument("-l", "--log", help="Directory to store logs. Log file name will be appended on", required=True)
    parser.add_argument("-d", "--docker-file", help="Testing", required=False)
    args = parser.parse_args()

    print(f"[+] SSH server will run on port {args.port}")

    logfile = open(args.log + "/ssh.json", "a")
    observer = JSONLogObserver(logfile)
    log.startLoggingWithObserver(observer)


    reactor.listenTCP(args.port, ExampleFactory())
    reactor.run()
    

