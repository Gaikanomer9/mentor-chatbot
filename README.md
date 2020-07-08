# Mentor chatbot for Facebook Messenger

Raido is open sourced chatbot for Facebook Messenger. 

### How the bot works?

You select the skill you want to master (Photoshop, Docker, Kubernetes, Frontend development and etc.), your level and time you have. After that Raido proposes the path with several tasks that you need to complete in order to master that skill. Alongside the way you will get notification (in a several days - when Raido thinks you should be done with the task and if user agreed to receive such a notification) and get a new task.

To try out the chatbot write to the app page [here](https://www.facebook.com/Raido-Mentor-Bot-109235004160923).

### Deployment

The bot is hosted in GCP and deployed via Cloud Build to Cloud Run service. It happened automatically with push to master branch.

### Local debugging

For deploying and running locally use the Makefile. You would need to prepare the google cloud credentials for your test environment and download the ngrok.

For testing the bot itself create a new test app in Facebook apps and the ngrok link as the endpoint. After that feel free to create a new pull request for changes.

### Contributing

Feel free to explore the bot and propose your ideas as issues.


Or start with a new fork and create a new pull request for this repository. As soon as it's reviewed and merged the automatic deployment will occur.
