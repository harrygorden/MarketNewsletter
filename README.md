# About This [Anvil](https://anvil.works/?utm_source=github:app_README) App

**UNDER DEVELOPMENT:** This app is currently under development. It will fetch a newsletter from your GMail inbox and provide it to AI for analysis. Check back soon to learn more!

## Local Development Setup

To set up the local development environment, follow these steps:

1. **Set up Google Cloud Console**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select an existing one
   - Enable the Gmail API for your project
   - Create OAuth 2.0 credentials (OAuth client ID)
   - Add "http://localhost:8080/" as an "Authorized redirect URI" in the OAuth consent screen
   - Download the client configuration file

2. **Configure Local Files**
   - In the `local_tools` directory:
     1. Copy `example_client_secrets.json` to `client_secrets.json`
     2. Replace the contents with your downloaded Google OAuth credentials
     3. Copy `Example_Uplink_Connect.py` to `Uplink_Connect.py`
     4. In `Uplink_Connect.py`, replace `server_H5WIGHRGGOH3REFDRWQV42VW-JEYPSRQHY3WGCTGA` with your Anvil server uplink code
        - You can find this code in your Anvil app settings under "Uplink"

3. **Get Google OAuth Refresh Token**
   - Run the `get_refresh_token.py` script in the `local_tools` directory
   - Follow the browser authentication flow
   - If no refresh token is generated (shows as "None"):
     1. Go to [Google Account Permissions](https://myaccount.google.com/permissions)
     2. Remove access for this application
     3. Run `get_refresh_token.py` again
   - Save the generated refresh token
   - Add it to your Anvil app's secrets as `google_refresh_token`

4. **Additional Anvil Secrets Required**
   - `google_client_id`: Your Google OAuth client ID
   - `google_client_secret`: Your Google OAuth client secret
   - `sender_email`: Email address of the newsletter sender
   - `openai_api_key`: Your OpenAI API key

### Build web apps with nothing but Python.

The app in this repository is built with [Anvil](https://anvil.works?utm_source=github:app_README), the framework for building web apps with nothing but Python. You can clone this app into your own Anvil account to use and modify.

Below, you will find:
- [How to open this app](#opening-this-app-in-anvil-and-getting-it-online) in Anvil and deploy it online
- Information [about Anvil](#about-anvil)
- And links to some handy [documentation and tutorials](#tutorials-and-documentation)

## Opening this app in Anvil and getting it online

### Cloning the app

Go to the [Anvil Editor](https://anvil.works/build?utm_source=github:app_README) (you might need to sign up for a free account) and click on "Clone from GitHub" (underneath the "Blank App" option):

<img src="https://anvil.works/docs/version-control-new-ide/img/git/clone-from-github.png" alt="Clone from GitHub"/>

Enter the URL of this GitHub repository. If you're not yet logged in, choose "GitHub credentials" as the authentication method and click "Connect to GitHub".

<img src="https://anvil.works/docs/version-control-new-ide/img/git/clone-app-from-git.png" alt="Clone App from Git modal"/>

Finally, click "Clone App".

This app will then be in your Anvil account, ready for you to run it or start editing it! **Any changes you make will be automatically pushed back to this repository, if you have permission!** You might want to [make a new branch](https://anvil.works/docs/version-control-new-ide?utm_source=github:app_README).

### Running the app yourself:

Find the **Run** button at the top-right of the Anvil editor:

<img src="https://anvil.works/docs/img/run-button-new-ide.png"/>


### Publishing the app on your own URL

Now you've cloned the app, you can [deploy it on the internet with two clicks](https://anvil.works/docs/deployment/quickstart?utm_source=github:app_README)! Find the **Publish** button at the top-right of the editor:

<img src="https://anvil.works/docs/deployment-new-ide/img/environments/publish-button.png"/>

When you click it, you will see the Publish dialog:

<img src="https://anvil.works/docs/deployment-new-ide/img/quickstart/empty-environments-dialog.png"/>

Click **Publish This App**, and you will see that your app has been deployed at a new, public URL:

<img src="https://anvil.works/docs/deployment-new-ide/img/quickstart/default-public-environment.png"/>

That's it - **your app is now online**. Click the link and try it!

## About Anvil

If you're new to Anvil, welcome! Anvil is a platform for building full-stack web apps with nothing but Python. No need to wrestle with JS, HTML, CSS, Python, SQL and all their frameworks – just build it all in Python.

<figure>
<figcaption><h3>Learn About Anvil In 80 Seconds👇</h3></figcaption>
<a href="https://www.youtube.com/watch?v=3V-3g1mQ5GY" target="_blank">
<img
  src="https://anvil-website-static.s3.eu-west-2.amazonaws.com/anvil-in-80-seconds-YouTube.png"
  alt="Anvil In 80 Seconds"
/>
</a>
</figure>
<br><br>

[![Try Anvil Free](https://anvil-website-static.s3.eu-west-2.amazonaws.com/mark-complete.png)](https://anvil.works?utm_source=github:app_README)

To learn more about Anvil, visit [https://anvil.works](https://anvil.works?utm_source=github:app_README).

## Tutorials and documentation

### Tutorials

If you are just starting out with Anvil, why not **[try the 10-minute Feedback Form tutorial](https://anvil.works/learn/tutorials/feedback-form?utm_source=github:app_README)**? It features step-by-step tutorials that will introduce you to the most important parts of Anvil.

Anvil has tutorials on:
- [Building Dashboards](https://anvil.works/learn/tutorials/data-science#dashboarding?utm_source=github:app_README)
- [Multi-User Applications](https://anvil.works/learn/tutorials/multi-user-apps?utm_source=github:app_README)
- [Building Web Apps with an External Database](https://anvil.works/learn/tutorials/external-database?utm_source=github:app_README)
- [Deploying Machine Learning Models](https://anvil.works/learn/tutorials/deploy-machine-learning-model?utm_source=github:app_README)
- [Taking Payments with Stripe](https://anvil.works/learn/tutorials/stripe?utm_source=github:app_README)
- And [much more....](https://anvil.works/learn/tutorials?utm_source=github:app_README)

### Reference Documentation

The Anvil reference documentation provides comprehensive information on how to use Anvil to build web applications. You can find the documentation [here](https://anvil.works/docs/overview?utm_source=github:app_README).

If you want to get to the basics as quickly as possible, each section of this documentation features a [Quick-Start Guide](https://anvil.works/docs/overview/quickstarts?utm_source=github:app_README).
