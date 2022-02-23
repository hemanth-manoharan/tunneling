# How to create a system service for tunnel-client

Change directory to `/lib/systemd/system`

Create `tunnel-client.service` file with the content from git with root creds.

Then run the following commands

`sudo systemctl daemon-reload`

`sudo systemctl enable tunnel-client`

`sudo systemctl start tunnel-client`

`sudo systemctl status tunnel-client`

