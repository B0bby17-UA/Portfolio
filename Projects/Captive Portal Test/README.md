# Captive Portal Test

A proof-of-concept fake captive portal that replicates a Wi-Fi login page for **WI-FI FORUM AVEIRO**. Built as a social engineering demonstration to show how easily users can be tricked into submitting credentials on a spoofed page.

## Overview

This project replicates the look and feel of a legitimate public Wi-Fi captive portal — the kind you see at malls, airports, and hotels. The page mimics a Google login flow, guiding the user through a two-step form (email → password) that feels authentic at first glance.

The goal is educational: to raise awareness about how convincing phishing pages can be and why users should always verify the URL before entering sensitive information.

## Features

- **Pixel-perfect Google login replication** — styled to match the real Google authentication flow
- **Two-step form** — email first, then password, just like the real thing
- **Smooth transitions** — animated screen changes between initial → login → success
- **Network verification simulation** — fake "Verifying network..." screen adds legitimacy
- **Responsive design** — works on both desktop and mobile devices
- **Self-contained** — all HTML, CSS, and JavaScript in a single file (no external dependencies)
- **Credential capture** — form submissions POST to a configurable endpoint
- **Metadata logging** — records the AP name (`WI-FI FORUM AVEIRO`) and login timestamp with each submission

## How It Works

1. The user connects to a fake Wi-Fi network (or is redirected via DNS spoofing)
2. A captive portal page appears, showing the **WI-FI FORUM AVEIRO** login screen
3. The user clicks **"Continuar com Google"** (Continue with Google)
4. A fake "Verifying network..." screen appears briefly
5. A Google-style login form appears — first asking for email, then password
6. After submission, a success screen is shown ("Connected! You can close this screen and browse safely") while credentials are captured in the background

## Detection

Despite the realistic appearance, the page has subtle tells:

- **No HTTPS padlock** — the URL doesn't match Google's domain
- **Placeholder links** — Terms of Service, Privacy Policy, and Help links point nowhere
- **No real OAuth flow** — the form submits directly to a local endpoint (`/BruceEvilCreds/credenciais.txt`), not Google's servers
- **Slight visual inconsistencies** — fonts, spacing, or colors may differ from the real page
- **Hidden metadata fields** — the form includes hidden inputs for AP name and timestamp, which wouldn't exist on a real Google login

## File Structure

```
captive-portal-test/
├── index.html          # Main captive portal page (all-in-one)
├── README.md           # This file (English)
└── README.pt-BR.md     # Português do Brasil
```

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/captive-portal-test.git
   cd captive-portal-test
   ```

2. Configure the form action endpoint in `index.html`:
   ```html
   <form id="loginForm" method="POST" action="/BruceEvilCreds/credenciais.txt">
   ```

3. Serve the page using a local web server:
   ```bash
   # Python
   python -m http.server 8080

   # Node.js
   npx http-server -p 8080
   ```

4. Access the page at `http://localhost:8080`

## Technical Details

| Component | Technology |
|-----------|------------|
| Markup | HTML5 |
| Styling | Inline CSS (Google-inspired design system) |
| Logic | Vanilla JavaScript (no frameworks) |
| Icons | Base64-encoded PNGs and SVGs |
| Forms | Two-step email → password flow with client-side validation |
| Data capture | POST to `/BruceEvilCreds/credenciais.txt` |

## Form Fields

| Field | Type | Description |
|-------|------|-------------|
| `ap_name` | hidden | Network SSID (`WI-FI FORUM AVEIRO`) |
| `login_date` | hidden | ISO timestamp of submission |
| `email` | text | User's email address |
| `password` | password | User's password |

## Use Cases

- **Security awareness training** — demonstrate phishing risks to non-technical users
- **Penetration testing** — test organizational resilience against credential phishing
- **Education** — teach students about social engineering and web security

## Disclaimer

This tool is intended **exclusively for authorized security testing and educational purposes**. Unauthorized use of this tool to capture credentials without explicit consent is illegal and unethical. The author assumes no responsibility for misuse.

## License

MIT
