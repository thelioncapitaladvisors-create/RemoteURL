# TLCS Architecture Update Log
**Date:** July 26, 2026
**Update:** User Session Management & Auth

## 1. Strict Subscription Enforcement
- **Forceful Logout:** Implemented a strict rule regarding user session management. Once a user's subscription ends or expires, they MUST be completely cut off and forcefully logged out (e.g., via `client.auth.signOut()`) from ALL access points.
- **Total Revocation:** This includes the web dashboard, the mobile application, and Telegram access. Expired users are not permitted to linger in the system or access any free marketing dashboards under an authenticated session.
- **Benefit:** This strictly protects intellectual property and forces users to renew their subscription from a completely unauthenticated state, ensuring no loopholes exist for unauthorized access.

## 2. Free Promotion Access
- **Full Access for Active Trials:** If a registered user is offered a free subscription (e.g., a 3-month trial), their `subscription_status` is logged as active until the expiry date. During this active period, the user must have full, unrestricted access to everything that is otherwise available to paid users (treated completely as an 'Elite' or premium user). 
- **Platform Limitation:** This free tier equivalence strictly applies ONLY to the website and mobile app plans. It does NOT include access to premium TradingView Indicator subscriptions.
