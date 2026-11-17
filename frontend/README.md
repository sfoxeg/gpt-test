# CatchMe frontend

React + TypeScript + Vite mobile-first client. One codebase supports browser/PWA and native iOS/Android shells through Capacitor 7.

## Features
- Registration and login via `/api/v1/auth/*`
- Profile load/update via `/api/v1/me` and `/api/v1/profiles/me`
- Filtered partner discovery via `/api/v1/profiles`
- Chat creation, list, history and sending via `/api/v1/chats`
- Token persistence through Capacitor Preferences with a web localStorage fallback

## Web development
```bash
cd frontend
npm install
npm run dev
```
Set `VITE_API_URL` to the reachable API base, e.g. `http://localhost:8000/api/v1`.

## Production web/PWA
```bash
cd frontend
npm run build
```
Serve `dist` over HTTPS. The PWA manifest is `/manifest.webmanifest`.

## Native apps
Install Node.js 20+ and platform tooling:
- Android: Android Studio + Android SDK.
- iOS: macOS + Xcode (iOS builds cannot be produced on Windows/Linux).

```bash
cd frontend
npm install
npx cap add android
npx cap add ios
npm run cap:sync
npm run cap:android
npm run cap:ios
```

Set `VITE_API_URL` at build time to a publicly reachable HTTPS API endpoint before building mobile binaries. Do not use localhost for a device build: localhost points to the phone itself. Configure FastAPI CORS for your deployed web origin and the Capacitor app origins. Native platform directories are generated locally and are not committed until signing, icons, splash screens and deployment settings are configured.
