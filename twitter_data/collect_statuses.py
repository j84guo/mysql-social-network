#!/usr/bin/python3
#
# Description:
# Parse a txt file which contains a tuple '<followerID> <followedID>' on each
# line, i.e. a list of edges in a user graph. Fetch recent tweets for each
# distinct user and save them to a json file.
#
# Tokens:
# Twitter's API require clients to authenticate via tokens. This script assumes
# they are stored in environment variables.
#
# Data:
# We need 2 important types of data, the users' followers/follows and the
# users' posts. Twitter's API has follows and timeline endpoints. The follows
# endpoint is strictly rate-limited, so an existing user graph is obtained from
# https://snap.stanford.edu/data/twitter_combined.txt.gz. Tweets are then
# collected from the timeline endpoint, which is much more generous with its
# rate limit.
#
# Usage:
# python3 collect_statuses.py --help

import argparse
import os
import twitter

def parse_args():
    p = argparse.ArgumentParser(description='Collect Twitter statuses from user_id\'s.')
    p.add_argument('--follows_file', help='txt file containing a list of edges in a user graph', required=True)
    p.add_argument('--statuses_file', help='json file for retrieved statuses', default='twitter_statuses.json')
    return p.parse_args()

'''
Build a set of distinct user_id's from the input file.
'''
def get_user_ids(follows_file):
    user_ids = set()
    with open(follows_file) as f:
        while True:
            line = f.readline()
            if line == '':
                break
            edge = line.split()
            user_ids.add(edge[0])
            user_ids.add(edge[1])
        return user_ids

'''
Fetch a timeline (of up to max_count statuses) for each user_id and yield the
timelines one by one. Certain users are private, in which case the twitter
client throws an exception; we simply skip such users.

Calling this function does not fetch any timelines! Rather, a Python3 generator
will be returned which can be iterated through; each iteration over the
generator fetches one timeline.
'''
def download_timelines(twitter_client, user_ids, max_count=200):
    num_users_tried = 0
    for user_id in user_ids:
        num_users_tried += 1
        try:
            timeline = twitter_client.GetUserTimeline(user_id=user_id, exclude_replies=False, include_rts=False, count=max_count)
            print('[{}/{}] Retrieved {} statuses for user_id={}'.format(num_users_tried, len(user_ids), len(timeline), user_id))
            yield timeline
        except twitter.error.TwitterError as e:
            print('[{}/{}] Error retrieving user_id={} {}'.format(num_users_tried, len(user_ids), user_id, repr(e)))

'''
Write retrieved timelines to a json file as a single list of status objects.

Why are we not simply using json.dump? Because that method buffers all json
data in memory before writing to file, but for a large number of timelines
this will likely cause a MemoryError (e.g. the limit on ecetesla3 was ~30000).

Instead, we write each timeline after retrieving it. The timelines object is
expected to be a generator which requests one timeline per iteration.
'''
def save_timelines(timelines, statuses_file):
    with open(statuses_file, 'w') as f:
        f.write('[')
        is_first_status = True

        for timeline in timelines: 
            for status in timeline:
                if is_first_status:
                    is_first_status = False
                else:
                    f.write(',')
                f.write(status.AsJsonString())

        f.write(']')

if __name__ == '__main__':
    args = parse_args()
    user_ids = get_user_ids(args.follows_file)
    
    twitter_client = twitter.Api(
        consumer_key=os.getenv('TWITTER_CONSUMER_TOKEN_KEY'),
        consumer_secret=os.getenv('TWITTER_CONSUMER_TOKEN_SECRET'),
        access_token_key=os.getenv('TWITTER_ACCESS_TOKEN_KEY'),
        access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
        sleep_on_rate_limit=True)

    timelines = download_timelines(twitter_client, user_ids)
    save_timelines(timelines, args.statuses_file)
