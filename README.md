# ssh-mimik

SSH honeypot utilizing ephemeral Docker containers.

# Usage

`git clone https://github.com/1d8/ssh-mimik`

`pip3 install -r requirements.txt`

Now we must generate the SSH keys that our mock SSH server will use:

`ssh-keygen -t rsa -b 2048 -f ssh_host_key_rsa`

`python3 serve.py --help` to display available options (This is subject to change when new features are introduced)

`sudo python3 serve.py -p 22 -l /splunk/log/folder` to serve the SSH server on port 22 & place log file within specified directory

* If you choose to run on a different port, you still need to run as `sudo`. Otherwise the docker containers will not be able to spawn & each time you try SSHing in, you will get the following error: `shell request failed on channel 0`


Once the server is up & running the default creds are: `user:password`

## Todo

- [x] Update readme to include usage information
- [ ] Clean up `serve.py` code
- [ ] Update `serve.py` code to auto generate the necessary SSH keys
- Add CLI args for: 
	- [x] Specifying the port SSH will run on
	- [x] Specify the location log files will be saved to
- [ ] Add example usage of utilizing Dockerfiles to deploy more realistic honeypots (EX: Deploying additional directories & files)
- [ ] Add automated python script that'll auto attack SSH honeypots on specified subnet to simulate attacker. CTF-style questions will then be asked based on these commands ran.
- [ ] Possible web interface for viewing active SSH sessions & logs?
- [ ] Implement check to ensure running with root privileges, otherwise exit to avoid causing errors
- [x] Implement dockerfile capability for deploying breadcrumbs

## DockerFile Breadcrumb Example Usage



## Common Issues

Script immediately exiting without starting server:

![](https://i.ibb.co/qLTCPHjv/2025-05-26-08-59.png)

**Fix: Ensure you've generated your SSH keys & they're placed in the same directory you're running the script from.**
