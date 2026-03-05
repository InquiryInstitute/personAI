# GitHub Device Flow Setup Guide

This guide will help you set up GitHub Device Flow for PersonAI, allowing users to authenticate with their GitHub accounts using a simple code - no callback URLs or redirects needed!

## Why Device Flow?

- ✅ No callback URL configuration needed
- ✅ Works perfectly with static sites (GitHub Pages)
- ✅ Simple user experience (enter a code)
- ✅ No backend redirect handling required
- ✅ Secure OAuth 2.0 flow
- ✅ Great for CLI tools and static web apps

## How It Works

1. User clicks "Continue with GitHub"
2. App requests a device code from GitHub
3. User sees a code (e.g., `ABCD-1234`)
4. GitHub opens in new tab for authorization
5. User enters the code on GitHub
6. App polls GitHub until user authorizes
7. User is authenticated!

## Setup Steps

### 1. Create a GitHub OAuth App

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click "OAuth Apps" → "New OAuth App"
3. Fill in the application details:
   - **Application name**: `PersonAI` (or your custom name)
   - **Homepage URL**: `https://yourusername.github.io/PersonAI`
   - **Authorization callback URL**: `http://localhost` (required but not used for device flow)
4. Click "Register application"

### 2. Get Your Credentials

After creating the app, you'll see:
- **Client ID**: Copy this value
- **Client Secret**: Click "Generate a new client secret" and copy it

⚠️ **Important**: Keep your Client Secret secure! Never commit it to version control.

### 3. Configure Your Environment

Add to your `.env` file:

```bash
# GitHub OAuth (Device Flow)
GITHUB_CLIENT_ID=Ov23liDA7zxsT4FkKh5Y
GITHUB_CLIENT_SECRET=your_client_secret_here
```

That's it! No `FRONTEND_URL` or callback configuration needed.

## Testing Locally

1. Start the backend:
   ```bash
   python main.py
   ```

2. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Visit `http://localhost:5173`
4. Click "Continue with GitHub"
5. Copy the code shown
6. Authorize on GitHub
7. You're in!

## Production Deployment

Device flow works great with static sites:

1. Deploy frontend to GitHub Pages (automatic with push to main)
2. Deploy backend to any service (Heroku, Railway, Fly.io, etc.)
3. Update frontend API URL if needed

No callback URL configuration required!

## OAuth Scopes

PersonAI requests these GitHub scopes:
- `repo`: Full access to repositories (read/write)
- `read:user`: Read user profile information
- `user:email`: Access user email addresses

## Security Features

- **Device Code**: One-time use code for authorization
- **Polling**: Secure polling mechanism prevents token exposure
- **Expiration**: Device codes expire after 15 minutes
- **Rate Limiting**: Built-in rate limit protection

## Troubleshooting

### "GitHub OAuth not configured" error
- Ensure `GITHUB_CLIENT_ID` is set in `.env`
- Restart the backend server after adding environment variables

### "Authentication timeout" error
- Device codes expire after 15 minutes
- Click "Continue with GitHub" again to get a new code

### Code not working
- Make sure you're entering the code on github.com/login/device
- Check that you're logged into the correct GitHub account
- Try generating a new code

## For Students

If you're a student using PersonAI:

1. Fork the repository
2. Create your own GitHub OAuth App
3. Add your Client ID and Secret to `.env` (never commit this file!)
4. Deploy and use - no callback URL setup needed!

## API Endpoints

The device flow uses these endpoints:

- `GET /auth/github/device/start` - Start device flow, get user code
- `POST /auth/github/device/poll` - Poll for authorization completion

## Resources

- [GitHub Device Flow Documentation](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#device-flow)
- [OAuth 2.0 Device Flow Spec](https://oauth.net/2/device-flow/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
