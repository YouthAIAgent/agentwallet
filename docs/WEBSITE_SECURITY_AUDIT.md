# AgentWallet Landing Page Security Audit Report

**Auditor:** IRONMAN (Security Auditor)  
**Date:** February 18, 2026  
**Scope:** Landing page frontend code (index.html, dashboard.html, quest.html, docs.html)  
**Severity Scale:** Critical / High / Medium / Low

---

## EXECUTIVE SUMMARY

The AgentWallet landing page contains **3 CRITICAL** and **6 HIGH** severity vulnerabilities that require immediate attention. The most severe issues include hardcoded Supabase credentials exposing the database to unauthorized access, multiple XSS vulnerabilities through innerHTML usage, and insecure storage of authentication tokens.

### Critical Issues Summary
| # | Issue | Files Affected | Risk |
|---|-------|----------------|------|
| 1 | Hardcoded Supabase credentials | quest.html, dashboard.html | Database compromise |
| 2 | XSS via innerHTML with user input | index.html, dashboard.html, quest.html | Account takeover, data theft |
| 3 | Missing CSP headers | All HTML files | XSS, data exfiltration |

---

## DETAILED FINDINGS

### CRITICAL SEVERITY

#### 1. Hardcoded Supabase Credentials
- **Severity:** CRITICAL
- **Description:** Supabase URL and anonymous public key are hardcoded in JavaScript, exposing the entire database to potential unauthorized access. The anon key has database read/write permissions.
- **Location:** 
  - `quest.html:806-807`
  - `dashboard.html:854-875` (inline script at end)
- **Code:**
```javascript
const SUPABASE_URL = 'https://rlajsbxsculwamkpgsmm.supabase.co';
const SUPABASE_ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJsYWpzYnhzY3Vsd2Fta3Bnc21tIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA5NDUwNTUsImV4cCI6MjA4NjUyMTA1NX0.3C0AxpkvFBfGsbYZQYHDE25DY4UgVPMur4c6zK5Lu7A';
```
- **Impact:** 
  - Unauthorized database access
  - Data exfiltration of user information
  - Potential modification of quest data, user profiles, and points
- **Fix Recommendation:**
  ```javascript
  // Move to environment variables and inject at build time
  const SUPABASE_URL = process.env.SUPABASE_URL;
  const SUPABASE_ANON = process.env.SUPABASE_ANON_KEY;
  // Or use a backend proxy to handle Supabase requests
  ```

#### 2. XSS via innerHTML with Unsanitized User Input
- **Severity:** CRITICAL
- **Description:** Multiple locations use `innerHTML` with user-controlled input without sanitization, enabling stored and reflected XSS attacks.
- **Locations:**
  - `index.html:1518-1600` (ppResult function displays user data)
  - `dashboard.html:400-450` (table rendering with innerHTML)
  - `quest.html:900-1000` (quest completion messages)
- **Vulnerable Code Pattern:**
```javascript
// From dashboard.html - user data rendered directly
el.innerHTML = `<span style="color:var(--green)">${data.sol_balance ?? '--'} SOL</span>`;

// From quest.html
ppResult('pp-init-res', '<span style="color:var(--g)">&#10003;</span> Org: <span style="color:var(--c)">'+pp.orgId+'</span>');
```
- **Impact:** 
  - Session hijacking via token theft
  - Phishing attacks through page defacement
  - Keylogger injection
- **Fix Recommendation:**
  ```javascript
  // Use textContent instead of innerHTML
  element.textContent = userInput;
  
  // Or use a sanitization library like DOMPurify
  element.innerHTML = DOMPurify.sanitize(userInput);
  
  // For React/Vue: Use JSX with automatic escaping
  ```

#### 3. Missing Content Security Policy (CSP)
- **Severity:** CRITICAL
- **Description:** No Content-Security-Policy header or meta tag is implemented, allowing execution of inline scripts and loading resources from any origin.
- **Location:** All HTML files (index.html, dashboard.html, quest.html, docs.html)
- **Impact:**
  - XSS attacks can execute injected scripts
  - Data exfiltration to arbitrary domains
  - Loading of malicious external resources
