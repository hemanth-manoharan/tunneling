# Tunneling client/server for self-hosting

This project includes a basic version of a tunneling client and server written using WebSockets that enables one to self-host a simple web application like a blog from a Raspberry Pi via a tunneling host in a public cloud.

It uses Caddy as the reverse-proxy in the tunneling host which enables one to expose the web application via https.

Major features to be added
- Add unit tests.
- Validate with real RPi test setup.
- Add support for secure WebSockets for a secure tunnel across tunneling client and server.
