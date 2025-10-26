# ssh-mimik

SSH honeypot utilizing ephemeral Docker containers.

# Usage

## Installation 

Ensure that Docker is installed & the service is enabled & running on the machine you're running this on, otherwise the Docker containers won't be able to be spun up. See the [docker installation instruction page](https://docs.docker.com/engine/install/)

`git clone https://github.com/1d8/ssh-mimik`

`pip3 install -r requirements.txt`

Now we must generate the SSH keys that our mock SSH server will use:

`ssh-keygen -t rsa -b 2048 -f ssh_host_key_rsa`

`python3 serve.py --help` to display available options (This is subject to change when new features are introduced)

`sudo python3 serve.py -p 22 -l /splunk/log/folder` to serve the SSH server on port 22 & place log file within specified directory

* You can place the log file anywhere, the file format is JSON
* If you choose to run on a different port, you still need to run as `sudo`. Otherwise the docker containers will not be able to spawn & each time you try SSHing in, you will get the following error: `shell request failed on channel 0`

Once the server is up & running the default creds are: `user:password`

## DockerFile Breadcrumb Example Usage

### Usage

Since Docker containers are deployed once a successful SSH connection is made, you can use custom DockerFiles to help deploy additional breadcrumbs when an attacker connects.

For example, say you wanted to lead the adversary down a path of deception. You could have the following DockerFile:

```
FROM ubuntu:20.04

WORKDIR /opt/scripts

COPY ssh_login.sh /opt/scripts/logmein.sh

RUN chmod +x /opt/scripts/logmein.sh
```

Then on our local system, the content of our `ssh_login.sh` would be:

```
ssh -i "IDENTITY.pem" 192.168.2.1
```

This will create a Docker container and copy a Bash SSH login script to the container's `/opt/scripts/` directory. Ideally, you'd also transfer the `IDENTITY.pem` file & standup a server with an IP of `192.168.2.1` to lead an attacker down a further path of deception and confusion.

Then you'd run the honeypot:

`sudo python3 serve.py -p 22 -l . -d examples/DockerFile`

### Errors

If you pass a DockerFile that doesn't exist, the program will exit with an error indicating so.

~~If you pass a DockerFile that doesn't exist, the program won't currently exit & will continue running but will log a message saying: `[!] Fatal error! DockerFile was passed but doesn't exist: <DockerFile Name>!`. But on the client-side, you'll get an error saying `shell request failed on channel 0` after attempting to authenticate.~~

## Common Issues

Script immediately exiting without starting server:

![](https://i.ibb.co/qLTCPHjv/2025-05-26-08-59.png)

**Fix: Ensure you've generated your SSH keys & they're placed in the same directory you're running the script from.**

## Todo

- [x] Update readme to include usage information
- [ ] Clean up `serve.py` code
- [ ] Update `serve.py` code to auto generate the necessary SSH keys
- Add CLI args for: 
	- [x] Specifying the port SSH will run on
	- [x] Specify the location log files will be saved to
- [x] Add example usage of utilizing DockerFiles to deploy more realistic honeypots (EX: Deploying additional directories & files)
- [ ] Add automated python script that'll auto attack SSH honeypots on specified subnet to simulate attacker. CTF-style questions will then be asked based on these commands ran.
- [ ] Possible web interface for viewing active SSH sessions & logs?
- [x] Implement check to ensure running with root privileges, otherwise exit to avoid causing errors
- [x] Implement DockerFile capability for deploying breadcrumbs
	- [x] Implement better error handling with DockerFile implementation
	- [x] Document this feature better 

