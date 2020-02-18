import io
from VideoLookup import getVideoList, extractInfos
import json
#import Telegram
from Telegram import lock
import time

subscriptions = {}


def process(lecture, user, subscribing):
    lock.acquire()
    if lecture in subscriptions:
        if subscribing == 1 and not user in subscriptions[lecture]["users"]:
            subscriptions[lecture]["users"].append(user)
        if subscribing == 0 and user in subscriptions[lecture]["users"]:
            subscriptions[lecture]["users"].remove(user)
    elif subscribing == 1:
        numberOfVideos = len(getVideoList(lecture))
        subscriptions[lecture] = {"count": numberOfVideos, "users": [user]}
    save()
    lock.release()


def load():
    lock.acquire()
    with open('subscriptions') as json_file:
        global subscriptions
        subscriptions = json.load(json_file)

    lock.release()


def save():
    lock.acquire()
    with open('subscriptions', 'w') as json_file:
        json.dump(subscriptions, json_file)
    lock.release()


def checkChanges():
    lock.acquire()
    changes = []
    global subscriptions

    sbscpy = subscriptions
    for lecture in sbscpy:
        videos = getVideoList(lecture)
        updatedCount = len(videos)
        if sbscpy[lecture]["count"] < updatedCount:
            sbscpy[lecture]["count"] = updatedCount

            changes.append([sbscpy[lecture]["users"], extractInfos(videos[0], lecture)])

    save()
    lock.release()
    return changes
