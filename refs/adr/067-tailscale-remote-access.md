# ADR-067: Secure Remote Access with Tailscale

- **Status**: Accepted
- **Date**: 2025-08-16

## Context

The personal agent, including its web interfaces (Streamlit) and underlying services (LightRAG, Ollama), has historically been accessible only on the local network. This limits development, testing, and usage to being physically on the same network as the server, which is often a Mac Mini. There is a need to access these services remotely and securely from different devices (e.g., a development laptop, a phone) without exposing the services to the public internet.

## Decision

We have decided to implement **Tailscale** as the solution for creating a secure, private network (a "tailnet") that connects all authorized devices. This approach provides secure remote access to the agent's services without the complexity and security risks of public port forwarding, traditional VPNs, or firewall configuration.

### Implementation Details:

1.  **Installation**: Tailscale was installed on the primary server (Mac Mini, hostname: `tesla`), the development machine (MacBook, hostname: `kepler`), and a mobile device (iPhone).
2.  **Service Activation**: The Tailscale daemon (`tailscaled`) is configured to run as a service at boot on the server, ensuring the connection is always available.
3.  **SSH Access**: Tailscale's built-in SSH functionality (`tailscale up --ssh`) was enabled, allowing direct, secure shell access to the server using its tailnet hostname.
4.  **MagicDNS**: Tailscale's MagicDNS provides human-readable hostnames (e.g., `100.115.62.30`) for all devices in the tailnet, simplifying access to web services.
5.  **DNS Workaround**: Due to limitations in the free plan, a manual DNS override was configured on client devices (macOS, iPhone) to point to Tailscale's DNS server (`100.100.100.100`), enabling resolution of MagicDNS hostnames.
6.  **Security Hardening**: Standard SSH security practices were enforced on the server, including disabling password-based authentication in favor of public key authentication.

## Consequences

### Positive:
- **Secure Remote Access**: All services on the server are now accessible from any device in the tailnet, from any location, as if they were on the same local network.
- **Enhanced Security**: Services are not exposed to the public internet, drastically reducing the attack surface. All traffic is end-to-end encrypted.
- **Simplified Workflow**: Developers can now seamlessly access the Streamlit UI, SSH into the server, and interact with other services remotely, improving productivity.
- **No Firewall Configuration**: Avoids complex and error-prone firewall rules and port forwarding.

### Negative:
- **Dependency**: The project now depends on the Tailscale service being active on all relevant machines.
- **Manual DNS for Free Tier**: The free version of Tailscale requires a one-time manual DNS configuration on client devices to use MagicDNS hostnames. This is a minor inconvenience but a known limitation.
- **Centralized Control**: While the network is peer-to-peer, the authentication and coordination are managed by Tailscale's servers.
