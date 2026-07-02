# IT and Security Policy

**Acme Corp** | Effective January 1, 2026

## Overview

Acme Corp's IT systems exist to support business operations. All employees are responsible for protecting company data, systems, and the privacy of colleagues and customers. Violations of this policy may result in disciplinary action up to and including termination.

## Account Management

- Acme Corp provisions accounts via Google Workspace (email and docs), Slack (messaging), and Okta (SSO).
- Each employee has a unique account. **Account sharing is prohibited.**
- Employees must report lost or compromised credentials to helpdesk@acmecorp.internal immediately.
- Access is revoked within **4 hours of separation** from the company.

## Password and Authentication Requirements

- Passwords must be at least **14 characters**, mixing upper/lower case, numbers, and symbols.
- Do not reuse passwords across company and personal accounts.
- **Multi-Factor Authentication (MFA) is mandatory** for all company accounts. Hardware keys (YubiKey) are preferred; authenticator apps (e.g., Google Authenticator) are acceptable.
- Use the company-approved password manager (1Password Teams) for storing credentials.

## Device Policy

- Only **Acme-issued or IT-approved devices** may access internal systems or sensitive data.
- Full-disk encryption must be enabled (FileVault on macOS, BitLocker on Windows). IT configures this during setup.
- Operating systems and software must be kept up to date. IT enforces automatic updates via MDM.
- If a device is lost or stolen, report it to helpdesk within **2 hours**. IT can remotely wipe the device.

## Acceptable Use

Company systems may be used for **incidental personal use** as long as it does not:
- Violate any law or Acme policy.
- Consume excessive bandwidth or storage.
- Create a hostile or inappropriate environment.

The following are **never permitted** on company systems:
- Accessing or distributing illegal content.
- Installing unauthorized software or browser extensions.
- Disabling security controls (antivirus, MDM, VPN).
- Storing company data in unapproved personal cloud services (e.g., personal Google Drive, Dropbox).

## VPN and Network Access

- The Acme VPN (Tailscale) must be active when accessing internal systems or the corporate network from outside a trusted office location.
- Public Wi-Fi usage requires the VPN. A privacy screen is strongly recommended in public spaces.

## Data Classification

| Classification | Examples | Handling |
|---|---|---|
| Public | Blog posts, press releases | No restrictions |
| Internal | Policies, org charts, roadmaps | Share only with Acme employees |
| Confidential | Customer data, financial data, HR records | Encrypted in transit and at rest, need-to-know basis |
| Restricted | M&A info, security keys, PII | Need-to-know; access logged; never sent via email |

---
*Report security incidents to security@acmecorp.internal or Slack #security-incidents.*
