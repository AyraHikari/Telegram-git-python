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
	if not data:
		return "Guide: contact our API bot, then type /help in group, copy URL and paste to your git webhook."
	# If webhook was set
	if data.get('hook'):
		response = post_tg(groupid, "✅ Successfully set webhook for <a href='{}'>{}</a> by <a href='{}'>{}</a>!".format(data['repository']['html_url'], data['repository']['name'], data['sender']['html_url'], data['sender']['login']), "html")
		return response

	# If push
	if data.get('commits'):
		commits_text = ""
		rng = len(data['commits'])
		if rng > 10:
			rng = 10
		for x in range(rng):
			commit = data['commits'][x]
			if len(escape(commit['message'])) > 300:
				commit_msg = escape(commit['message']).split("\n")[0]
			else:
				commit_msg = escape(commit['message'])
			commits_text += f"<code>{commit_msg}</code>\n<a href='{commit['url']}'>{commit['id'][:7]}</a> - {commit['author']['name']} {escape('<')}{commit['author']['email']}{escape('>')}\n\n"
			if len(commits_text) > 1000:
				text = """🔨 <b>{}</b> - New {} commits ({})

{}
""".format(escape(data['repository']['name']), len(data['commits']), escape(data['ref'].split("/")[-1]), commits_text)
				response = post_tg(groupid, text, "html")
				commits_text = ""
		if not commits_text:
			return jsonify({"ok": True, "text": "Commits text is none"})
		text = """🔨 <b>{}</b> - New {} commits ({})

{}
""".format(escape(data['repository']['name']), len(data['commits']), escape(data['ref'].split("/")[-1]), commits_text)
		if len(data['commits']) > 10:
			text += "\n\n<i>And {} other commits</i>".format(len(data['commits'])-10)
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
			text = """💬 There is a new pull request for <b>{}</b> ({})

<code>{}</code>

<a href='{}'>Pull request #{}</a>
""".format(escape(data['repository']['name']), data['pull_request']['state'], escape(data['comment']['body']), data['comment']['html_url'], data['issue']['number'])
			response = post_tg(groupid, text, "html")
			return response
		text = """👨‍🔧 New {} pull request for <b>{}</b>

<b>{}</b> ({})
<code>{}</code>

<a href='{}'>Pull request #{}</a>
""".format(data['action'], escape(data['repository']['name']), escape(data['pull_request']['title']), data['pull_request']['state'], escape(data['pull_request']['body']), data['pull_request']['html_url'], data['pull_request']['number'])
		response = post_tg(groupid, text, "html")
		return response

	# If fork trigger
	if data.get('forkee'):
		response = post_tg(groupid, "🧾 <a href='{}'>{}</a> has forked <a href='{}'>{}</a>!\nTotal forks now are {}".format(data['sender']['html_url'], data['sender']['login'], data['repository']['html_url'], data['repository']['name'], data['repository']['forks_count']), "html")
		return response

	# If there is an action
	if data.get('action'):

		# If release tag
		if data.get('action') == "published" and data.get('release'):
			text = "👨‍💻 <a href='{}'>{}</a> has {} <a href='{}'>{}</a>!".format(data['sender']['html_url'], data['sender']['login'], data['action'], data['repository']['html_url'], data['repository']['name'])
			text += "\n\n<b>{}</b> ({})\n<code>{}</code>\n\n<a href='{}'>Download tar</a> | <a href='{}'>Download zip</a>".format(data['release']['name'], data['release']['tag_name'], data['release']['body'], data['release']['tarball_url'], data['release']['zipball_url'])
			response = post_tg(groupid, text, "html")
			return response

		# If release tag was edited
		if data.get('action') == "edited" and data.get('release'):
			text = "👨‍💻 <a href='{}'>{}</a> has {} <a href='{}'>{}</a>!".format(data['sender']['html_url'], data['sender']['login'], data['action'], data['repository']['html_url'], data['repository']['name'])
			text += "\n\n<b>{}</b> ({})\n<code>{}</code>\n\n<a href='{}'>Download tar</a> | <a href='{}'>Download zip</a>".format(data['release']['name'], data['release']['tag_name'], data['release']['body'], data['release']['tarball_url'], data['release']['zipball_url'])
			response = post_tg(groupid, text, "html")
			return response

		# If repo was started
		if data.get('action') == "started":
			text = "🌟 <a href='{}'>{}</a> gave a star to <a href='{}'>{}</a>!\nTotal stars are now {}".format(data['sender']['html_url'], data['sender']['login'], data['repository']['html_url'], data['repository']['name'], data['repository']['stargazers_count'])
			response = post_tg(groupid, text, "html")
			return response

		# If repo was created, pass that
		if data.get('action') == "created":
			return jsonify({"ok": True, "text": "Pass trigger for created"})

		response = post_tg(groupid, "👨‍💻 <a href='{}'>{}</a> has {} <a href='{}'>{}</a>!".format(data['sender']['html_url'], data['sender']['login'], data['action'], data['repository']['html_url'], data['repository']['name']), "html")
		return response

	# If there was ref_type
	if data.get('ref_type'):
		response = post_tg(groupid, "👨‍💻 A new {} on <a href='{}'>{}</a> was created by <a href='{}'>{}</a>!".format(data['ref_type'], data['repository']['html_url'], data['repository']['name'], data['sender']['html_url'], data['sender']['login']), "html")
		return response

	# If branch was created
	if data.get('created'):
		response = post_tg(groupid, "👨‍💻 Branch {} ({}) on <a href='{}'>{}</a> was created by <a href='{}'>{}</a>!".format(data['ref'].split("/")[-1], data['ref'].split("/")[-2], data['repository']['html_url'], data['repository']['name'], data['sender']['html_url'], data['sender']['login']), "html")
		return response

	# If branch was deleted
	if data.get('deleted'):
		response = post_tg(groupid, "👨‍💻 Branch {} ({}) on <a href='{}'>{}</a> was deleted by <a href='{}'>{}</a>!".format(data['ref'].split("/")[-1], data['ref'].split("/")[-2], data['repository']['html_url'], data['repository']['name'], data['sender']['html_url'], data['sender']['login']), "html")
		return response

	# If branch was forced
	if data.get('forced'):
		response = post_tg(groupid, "👨‍💻 Branch {} ({}) on <a href='{}'>{}</a> was forced by <a href='{}'>{}</a>!".format(data['ref'].split("/")[-1], data['ref'].split("/")[-2], data['repository']['html_url'], data['repository']['name'], data['sender']['html_url'], data['sender']['login']), "html")
		return response

	# If wiki pages were changed
	if data.get('pages'):
		text = "👨‍💻 <a href='{}'>{}</a> wiki pages were updated by <a href='{}'>{}</a>!\n\n".format(data['repository']['html_url'], data['repository']['name'], data['sender']['html_url'], data['sender']['login'])
		for x in data['pages']:
			summary = ""
			if x['summary']:
				summary = f"<code>{x['summary']}</code>\n"
			text += f"📖 <b>{escape(x['title'])}</b> ({x['action']})\n{summary}<a href='{x['html_url']}'>{x['page_name']}</a> - <code>{x['sha'][:7]}</code>"
			if len(data['pages']) >= 2:
				text += "\n—————————————————————\n"
			response = post_tg(groupid, text, "html")
		return response

	# If repo trigger proccess building on ci
	if data.get('context'):
		if data.get('state') == "pending":
			emo = "⏳"
		elif data.get('state') == "success":
			emo = "✅"
		elif data.get('state') == "failure":
			emo = "❎"
		else:
			emo = "💡"
		response = post_tg(groupid, f"{emo} <a href='{data['target_url']}'>{data['description']}</a> on <a href='{data['repository']['html_url']}'>{data['repository']['name']}</a> by <a href='{data['sender']['html_url']}'>{data['sender']['login']}</a>!\nLatest commit:\n<a href='{data['commit']['commit']['url']}'>{escape(data['commit']['commit']['message'])}</a>", "html")
		return response

	# When there is no trigger known, send this
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
