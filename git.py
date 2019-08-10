#!/usr/bin/env python3

import requests

import os, logging
from flask import Flask, request, jsonify
from html import escape
from bot import bot

from config import BOT_TOKEN

app = Flask(__name__)  # Standard Flask app

# logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger()

BOT_API = 'https://api.telegram.org/bot{}/'.format(BOT_TOKEN)

checkbot = requests.get(BOT_API + "getMe").json()
if not checkbot['ok']:
	log.error("Token invalid!\nBot exit...")
	exit(1)
else:
	log.info("Bot was valid, logged in as @{}".format(checkbot['result']['username']))


def post_tg(chat, message, parse_mode):
	response = requests.post(BOT_API + "sendMessage", params={"chat_id": chat, "text": message, "parse_mode": parse_mode, "disable_web_page_preview": True}).json()
	return response

def reply_tg(chat, message_id, message, parse_mode):
	response = requests.post(BOT_API + "sendMessage", params={"chat_id": chat, "reply_to_message_id": message_id, "text": message, "parse_mode": parse_mode, "disable_web_page_preview": True}).json()
	return response


@app.route("/<groupid>", methods=['GET', 'POST'])
def git_api(groupid):
	data = request.json
	# If webhook was set
	if data.get('hook'):
		response = post_tg(groupid, "Successfully set webhook for <b>{}</b> by <a href='{}'>{}</a>!".format(data['repository']['name'], data['sender']['html_url'], data['sender']['login']), "html")
		return response
	# If push
	if data.get('commits'):
		commits_text = ""
		for x in data['commits']:
			commits_text += f"<a href='{x['url']}'>{x['id'][:7]}</a> - {x['author']['name']} {escape('<')}{x['author']['email']}{escape('>')}\n<code>{escape(x['message'])}</code>"
			if len(data['commits']) >= 2:
				commits_text += "\n———————————————————————\n"
			if len(commits_text) > 1000:
				text = """<b>{}</b> - New {} commits ({})

{}
""".format(escape(data['repository']['name']), len(data['commits']), escape(data['ref'].split("/")[-1]), commits_text)
				response = post_tg(groupid, text, "markdown")
				commits_text = ""
		text = """🔨 <b>{}</b> - New {} commits ({})

{}
""".format(escape(data['repository']['name']), len(data['commits']), escape(data['ref'].split("/")[-1]), commits_text)
		response = post_tg(groupid, text, "html")
		return response
	# if issue
	if data.get('issue'):
		if data.get('comment'):
			text = """💬 New comment issue for <b>{}</b>

<code>{}</code>

<a href='{}'>Issue #{}</a>
""".format(escape(data['repository']['name']), escape(data['comment']['body']), data['comment']['html_url'], data['issue']['number'])
			response = post_tg(groupid, text, "html")
			return response
		text = """🧾 New {} issue for <b>{}</b>

<b>{}</b>
<code>{}</code>

<a href='{}'>issue #{}</a>
""".format(data['action'], escape(data['repository']['name']), escape(data['issue']['title']), escape(data['issue']['body']), data['issue']['html_url'], data['issue']['number'])
		response = post_tg(groupid, text, "html")
		return response
	# If pull request
	if data.get('pull_request'):
		if data.get('comment'):
			text = """💬 New comment pull request for <b>{}</b> ({})

<code>{}</code>

<a href='{}'>Pull request #{}</a>
""".format(escape(data['repository']['name']), data['pull_request']['state'], escape(data['comment']['body']), data['comment']['html_url'], data['issue']['number'])
			response = post_tg(groupid, text, "html")
			return response
		text = """📊 New {} pull request for <b>{}</b>

<b>{}</b> ({})
<code>{}</code>

<a href='{}'>Pull request #{}</a>
""".format(data['action'], escape(data['repository']['name']), escape(data['pull_request']['title']), data['pull_request']['state'], escape(data['pull_request']['body']), data['pull_request']['html_url'], data['pull_request']['number'])
		response = post_tg(groupid, text, "html")
		return response
	url = deldog(data)
	response = post_tg(groupid, "⚠️ Undetected response: {}".format(url), "markdown")
	return response


# For reporting undetected api
def deldog(data):
	BASE_URL = 'https://del.dog'
	r = requests.post(f'{BASE_URL}/documents', data=str(data).encode('utf-8'))
	if r.status_code == 404:
		update.effective_message.reply_text('Failed to reach dogbin')
		r.raise_for_status()
	res = r.json()
	if r.status_code != 200:
		update.effective_message.reply_text(res['message'])
		r.raise_for_status()
	key = res['key']
	if res['isUrl']:
		reply = f'Shortened URL: {BASE_URL}/{key}\nYou can view stats, etc. [here]({BASE_URL}/v/{key})'
	else:
		reply = f'{BASE_URL}/{key}'
	return reply


if __name__ == "__main__":
	port = int(os.environ.get("PORT", 5000))
	app.run(host="0.0.0.0", port=port)
