# How to create a system service for tunnel-server

Change directory to `/lib/systemd/system`

Create `tunnel-server.service` file with the content from git with root creds.

Then run the following commands

`sudo systemctl daemon-reload`

`sudo systemctl enable tunnel-server`

`sudo systemctl start tunnel-server`

`sudo systemctl status tunnel-server`

