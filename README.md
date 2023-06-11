# Reddit Blackout
Set your subreddits to private for 48 hours

## What is this doing

This repository contains a single simple python script (`blackout.py`) and a single GitHub Actions workflow (`.github/workflows/blackout.yml`). I recommend you read them yourself before giving this access to your account. They should hopefully be simple and well-commented enough to understand even without any programming experience.

The `pyproject.toml` and `poetry.lock` files are from a tool called [Poetry](https://python-poetry.org/) which is a package manager for Python that I prefer over using `pip` directly. The workflow installs and uses poetry already, but if you want to develop it locally without Poetry, there is currently just a single dependency (`praw`), so you can just install it by running `pip install praw` instead.

## Usage

1. Use this repository as a template or fork it (note that forks can't be set to private)

   ![use as a template location](https://github.com/oplik0/reddit-blackout/assets/25460763/c7cefaf8-4304-4e20-9496-b8ce1b5aede1)
   
   or
   
   ![fork button location](https://user-images.githubusercontent.com/25460763/183402131-46c4955f-9545-4ca5-8c9c-da8f860075a5.png)

2. Create a new Reddit app:
    1. Go to https://www.reddit.com/prefs/apps/
    2. Click the `are you a developer? create an app...` button at the bottom of the page
    3. Create some name (for example `blackout`. It can't contain `reddit` though)
    4. Select `script` as the application type
    5. Write some URL in `redirect_uri` - for example `http://localhost` or even something like `http://invalid-uri`. It won't be useful for this application, but Reddit requires that this field contains an URL.
    6. Other fields are optional, so you can just create the app now
    
    ![filled app creation form](https://user-images.githubusercontent.com/25460763/183403287-76139f11-1e2a-4100-ae8f-0e2396e3459b.png)
3. Save two pieces of information from your created app (or just leave the tab open) - client id and secret:

![client id and client secret locations](https://user-images.githubusercontent.com/25460763/183404430-656f88c5-e028-4081-b9d5-a7d7473760da.png)

4. Open your forked repository in another tab and go to Settings, then Security>Secrets>Actions. You'll need to create a total of 4 repository secrets. Repository secrets are saved in encrypted form and can't be retrieved directly - they will even be hidden from actions logs (but if you give them to a malicious script in an action it can still send them somewhere, so beware):
    - `REDDIT_CLIENT_ID` - the ID of the app from earlier
    - `REDDIT_CLIENT_SECRET` - the app secret from earlier
    - `REDDIT_USERNAME` - your username
    - `REDDIT_PASSWORD` - your password; Unfortunately this authentication flow requires it. For hosted applications normal Oauth2 flow would be better, but as this repository is meant to be copied and used for a single account this is the least bad option. WARNING: 2FA unfortunately has to be disabled for this method to work
    - `REDDIT_REFRESH_TOKEN` (optional, instead of username/password) - refresh token obtained from Reddit OAuth API for your account. Unfortunately, as the user is redirected to a specified website during this flow, it's not trivial to set it up here. More info in []
    - `REDDIT_USER_AGENT` (optional) - how the application will identify itself to Reddit. Defaults to "Blackout"
    - `SUBREDDIT_BLACKLIST` (optional) - comma separated list of subreddits excluded from being privated. Takes precedence over whitelist.
    - `SUBREDDIT_WHITELIST` (optional) - comma separated list of subreddits. If set, only the included subreddits will be privated
    - `SUBREDDIT_DESCRIPTION` (optional) - custom text to change the subreddit description to (inserted after the subreddit name)
> **Warning**
> Subreddit names will be visible in backups, so if you don't want them to be public ensure your repository is private.

5. Ensure you have workflows enabled in the repository by going to the Actions tab on the top and selecting `I understand my workflows, go ahead and enable them`:

![Actions warning](https://user-images.githubusercontent.com/25460763/183405553-1ce872f0-7790-466a-a115-7e3f4bdcf0dc.png)

6. And it'd done - the workflow will now run at 00:00 UTC the 12th of July. You can also trigger it manually by going to Actions, selecting `.github/workflows/blackout.yml` and using the `Run workflow` button:

![Running the workflow manually](https://user-images.githubusercontent.com/25460763/183406938-af2f4c77-9f8b-44bb-bf15-6943e120d1e5.png)

## How to use with 2FA

For password authentication reddit requires the user to append the 2FA code after a colon (eg. `yourpassword:123456`). This is obviously not practical for this script. There is a better way - oauth, but unfortunately it's non trivial without a server running. There are 2 options here:
1. Easier one: https://not-an-aardvark.github.io/reddit-oauth-helper/ (note: unfortunately it seems broken in Firefox, try any Chromium based browsers)
   This is a client-side application for generating the required tokens. You need to set the redirect URL in your reddit app to `https://not-an-aardvark.github.io/reddit-oauth-helper/`, paste your client id/secret into the right inputs, select permanent (otherwise the token will be disabled after 1 hour) and select scopes: `modconfig`, `modcontributors` and `mysubreddits`.
   Then click generate tokens, authorize the application, and you should get refresh/access tokens.
   As this app doesn't pass this info to any server (and is running off of GitHub Pages with their URL - so you can see the code here: https://github.com/not-an-aardvark/reddit-oauth-helper), it shouldn't pose any risk. But still, make sure you only grant the token access to what it needs.
2. A bit more advanced: you can use the script provided by praw here: https://praw.readthedocs.io/en/stable/tutorials/refresh_token.html#obtaining-refresh-tokens - the scopes needed are `modconfig`, `modcontributors` and `mysubreddits`. Remember to set redirect URL to the one the script is listening on (`http://localhost:8080``).
   After running the script and inputting the right scopes you should be directed to an authentication URL and then a refresh token will be printed to the console.

Either way, after you have the refresh token, go back to secrets and paste it into a `REDDIT_REFRESH_TOKEN` secret. Then make sure you delete `REDDIT_USERNAME` and `REDDIT_PASSWORD` since praw can be confused if it gets both authentication methods.

## How to change the schedule

The workflow runs using two `cron` triggers in the GitHub Actions workflow. You can easily modify the current schedule or even add more cron expressions. Just edit this part of the file (you can do this easily in the GitHub web UI):
```yaml
on:
  schedule:
    - cron: "0 0 12 06 *"
    - cron: "0 0 14 06 *"
```

If you aren't familiar with cron's notation (and even if you are), you can use a tool like [Crontab.guru](https://crontab.guru/) to create the expression.

## How to do indefinite blackout

Just remove the schedule section of the workflow and run the workflow manually instead
