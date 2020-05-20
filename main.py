from dotenv import load_dotenv
from google.cloud import firestore
from instabot import Bot
from urllib import request

import praw
import random
import os

load_dotenv()

# Setup clients
reddit = praw.Reddit(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    password=os.getenv("REDDIT_PASSWORD"),
    user_agent=os.getenv("USER_AGENT"),
    username=os.getenv("REDDIT_USERNAME")
)

subreddit = reddit.subreddit('memes')

db = firestore.Client()


def get_post_and_upload(req):
    caption_docs = db.collection(u'captions').stream()
    hashtag_docs = db.collection(u'hashtags').stream()

    json_filename = "{}_uuid_and_cookie.json".format(os.getenv("INSTAGRAM_USERNAME"))
    json_filename_path = os.path.join("/tmp", json_filename)
    uuid_and_cookie_json = db.collection(u'json').document(u'uuid_and_cookie_json')
    json_file_write = open(json_filename_path, 'w')
    json_value = uuid_and_cookie_json.get().to_dict()["value"]
    json_file_write.write(json_value)
    json_file_write.close()

    captions = []
    for doc in caption_docs:
        captions.append(doc.to_dict()["text"])

    caption = random.choice(captions)
    for doc in hashtag_docs:
        caption += " {}".format(doc.to_dict()["text"])

    instagram_bot = Bot(base_path="/tmp")
    instagram_bot.login(username=os.getenv("INSTAGRAM_USERNAME"), password=os.getenv("INSTAGRAM_PASSWORD"))

    for submission in subreddit.hot(limit=50):
        get_ref = db.collection(u'posts').document(submission.id)
        doc = get_ref.get()
        print(u'Document data: {}'.format(doc.to_dict()))
        print(submission.title)  # Output: the submission's title
        print(submission.score)  # Output: the submission's score
        print(submission.id)  # Output: the submission's ID
        print(submission.url)  # Output: the URL

        if not doc.to_dict():
            try:
                f = open('/tmp/img.jpg', 'wb')
                f.write(request.urlopen(submission.url).read())
                f.close()
                print("63")
                set_ref = db.collection(u'posts').document(submission.id)
                set_ref.set({
                    u'title': submission.title,
                    u'url': submission.url
                })

                print("70")
                result = instagram_bot.upload_photo('/tmp/img.jpg', caption)
                print(result)
                if not result:
                    continue
                json_file_read = open(json_filename_path, 'r')
                data = json_file_read.read()
                json_file_read.close()
                uuid_and_cookie_json.update({u'value': data})
                return "Success"
            except Exception as e:
                print("Could not open image or upload photo, trying next post")
                print(e)

    return "Could not upload picture"
