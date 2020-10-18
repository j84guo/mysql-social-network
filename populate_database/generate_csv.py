#!/usr/bin/python3

import argparse
import datetime
import ijson

def parse_args():
    p = argparse.ArgumentParser(description='Generate MySQL-loadable CSV files from follow relationships and statuses.')
    p.add_argument('--follows_file', help='txt file containing a list of edges in a user graph', required=True)
    p.add_argument('--statuses_file', help='json file for retrieved statuses', required=True)
    p.add_argument('--stats', help='print dataset statistics and exit', action='store_true')
    return p.parse_args()

def get_statuses(statuses_file):
    with open(statuses_file) as f:
        for status in ijson.items(f, 'item'):
            yield status

def to_mysql_datetime(ts):
    dt = datetime.datetime.strptime(ts, '%a %b %d %H:%M:%S %z %Y')
    dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def escape_for_mysql_csv(v):
    return v.replace('\\', '\\\\').replace('\n', '\\n').replace(',', '\\,')

# Tables:
# * User
# * UserUrl
# * FollowUser
# * Post
# * Topic
# * PostTopic
#
# (optionally populate)
# * AuthorLastRead
# * FollowTopic
# * TopicLastRead
#
# Notes:
# 1. Convert timestamps to UTC and write in MySQL format
# 2. Escape '\n' and ',' characters in strings before writing.
class TableCSV:
    def __init__(self, file_name):
        self._file_name = file_name
        self._file = open(self._file_name, 'w')

    def __enter__(self):
        return self

    def __exit__(self, c, e, t):
        self._file.close()

    def write(self, values):
        first_value = True
        for v in values:
            if first_value:
                first_value = False
            else:
                self._file.write(',')
            if v is None:
                v = '\\N'
            elif isinstance(v, str):
                v = escape_for_mysql_csv(v)
            self._file.write(str(v))
        self._file.write('\n')

def process_user(user_ids, user_csv, user_url_csv, user):
    if user['id'] in user_ids:
        return
    user_ids.add(user['id'])

    # User
    created_at = to_mysql_datetime(user['created_at'])
    location = user.get('location', None)
    description = user.get('description', None)
    name = user.get('name', None)
    user_csv.write([
        created_at,
        description,
        user['id'],
        location,
        name,
        user['screen_name']
    ])

    # UserUrl
    if 'url' in user:
        user_url_csv.write([
            user['id'],
            user['url'],
            1
        ])

def process_post(post_csv, status):
    if 'text' not in status:
        return

    # Post
    created_at = to_mysql_datetime(status['created_at'])
    parent_id = status.get('in_reply_to_status_id', None)

    post_csv.write([
        status['user']['id'],
        created_at,
        status['id'],
        status['text'],
        parent_id
    ])

def process_topics(next_topic_id, topics, topic_csv, post_topic_csv, status):
    # De-duplicate topics
    post_topics = set()
    for hashtag in status['hashtags']:
        post_topics.add(hashtag['text'])

    for topic in post_topics:
        if topic not in topics:
            # Topic
            topic_csv.write([next_topic_id, topic, 1])
            topics[topic] = next_topic_id
            next_topic_id += 1
        # PostTopic
        post_topic_csv.write([status['id'], topics[topic]])

    return next_topic_id

def process_statuses(statuses):
    with TableCSV('User.csv') as user_csv, TableCSV("UserUrl.csv") as user_url_csv, TableCSV(
            'Post.csv') as post_csv, TableCSV('Topic.csv') as topic_csv, TableCSV(
            'PostTopic.csv') as post_topic_csv:
        user_ids = set()
        topics = dict()
        # Start at 2 because 1 is a special row for indicating "no parent".
        next_topic_id = 2

        for status in statuses:
            try:
                process_user(user_ids, user_csv, user_url_csv, status['user'])
                process_post(post_csv, status)
                next_topic_id = process_topics(next_topic_id, topics, topic_csv, post_topic_csv, status)
            except Exception as e:
                print('Failed at status: {}'.format(status))
                raise e

def process_follows(follows_file):
    with open(follows_file) as follows_txt, TableCSV('FollowUser.csv') as follow_user_csv:
        user_graph = dict()
        while True:
            line = follows_txt.readline()
            if line == '':
                break
            edge = line.split()
            if edge[0] not in user_graph:
                user_graph[edge[0]] = set()
            if edge[1] not in user_graph[edge[0]]:
                user_graph[edge[0]].add(edge[1])
                follow_user_csv.write([edge[0], edge[1]])

def print_statistics(statuses):
    users = dict()
    numPosts = 0
    numReplies = 0
    hashtags = set()
    numPostsWithHashTags = 0

    for status in statuses:
        user = status['user']
        users[user['id']] = user
        numPosts += 1
        if 'in_reply_to_status_id' in status:
            numReplies += 1
        if 'hashtags' in status and len(status['hashtags']) > 0:
            for hashtag in status['hashtags']:
                hashtags.add(hashtag['text'])
            numPostsWithHashTags += 1
        if len(status['hashtags']) > 0:
            print(status['hashtags'])

    print('numUsers={}'.format(len(users)))
    print('numPosts={}'.format(numPosts))
    print('numReplies={}'.format(numReplies))
    print('numHashtags={}'.format(len(hashtags)))
    print('numPostsWithHashTags={}'.format(numPostsWithHashTags))

if __name__ == '__main__':
    args = parse_args()
    statuses = get_statuses(args.statuses_file)

    if args.stats:
        print_statistics(statuses)
    else:
        process_statuses(statuses)
        process_follows(args.follows_file)