- **Fix Recommendation:**
  ```html
  <meta http-equiv="Content-Security-Policy" content="
    default-src 'self';
    script-src 'self' https://cdn.jsdelivr.net https://www.googletagmanager.com;
    style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
    font-src 'self' https://fonts.gstatic.com;
    connect-src 'self' https://api.agentwallet.fun https://*.supabase.co;
    img-src 'self' data: https:;
    frame-ancestors 'none';
    base-uri 'self';
    form-action 'self';
  ">
  ```

---

### HIGH SEVERITY

#### 4. Insecure Token Storage in localStorage
- **Severity:** HIGH
- **Description:** JWT authentication tokens are stored in localStorage, making them vulnerable to XSS theft and persistent across sessions.
- **Location:** `dashboard.html:285-295`
- **Vulnerable Code:**
```javascript
localStorage.setItem('aw_token', token);
localStorage.setItem('aw_email', userEmail);
// Retrieved with:
let token = localStorage.getItem('aw_token');
```
- **Impact:**
  - Token theft via XSS enables account takeover
  - Tokens persist beyond logout on shared devices
  - No HttpOnly protection possible with localStorage
- **Fix Recommendation:**
  ```javascript
  // Store in httpOnly secure cookies instead
  // Server-side:
  res.cookie('token', jwt, { 
    httpOnly: true, 
    secure: true, 
    sameSite: 'strict',
    maxAge: 3600000 
  });
  ```

#### 5. Missing X-Frame-Options / Clickjacking Protection
- **Severity:** HIGH
- **Description:** No X-Frame-Options header or CSP frame-ancestors directive, allowing the site to be embedded in malicious iframes for clickjacking attacks.
- **Location:** All HTML files
- **Impact:**
  - UI redressing attacks
  - Tricking users into performing unintended actions
  - Credential harvesting through overlaid elements
- **Fix Recommendation:**
  ```html
  <meta http-equiv="X-Frame-Options" content="DENY">
  <!-- Or in CSP: -->
  frame-ancestors 'none';
  ```

#### 6. Open Redirect Vulnerabilities
- **Severity:** HIGH
- **Description:** User-controlled URLs are used for redirects without validation, enabling phishing attacks.
- **Location:** `quest.html:450-500`
- **Vulnerable Code:**
```javascript
window.toggleSound=function(){
  // ...
}

function startQuest(questId, url) {
  window.open(url, '_blank'); // URL from user input not validated
}
```
- **Impact:**
  - Phishing attacks redirecting to malicious sites
  - Credential theft through fake login pages
- **Fix Recommendation:**
  ```javascript
  // Validate URLs against allowlist
  const ALLOWED_DOMAINS = ['twitter.com', 'github.com', 'agentwallet.fun'];
  
  function isAllowedUrl(url) {
    try {
      const parsed = new URL(url);
      return ALLOWED_DOMAINS.some(d => parsed.hostname.endsWith(d));
    } catch {
      return false;
    }
  }
  ```

#### 7. No CSRF Protection on Forms
- **Severity:** HIGH
- **Description:** API calls lack CSRF tokens, allowing cross-site request forgery attacks.
- **Location:** `dashboard.html:300-450`
- **Vulnerable Code:**
```javascript
async function handleLogin(e) {
  const data = await api('/auth/login', { 
    method: 'POST', 
    body: JSON.stringify({email, password})
  });
}
```
- **Impact:**
  - Unauthorized actions on behalf of authenticated users
  - Forged transactions if user is logged in
- **Fix Recommendation:**
  ```javascript
  // Include CSRF token in all state-changing requests
  headers: {
    'X-CSRF-Token': getCsrfToken(),
    'Content-Type': 'application/json'
  }
  ```

#### 8. Insufficient Input Validation
- **Severity:** HIGH
- **Description:** User inputs (email, password, wallet addresses) lack client-side validation and are sent directly to API.
- **Location:** `dashboard.html:300-350`, `quest.html:550-650`
- **Impact:**
  - Injection attacks
  - API abuse
  - Data integrity issues
