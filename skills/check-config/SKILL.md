---
name: check-config
description: Validate required API keys and configuration for the requested Angel AI task. Inspects USER_PROJECT/.env.angel, reports missing keys, and guides the user to fill them in.
---

# Angel AI — Check Config

## Purpose
Validate that all required API keys are present before running an analysis or report.

## Trigger
Use this skill when: the user selects a platform, before starting any workflow, or when an API call fails due to missing credentials.

## Behavior

1. Load USER_PROJECT/.env.angel (not .env — always use .env.angel).
2. Determine which keys are required for the selected platform or service.
3. For each missing key, handle **one at a time** — do not batch or skip ahead:
   - Append the variable name (without value) to USER_PROJECT/.env.angel.example if not already there.
   - Tell the user the key is missing and include a brief plain-English summary of how to obtain it (see Key Inventory below for per-key guidance).
   - Wait for the user to confirm the key is filled in before proceeding to the next missing key.
4. Only continue to the workflow once every required key is confirmed present.

## Key Inventory by Platform

### General / Kaggle
- **KAGGLE_USERNAME** — Your Kaggle account username.
  > **How to get:** Go to kaggle.com → Account → Settings → scroll to API section → copy your username. Free account required.
- **KAGGLE_KEY** — Your Kaggle API token.
  > **How to get:** Same page → click "Create New API Token" — this downloads `kaggle.json`. The `key` field in that file is your KAGGLE_KEY.

### Google Cloud / BigQuery / Vertex AI
- **GOOGLE_APPLICATION_CREDENTIALS** — Path to your service account JSON file on disk.
  > **How to get:** Google Cloud Console → IAM & Admin → Service Accounts → create or select a service account → Keys → Add Key → JSON. Save the file and paste its full local path here.
- **GOOGLE_CLOUD_PROJECT** — Your Google Cloud project ID (not the display name).
  > **How to get:** Google Cloud Console → top project selector → copy the Project ID (e.g. `my-project-123456`). Free tier available with $300 credit for new accounts.

### Shopify
- **SHOPIFY_SHOP_DOMAIN** — Your store's `.myshopify.com` domain (e.g. `mystore.myshopify.com`).
  > **How to get:** Shopify Admin → Settings → Domains — use the primary `.myshopify.com` address.
- **SHOPIFY_ACCESS_TOKEN** — Private app or custom app access token.
  > **How to get:** Shopify Admin → Apps → Develop apps → Create an app → API credentials → Install app → copy the Admin API access token. Requires Partner or store owner access.

### Square
- **SQUARE_ACCESS_TOKEN** — Personal or OAuth access token.
  > **How to get:** developer.squareup.com → Applications → select your app → Credentials → copy the Access Token. Sandbox token available for testing, no payment required.
- **SQUARE_ENVIRONMENT** — Set to `sandbox` for testing or `production` for live data.

### QuickBooks
- **QUICKBOOKS_CLIENT_ID** — OAuth 2.0 client ID.
  > **How to get:** developer.intuit.com → Dashboard → My Apps → create or select an app → Keys & OAuth → copy Client ID.
- **QUICKBOOKS_CLIENT_SECRET** — OAuth 2.0 client secret (same location as above).
- **QUICKBOOKS_REFRESH_TOKEN** — Long-lived refresh token obtained after OAuth flow.
  > **How to get:** Complete the OAuth 2.0 authorization flow for your app; the refresh token is returned at the end. Use Intuit's OAuth Playground for quick setup.
- **QUICKBOOKS_REALM_ID** — Your QuickBooks company ID.
  > **How to get:** After connecting via OAuth, the realm ID is returned in the redirect URL and token response.

## Rules
- Never insert real secret values anywhere.
- Never use the generic .env file; always use .env.angel.
- Handle missing keys one at a time — do not batch or skip ahead.
- When prompting the user to choose a platform, do not label "General" as the recommended option.
