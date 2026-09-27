# Security Policy

At **MiSuperProfe**, the security, integrity, and confidentiality of our AI-powered educational platform, student data, and tutoring infrastructure are paramount. We appreciate the invaluable contributions of the global security research community in keeping our software and users safe.

This document outlines our security policies, supported versions, reporting procedures, and response commitments under our **Coordinated Vulnerability Disclosure (CVD)** process.

---

## Supported Versions

Security patches and vulnerability remediations are prioritized for active release branches. The table below details the current support lifecycle:

| Version | Status | Security Patch Support |
| :--- | :--- | :--- |
| `1.x` / `main` | **Active / Current** | ✅ Fully supported with active security patches |
| `< 1.0` | **Deprecated** | ❌ End of Life (Upgrade to latest release required) |

We strongly encourage all operators, developers, and deployment teams to track the latest release tags and apply security updates promptly.

---

## Reporting a Vulnerability

If you identify a security vulnerability or potential threat in MiSuperProfe, **please do not disclose it publicly** through GitHub issues, discussions, pull requests, or public chat channels. Public disclosure prematurely exposes active deployments to potential exploitation.

### Official Security Contact

Please report all security vulnerabilities via encrypted or secure email directly to:

📧 **[security@misuperprofe.com](mailto:security@misuperprofe.com)**

*(CC: [dev@misuperprofe.com](mailto:dev@misuperprofe.com))*

### What to Include in Your Report

To help us investigate, validate, and remediate the issue rapidly, please include as much detail as possible in your report:

1. **Vulnerability Summary:** A concise overview of the issue and its potential impact.
2. **Affected Components:** The impacted modules, API endpoints, microservices, or files (e.g., FastAPI routers, JWT authentication, DECO engine, database models).
3. **Severity Assessment:** Your estimated severity rating (e.g., CVSS score or Low / Medium / High / Critical).
4. **Step-by-Step Reproduction Instructions:** Clear, repeatable steps, scripts, or cURL requests required to reproduce the behavior.
5. **Proof of Concept (PoC):** Non-destructive code or demonstration payloads verifying the vulnerability.
6. **Suggested Remediation (Optional):** Recommendations, patch proposals, or architectural safeguards if known.

---

## Vulnerability Handling & Response Process

We follow a rigorous, coordinated response lifecycle:

```
[Receipt & Acknowledgment] (Within 24-48 Hours)
           │
           ▼
  [Triage & CVSS Assessment] (Within 3 Business Days)
           │
           ▼
[Private Patch Development & Testing]
           │
           ▼
  [Release Deployment & Advisory] (Coordinated with Reporter)
```

1. **Initial Acknowledgment:** Within **24 to 48 hours**, our security team will acknowledge receipt of your report and assign a tracking identifier.
2. **Triage & Validation:** Within **3 business days**, we will evaluate the vulnerability, reproduce the issue in an isolated environment, and assign a preliminary CVSS score.
3. **Remediation & Patching:** Our engineering team will develop and test a security patch within a private advisory fork.
4. **Coordinated Disclosure:** We will coordinate with the reporter on a release date. Once the patch is merged and deployed across active releases, a public security advisory will be published, crediting the reporter (unless anonymity is requested).

---

## Safe Harbor Policy

We consider security research conducted under this policy to be authorized. We commit not to pursue legal action against researchers who:

- Make a good-faith effort to avoid privacy violations, data destruction, degradation of user experience, and interruption of production services.
- Only interact with test accounts or systems under their direct control, and refrain from accessing, modifying, or retaining customer or student data.
- Promptly report any discovered vulnerability to [security@misuperprofe.com](mailto:security@misuperprofe.com) and keep all details confidential until a fix has been released.
- Do not exploit a vulnerability beyond what is strictly necessary to establish a proof of concept.
- Refrain from conducting volumetric Denial of Service (DoS/DDoS) attacks, social engineering, spamming, or physical security attacks against MiSuperProfe personnel or infrastructure.

---

## Security Best Practices for Contributors & Operators

### 1. Secrets Management
- **Never commit `.env` files, production credentials, private keys, or API tokens to version control.**
- Use `.env.example` strictly as a template with placeholder values.
- Rotate credentials immediately if exposure is suspected.

### 2. Authentication & Authorization
- Use strong, cryptographically secure keys (at least 256 bits) for `JWT_SECRET_KEY` and `JWT_OAUTH_SECRET_KEY`.
- Enforce strict token expiration lifetimes (`ACCESS_TOKEN_EXPIRE_MINUTES`).
- Validate user scopes and roles on every protected endpoint using FastAPI dependency injection.

### 3. Container & Ingress Hardening
- Deploy reverse proxies (such as Caddy or Nginx) to enforce TLS 1.3 encryption and automatic certificate renewal.
- Restrict Docker container exposed ports to internal networks wherever possible.
- Run containers with non-root privileges and read-only filesystems when applicable.

### 4. Database Security
- Store database credentials securely outside source trees.
- Validate that all database connections enforce encrypted transit (SSL mode `require` or `verify-full`).
- Parameterize all SQL queries using SQLAlchemy 2.0 ORM to prevent SQL injection vulnerabilities.

---

*Thank you for helping us keep MiSuperProfe secure, resilient, and trustworthy for students and educators worldwide.*
