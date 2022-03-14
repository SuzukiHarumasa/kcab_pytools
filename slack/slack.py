import requests
import json

class Slack:
    """
    A simple wrapper for sending messages to slack.

    Inputs:
        - channel_url: Get the Incoming Web Hook URL for the channel you want to send to. The default URL sends to `@alex`.
        - username: The name of the posting username. Default usage assumes a Python cron job, so change as necessary.

    Example:
        slack = Slack()
        slack.success("Hello world!")
        slack.failure("Something went wrong...", e)

    """

    def __init__(self, channel_url: str = "https://hooks.slack.com/services/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",
                        username: str = 'Python Cron Jobs'):
        self.username = username
        self.channel_url = channel_url

    def message(self, message: str = "") -> None:
        "Sends a message to Slack."
        requests.post(self.channel_url,
                        data=json.dumps({
                            'text': message,
                            'username': self.username,
                            'link_names': 1,
                        }),
                        headers={'Content-Type': 'application/json'})

    def success(self, message: str = "") -> None:
        "Sends successful status message to Slack."
        message = f"SUCCESS: {message}"
        self.message(message)

    def failure(self, message: str = "", exception: Exception = None) -> None:
        "Sends unsuccessful status message to Slack."
        message = f"FAILURE: {message}"
        if exception:
            message = f"{message}\n" + '-' * 20 + f'\n{exception}\n' + '-' * 20
        self.message(message)