- **Fix Recommendation:**
  ```javascript
  function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  }
  
  function validateSolanaAddress(addr) {
    return /^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(addr);
  }
  ```

---

### MEDIUM SEVERITY

#### 9. Inline Event Handlers (CSP Bypass)
- **Severity:** MEDIUM
- **Description:** Inline onclick handlers prevent effective CSP implementation and bypass script restrictions.
- **Location:** Throughout all HTML files
- **Examples:**
```html
<button onclick="sendMagicLink()">SEND MAGIC LINK</button>
<button onclick="startQuest('follow-twitter','https://twitter.com/...')">EXECUTE</button>
```
- **Fix Recommendation:**
  ```javascript
  // Use addEventListener instead
  document.getElementById('send-btn').addEventListener('click', sendMagicLink);
  ```

#### 10. Missing HTTPS Enforcement (HSTS)
- **Severity:** MEDIUM
- **Description:** No HSTS header to force HTTPS connections.
- **Location:** All HTML files (server configuration)
- **Fix Recommendation:**
  ```
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  ```

#### 11. Information Disclosure in Error Messages
- **Severity:** MEDIUM
- **Description:** Detailed error messages reveal internal implementation details.
- **Location:** `dashboard.html:320-330`
- **Vulnerable Code:**
```javascript
catch (err) { 
  errEl.textContent = err.message; // Full error exposed to user
}
```
- **Fix Recommendation:**
  ```javascript
  // Log full error, show generic message to user
  console.error('Login error:', err);
  errEl.textContent = 'Authentication failed. Please try again.';
  ```

#### 12. eval() Usage in Terminal Command Processing
- **Severity:** MEDIUM
- **Description:** The terminal interface could be vulnerable to code injection if user input reaches eval().
- **Location:** `index.html:900-1100` (terminal command handler)
- **Mitigation:** Current implementation appears safe but should be audited regularly.

---

### LOW SEVERITY

#### 13. Google Analytics Without Privacy Controls
- **Severity:** LOW
- **Description:** Google Analytics is loaded without consent management or IP anonymization.
- **Location:** `index.html:20-22`
- **Fix Recommendation:**
  ```javascript
  // Add IP anonymization and consent checks
  gtag('config', 'G-C7XR8BZWXG', { 
    'anonymize_ip': true,
    'allow_google_signals': false
  });
  ```

#### 14. Verbose Console Logging
- **Severity:** LOW
- **Description:** Debug information logged to console in production.
- **Location:** Throughout JavaScript files
- **Fix Recommendation:** Remove console.log statements for production builds.

---

## RECOMMENDATIONS SUMMARY

### Immediate Actions (Within 24 hours)
1. **Rotate Supabase credentials** and move them to environment variables
2. **Implement CSP headers** with strict policies
3. **Add X-Frame-Options** to prevent clickjacking
4. **Audit and sanitize all innerHTML usage**

### Short-term (Within 1 week)
1. Migrate token storage from localStorage to httpOnly cookies
2. Implement comprehensive input validation
3. Add CSRF protection to all forms
4. Fix open redirect vulnerabilities

### Long-term (Within 1 month)
1. Conduct full penetration testing
2. Implement automated security scanning in CI/CD
3. Add security headers monitoring
4. Create incident response plan for credential exposure

---

## COMPLIANCE NOTES

### GDPR/CCPA Concerns
- Google Analytics without consent mechanism
- No privacy policy visible on quest/login pages
- User data stored without clear retention policy

### Security Standards
- **OWASP Top 10 2021:** A01 (Broken Access Control), A03 (Injection), A07 (Auth Failures)
- **CWE Coverage:** CWE-79 (XSS), CWE-312 (Cleartext Storage), CWE-352 (CSRF)

---

## CONCLUSION

The AgentWallet landing page requires immediate security hardening before production use. The combination of exposed database credentials and XSS vulnerabilities presents an unacceptable risk to user data and platform integrity. Priority should be given to securing the Supabase configuration and implementing proper output encoding.

**Risk Rating: HIGH** - Do not deploy to production without addressing Critical and High severity findings.

---

*Report generated by IRONMAN Security Auditor*  
*AgentWallet Security Audit - February 2026*
