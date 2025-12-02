import os
import requests
def send_simple_message():
  	return requests.post(
  		"https://api.mailgun.net/v3/sandbox344e76659d4f4e838bbbf2d6046eb917.mailgun.org/messages",
  		auth=("api", os.getenv('API_KEY', 'API_KEY')),
  		data={"from": "Mailgun Sandbox <postmaster@sandbox344e76659d4f4e838bbbf2d6046eb917.mailgun.org>",
			"to": "Thomas Gammer <tjg@njit.edu>",
  			"subject": "Hello Thomas Gammer",
  			"text": "Congratulations Thomas Gammer, you just sent an email with Mailgun! You are truly awesome!"})