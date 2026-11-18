# DarGlobal & Wasalt Real Estate Advisory System

An institutional AI real estate intelligence platform combining verified public data from **DarGlobal** (London Stock Exchange: `DAR`) and **Wasalt** (Saudi Arabia's REGA-accredited PropTech marketplace).

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/GhaziahShoeb/darglobal-wasalt-ai)

---

## 🌐 Live Deployments

- **GitHub Repository**: [https://github.com/GhaziahShoeb/darglobal-wasalt-ai](https://github.com/GhaziahShoeb/darglobal-wasalt-ai)
- **Live Local Tunnel (Active)**: [https://uncoated-reliance-babble.ngrok-free.dev](https://uncoated-reliance-babble.ngrok-free.dev)
- **1-Click Permanent Cloud Deploy**: Click the **Deploy to Render** button above to host a 24/7 cloud instance that never sleeps.

---

## 🔒 Security Architecture

The solution has been hardened with enterprise-level security controls:

1. **Container Hardening (Least Privilege)**:
   - Runs under a dedicated, unprivileged non-root user (`appuser`, UID `1000`).
   - Integrated Docker `HEALTHCHECK` monitoring endpoint reachability every 30s.
2. **HTTP Security Headers**:
   - `Content-Security-Policy (CSP)`: Strict allowlist restricting external scripts and fonts.
   - `X-Frame-Options: DENY`: Clickjacking protection.
   - `X-Content-Type-Options: nosniff`: MIME-type sniffing mitigation.
   - `Strict-Transport-Security (HSTS)`: Enforces HTTPS communication.
   - `Referrer-Policy: strict-origin-when-cross-origin`.
   - `Permissions-Policy: camera=(), microphone=(), geolocation=()`.
3. **Application Defense & Rate Limiting**:
   - Sliding-window in-memory rate limiter per IP (`35 req/min` for chat, `120 req/min` for API reads) returning `HTTP 429 Too Many Requests`.
   - Input sanitization stripping control characters, escaping HTML, and strictly bounding query payload size (max 1000 characters).
   - Strict API key regex validation preventing header or command injection.
   - Internal stack traces and error details are suppressed from client responses.
4. **Prompt Hardening**:
   - System prompts are fenced against prompt injection, jailbreaking, and hallucinated regulatory statements.

---

## 🏛️ Professional Institutional UI (Less "Vibe-Coded")

- **Executive Aesthetic**: Designed in the style of financial and institutional property research terminals (e.g. Knight Frank, CBRE, Bloomberg Terminal, DarGlobal Corporate).
- **Subdued Palette**: Deep slate `#0B0F19` background with high-contrast text and subtle champagne/bronze accents.
- **Zero Gimmicks**: Removed neon glowing borders, spinning emoji icons, and promotional jargon in favor of structured data tables, verified filings, and official developer disclosures.
- **Interactive Index**: Slide-out asset index allowing real-time filtering across 260+ records by developer, jurisdiction, and asset class.

---

## 🚀 Running via Docker

```bash
# Build the hardened container
docker build -t darglobal-wasalt-ai .

# Run container with resource limits and health checks
docker run -d --name darglobal-wasalt-ai -p 8000:8000 --restart unless-stopped darglobal-wasalt-ai

# View container logs
docker logs -f darglobal-wasalt-ai
```
