# github_webhook
minimal lightweight github webhook handler in python. with no external dependencies.

it uses python built-in http.server. single-threaded but you don't need anything else for webhook handler.

- change SECRET to secret from your github webhook configuration.
- write event handlers
- run it with supervisor or whatever
