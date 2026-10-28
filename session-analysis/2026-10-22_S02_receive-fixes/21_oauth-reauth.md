# Gmail/Drive re-auth — waiting for your consent

**Session:** 2026-10-22_S02 · **Turn:** 21 · **T-028**

The local OAuth catcher is running on **:8080** and waiting. Please open this URL and sign in as the
newsroom account (`ainews.msme@gmail.com`), then approve **Gmail, Drive and Sheets**:

```text
https://accounts.google.com/o/oauth2/v2/auth?client_id=279187771445-oicpe7a3rqm4gva8ncsdcrc5078h5uek.apps.googleusercontent.com&redirect_uri=http%3A%2F%2F127.0.0.1%3A8080%2F&response_type=code&scope=openid+email+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.modify+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fspreadsheets&access_type=offline&prompt=consent&include_granted_scopes=true
```

- The browser will redirect to `http://127.0.0.1:8080/?code=...`; a small page should say **Authorised**.
  The catcher then writes `creds/gmail.json`, `creds/drive.json`, `creds/sheets.json` and exits.
- If the redirect page cannot load, **paste the full redirect URL here** and I will exchange it.
- If Google says **Access blocked / app not verified**, the OAuth app is still in **Testing**: add the
  newsroom account as a test user (or publish the app) in Google Cloud, then retry.

After you approve, I will test `/api/emails`, re-run the MATRADE email with the new Google-native export,
and report the result.
