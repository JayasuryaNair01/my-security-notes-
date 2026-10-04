1. What is it?

WCD occurs when an attacker tricks a web cache (CDN or reverse proxy) into saving a victims's private, dynamic HTTP response by appending a static file extension (eg.., .css, .js, .png) to a private URL.

When victim clicks the crafted link, the origin server ignores the fake extension and returns their sensitive data, while cache sees the .css extension and saves a public copy. The attacker then visits the exact same url to view the cached private data.

2. Do you need info about the victim?

No. In most WCD scenarios. But the victim should be logged in at the time of attack to make it succesull.
Because WCD exploits generic dynamic routes ( e.g., /my-account, /dashboard/profile, /api/v1/user/settings), the URL is relative to whoever clicks it:

    When Victim A visits [https://zerothehero.com/my-account/style.css](https://zerothehero.com/my-account/style.css), the backend reads Victim A's session cookie and renders Victim A's profile.

    The cache saves Victim A's profile under the key [zerothehero.com/my-account/style.css](https://zerothehero.com/my-account/style.css).

    The attacker then requests [https://zerothehero.com/my-account/style.css](https://zerothehero.com/my-account/style.css) without cookies and gets Victim A's profile data straight out of the cache.

Exception: If the endpoint explicitly uses a user ID in the path (e.g., /user/1042/profile), the attacker would need the victim's ID to construct /user/1042/profile/style.css.

3. How Attackers Trick victims into opening the link ( Delivery vectors)

Method A: Hidden Image Tag/ Zero-Click HTML Payload (Most Common)

   Attacker hosts an HTML page on their own site ([https://attacker-site.com/exploit.html](https://attacker-site.com/exploit.html)) containing a hidden HTML tag:

   # <!-- The victim's browser automatically requests this image upon loading the page -->
   <img src="https://zerothehero.com/my-account/style.css" style="display:none;" />

   When the victim visits attacker-site.com while logged into zerothehero.com, their browser automatically fires a background request to fetch the "image". The browser attaches the victim's session cookies, the cache stores the response, and the attack succeeds without the victim clicking anything on zerothehero.com.

Method B: Javascript fetch() /XMLHttpRequest

   The attacker uses a simple JS script on a phishing or malicious landing page:

   // Automatically triggers background fetch with credentials
   fetch('https://zerothehero.com/dashboard/profile/avatar.css', {
    credentials: 'include'
   });

Method C: Direct Social Engineering

Sending the direct link directly via email, forum comments, or chat messages:

    "Hey, check out this broken page style: [https://zerothehero.com/my-account/style.css](https://    zerothehero.com/my-account/style.css)"

4. Reconnaissance & Fingerprinting

Look for these specific indicators in your Burp HTTP history before attempting exploitation:

    Caching Proxy Detection: Review HTTP response headers on the target application:

    X-Cache: HIT or X-Cache: MISS

    CF-Cache-Status: HIT (Cloudflare)

    Age: 120

    Cache-Control: public, max-age=...

    Path Discrepancy Identification: The backend web server uses non-strict path routing (e.g., frameworks like Spring, Express, or Django) where extra path segments after a valid endpoint do not break the page.

5. Verification Criteria (Is it actually vulnerable?)

Verify these three conditions in order before declaring a true positive:

1. Path Stripping/Delimeter Handling: Sending GET /my-account/test.css returns the standard 200 ok content of /myaccount instead of a 404 Not Found.

2. Cache State Transition: Reponse headers for /my-account/test.css transition from x-cache: MISS on the first request to HIT on the second request.

3. Sensitive Data Exposure: The response contains user-specific sensitive data (eg., API keys, CSRF tokens, email address) and oes not default to an unauthenticated/guest state when cached.


6. Tool Execution Frameworks

A. Burp Suite (Manual & Automation Workflow)

Step 1: Path & Delimiter Fuzzing via Burp Intruder

    Send a private request (e.g., GET /dashboard/profile HTTP/2) to Intruder.

    Set the position marker around the path separator and static extension:
    GET /dashboard/profile§PAYLOAD§style.css HTTP/2

    In Payloads, set type to Simple List and add common delimiters:
    /, ;, %23, %3F, %00, ?, #

    Run the attack and sort by Status Code and Length to find endpoints returning 200 OK instead of 404.

Step 2: Cache Header Verification in Repeater

    Send the successful candidate path (e.g., GET /dashboard/profile/style.css) to Burp Repeater.

    Request 1: Click Send with your active session cookie attached. Check for X-Cache: MISS in the response headers.

    Request 2: Click Send again immediately. Check if X-Cache changes to HIT.

    Request 3 (Attacker Verification): Remove the Cookie: header entirely and click Send. If you receive 200 OK containing the private dashboard data with X-Cache: HIT, the vulnerability is confirmed.

7. Attack Variations & Bypasses


[ Attacker hosts page with <img> ] ──► [ Victim visits page while logged in ]
                                                     │
                                                     ▼
[ Attacker fetches URL ] ◄── [ Cache stores response ] ◄── [ Origin returns private data ]



Variation 1: Standard Path Extension

Appends an extension directly to the end of a valid endpoint.

    Payload: [https://zerothehero.com/api/v1/user/settings/static.js](https://zerothehero.com/api/v1/user/settings/static.js)

    Backend Behavior: Server strips /static.js and serves /api/v1/user/settings.

    Cache Behavior: Caches the response under key .../settings/static.js.

Variation 2: Delimiter Injection (Matrix Parameters / Encodings)

Uses special characters to break the origin server's path parser while keeping the cache parser intact.

    Payloads:

        [https://zerothehero.com/dashboard;style.css](https://zerothehero.com/dashboard;style.css) (Java/Spring matrix parameter)

        [https://zerothehero.com/dashboard%23style.css](https://zerothehero.com/dashboard%23style.css) (URL-encoded # fragment)

        [https://zerothehero.com/dashboard%3F.css](https://zerothehero.com/dashboard%3F.css) (URL-encoded ? query)

    Mechanism: The backend interprets ; or %23 as a path separator and stops parsing, returning /dashboard. The CDN does not decode %23 and reads .css as a static file extension.

Variation 3: Path Traversal Deception

Targets origin normalization rules by starting with a static cache path.

    Payload: [https://zerothehero.com/static/js/..%2f..%2fdashboard](https://zerothehero.com/static/js/..%2f..%2fdashboard)

    Mechanism: The CDN sees /static/js/ at the start and marks it cacheable. The backend normalizes ..%2f to navigate up to /dashboard.

Web Cache Deception relies entirely on getting two different systems—the Cache Server (CDN/Proxy) and the Origin Server (Backend Framework)—to interpret the exact same URL string in two completely different ways:

    The Cache Server looks at the URL to decide: "Is this a public static asset that I should store in memory?"

    The Origin Server looks at the URL to decide: "Which dynamic code controller should I execute to generate the response?"

Different path manipulation techniques are used depending on how strictly the target application and CDN parse URLs.

1. Standard Path Extension (/path/style.css)
How It Works

You append a static file extension directly to the end of a valid dynamic endpoint.

    Example URL: [https://example.com/account/settings/style.css](https://example.com/account/settings/style.css)

Why Use It?

This is the simplest technique and works against non-strict, REST-style backend routers (e.g., Express.js, Django, Ruby on Rails, or Spring) that use wildcard or path-prefix matching.

    Backend View: The framework matches the prefix /account/settings and simply ignores or strips the extra trailing segment /style.css, returning the private user settings page.

    Cache View: The CDN checks the end of the URL path string, sees .css, and marks the response as a cacheable static asset.

When to Use

Use this first as your baseline test. It is effective against modern single-page apps (SPAs) or backend APIs where the framework router handles path parameters flexibly.
2. Delimiter Injection (/path;style.css or /path%23style.css)
How It Works

You insert special characters (delimiters) between the dynamic route and the fake static extension to trick the backend parser into truncating the path early.

    Example URLs:

        Matrix parameters: [https://example.com/account/settings;style.css](https://example.com/account/settings;style.css)

        Fragment encoding: [https://example.com/account/settings%23style.css](https://example.com/account/settings%23style.css)

        Query encoding: [https://example.com/account/settings%3Fstyle.css](https://example.com/account/settings%3Fstyle.css)

Why Use It?

If standard path extensions return a 404 Not Found because the backend router enforces strict path matching, delimiter injection is used to force path truncation on the backend while keeping the extension visible to the CDN.

    Backend View: Frameworks like Java/Spring interpret ; as a matrix parameter delimiter, or treat %23 (#) / %3F (?) as the start of non-path data. The backend stops reading the path at the delimiter and executes /account/settings.

    Cache View: Most CDNs evaluate raw, unencoded URL strings without decoding percent-encoded characters like %23 or parsing frame-specific matrix parameters ;. The CDN reads the entire string to the end, sees .css, and treats it as a static file key.

When to Use

Use this when standard path extensions fail with a 404 or 400 error, particularly on enterprise frameworks (like Java Spring or ASP.NET) or when a reverse proxy normalizes paths differently than the backend.
3. Path Traversal / Normalization Mismatch (/static/..%2f/account)
How It Works

You structure the URL so it begins with a known, legitimate static directory path, followed by path traversal sequences pointing back to a dynamic endpoint.

    Example URL: [https://example.com/assets/css/..%2f..%2faccount/profile](https://example.com/assets/css/..%2f..%2faccount/profile)

Why Use It?

This technique targets directory-based caching rules. Many CDN configurations use rules like "Cache everything that lives inside the /assets/ or /static/ directory" rather than relying solely on file extensions.

    Cache View: The CDN inspects the beginning of the path (/assets/css/), matches its static directory caching rule, and marks the request as cacheable without normalizing the ..%2f sequence.

    Backend View: The web server or framework decodes %2f (/), resolves the directory traversal (/assets/css/../../account/profile), and executes the dynamic /account/profile controller.

When to Use

Use this when the target CDN does not cache based on file extensions, but instead uses strict directory-level caching rules (e.g., caching everything under /static/ or /public/).

8. Defensive Engineering & Remediation

To make an application secure against Web Cache Deception, apply defenses at both the application server layer and the cache/CDN layer:

    Set Explicit Cache-Control Headers: Ensure all endpoints delivering dynamic, private user content return strict non-caching directives:
    HTTP

    Cache-Control: no-store, no-cache, must-revalidate, private

    Align Cache and Origin Path Rules: Configure the CDN and web server to use identical path normalization and extension parsing rules so they never disagree on what constitutes a static resource.

    Use Strict Origin Routing: Ensure backend web frameworks return a 404 Not Found for any URL containing invalid trailing extensions or matrix parameters (e.g., rejecting /dashboard/style.css if only /dashboard is defined).

    Implement Content-Type Checking at Cache: Configure the CDN to ignore file extensions in the URL and only cache responses whose Content-Type header explicitly matches static assets (e.g., text/css, application/javascript, image/png).

    Set SameSite=Strict or Lax on Session Cookies: Restricts cookies from being sent on cross-site subresource requests (like <img> tags loaded from an attacker domain), neutering the background delivery vector.
