# Tunneling client/server for self-hosting

This project includes a basic version of a tunneling client and server written using WebSockets that enables one to self-host a simple web application like a blog from a Raspberry Pi via a tunneling host in a public cloud.

It uses Caddy as the reverse-proxy in the tunneling host which enables one to expose the web application via https.

## Folder structure

project_root/<br/>
|<br/>
|-- caddy-config/  # Configs for the Caddy reverse-proxy<br/>
|-- tunnel-server/  # Code-base for the tunneling server (to be hosted in the cloud behind Caddy)<br/>
|-- tunnel-client/  # Code-base for the tunneling client (to be hosted on the other end, close to the final service being exposed)<br/>
|-- sample-app/  # Sample web site to test the tunneling setup<br/>
|-- sample-web-svc/  # Sample web service to test the tunneling setup<br/>
