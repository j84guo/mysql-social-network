import argparse
import mysql.connector
import os
import social.api
import social.display
import sys

def parse_args():
    p = argparse.ArgumentParser(description='The command line social network.')
    p.add_argument('--host', help='MySQL host', default='localhost')
    p.add_argument('--port', help='MySQL port', default='3306')
    return p.parse_args()

current_screen_name = None

def print_intro():
    print('Welcome to the command line social network.')
    print('Type "help" for more information.')

def print_bad_command(tokens):
    bad = ' '.join(tokens)
    print('\n[ERROR] "{}" is not a valid command, try "help".'.format(bad))

def print_no_user():
    print('\n[ERROR] You need to select a user to use this command.')

def print_help():
    help ='''    COMMANDS:
    user create                                 
    user view [<screen_name>]
    user become <screen_name>
    user update
    user search
    user follow <screen_name>
    user unfollow <screen_name>
    user follows [<screen_name>]
    user followers [<screen_name>]
    user groups [<screen_name>]
    user topics
    
    topic search <name> [limit [offset]]
    topic tree <topic_id> [depth]
    topic create <name> [parent_topic_id>]
    topic follow <topic_id>
    topic unfollow <topic_id>
    topic followers <topic_id>
    
    post create <reply_to_post_id>
    post view <post_id>
    post search
    post tree <post_id>
    post react
    
    notifications
    notifications update
    
    group create
    group search
    group members <group_id>
    group view <group_id>
    group join <group_id>
    group leave <group_id>
    
    help'''
    print(help)

def prompt_block_text(prompt):
    print("(ctrl-D on a newline to submit)\n{}".format(prompt), end='')
    sys.stdout.flush()
    text = sys.stdin.read()
    if len(text) > 0 and text[-1] == '\n':
        text = text[0:-1]
    return text

def prompt_line_no_whitespace(prompt):
    line = input(prompt).lstrip().rstrip()
    if len(line.split()) > 1:
        raise ValueError('this value may not have whitespace')
    return line

def prompt_new_user_info():
    screen_name = prompt_line_no_whitespace('screen_name: ')
    user_info = prompt_update_user_info()
    user_info['screen_name'] = screen_name
    return user_info

def prompt_update_user_info():
    name = input('name: ')
    location = input('location: ')
    description = prompt_block_text('description:\n')
    return {
        'description': description,
        'location': location,
        'name': name
    }

def prompt_limit_offset(limit_prompt='limit: ', offset_prompt='offset: '):
    limit = input(limit_prompt)
    limit = 0 if limit == '' else abs(int(limit))
    offset = input(offset_prompt)
    offset = 0 if offset == '' else abs(int(offset))
    return limit, offset

def prompt_user_search_params():
    user_search_params = prompt_new_user_info()
    user_search_params['created_at_start'] = input('created_at_start: ')
    user_search_params['created_at_end'] = input('created_at_end: ')
    user_search_params['limit'], user_search_params['offset'] = prompt_limit_offset()
    return user_search_params

def run_user_create_command():
    user_info = prompt_new_user_info()
    user_links = prompt_block_text('links:\n').split()
    social.api.user_create(user_info, user_links)
    print('\n[INFO] Created with screen_name={}'.format(user_info['screen_name']))

def run_user_view_command(screen_name):
    user, user_urls = social.api.user_view(screen_name)
    if user is None:
        print('\n[WARNING] Could not find screen_name={}'.format(screen_name))
    else:
        social.display.view_user(user, user_urls)

def run_user_become_command(screen_name):
    user_info, _ = social.api.user_view(screen_name)
    if user_info is None:
        print('\n[ERROR] Could not find screen_name={}'.format(screen_name))
    else:
        global current_screen_name
        current_screen_name = screen_name

def run_user_update_command():
    user_info = prompt_update_user_info()
    user_info['screen_name'] = current_screen_name
    user_links = prompt_block_text('links:\n').split()
    social.api.user_update(user_info, user_links)

def run_user_search_command():
    user_search_params = prompt_user_search_params()
    users = social.api.user_search(user_search_params)
    social.display.summarize_users(users)

def run_user_follow_command(screen_name):
    social.api.user_follow(current_screen_name, screen_name)

def run_user_unfollow_command(screen_name):
    social.api.user_unfollow(current_screen_name, screen_name)

def run_user_follows_command(screen_name):
    followed_users = social.api.user_follows(screen_name)
    social.display.summarize_users(followed_users)

def run_user_followers_command(screen_name):
    followers = social.api.user_followers(screen_name)
    social.display.summarize_users(followers)

def run_user_groups_command(screen_name):
    groups = social.api.user_groups(screen_name)
    social.display.summarize_groups(groups)

def run_user_command(tokens):
    if tokens[1] == 'create':
        run_user_create_command()
    elif tokens[1] == 'view':
        if len(tokens) > 2:
            screen_name = tokens[2]
        elif current_screen_name is None:
            print_no_user()
            return
        else:
            screen_name = current_screen_name
        run_user_view_command(screen_name)
    elif tokens[1] == 'become' and len(tokens) > 2:
        run_user_become_command(tokens[2])
    elif tokens[1] == 'update':
        if current_screen_name is None:
            print_no_user()
        else:
            run_user_update_command()
    elif tokens[1] == 'search':
        run_user_search_command()
    elif tokens[1] == 'follow' and len(tokens) > 2:
        if current_screen_name is None:
            print_no_user()
        else:
            run_user_follow_command(tokens[2])
    elif tokens[1] == 'unfollow' and len(tokens) > 2:
        if current_screen_name is None:
            print_no_user()
        else:
            run_user_unfollow_command(tokens[2])
    elif tokens[1] == 'follows':
        if len(tokens) == 2:
            if current_screen_name is None:
                print_no_user()
                return
            screen_name = current_screen_name
        else:
            screen_name = tokens[2]
        run_user_follows_command(screen_name)
    elif tokens[1] == 'followers':
        if len(tokens) == 2:
            if current_screen_name is None:
                print_no_user()
                return
            screen_name = current_screen_name
        else:
            screen_name = tokens[2]
        run_user_followers_command(screen_name)
    elif tokens[1] == 'topics':
        if current_screen_name is None:
            print_no_user()
        else:
            screen_name = current_screen_name
            if len(tokens) > 2:
                screen_name = tokens[2]
            run_user_topics_command(screen_name)
    elif tokens[1] == 'groups':
        if len(tokens) == 1 and current_screen_name is None:
            print_no_user()
        else:
            screen_name = current_screen_name
            if len(tokens) > 2:
                screen_name = tokens[2]
            elif screen_name is None:
                print_no_user()
                return
            run_user_groups_command(screen_name)
    else:
        print_bad_command(tokens)

def run_topic_search_command(name, limit, offset):
    topics = social.api.topic_search(name, limit, offset)
    social.display.summarize_topics(topics)

def run_topic_tree_command(topic_id, depth):
    topics = social.api.topic_tree(topic_id, depth)
    social.display.topic_tree(topics)

def run_topic_create_command(name, parent_id):
    full_topic_info = social.api.topic_create(name, parent_id)
    print('\n[INFO] Created {} with topic_id={}'.format(full_topic_info['full_topic'], full_topic_info['topic_id']))

def run_topic_follow_command(topic_id):
    social.api.topic_follow(current_screen_name, topic_id)
    print('[INFO] Following topic_id={}'.format(topic_id))

def run_user_topics_command(screen_name):
    topics = social.api.user_topics(screen_name)
    social.display.summarize_topics(topics)

def run_topic_followers_command(topic_id):
    users = social.api.topic_followers(topic_id)
    social.display.summarize_users(users)

def run_topic_unfollow_command(topic_id):
    social.api.topic_unfollow(current_screen_name, topic_id)

def run_topic_command(tokens):
    if tokens[1] == 'search' and len(tokens) > 2:
        if '.' in tokens[2]:
            raise ValueError('topics may not contain periods')
        limit = 0 if len(tokens) < 4 else abs(int(tokens[3]))
        offset = 0 if len(tokens) < 5 else abs(int(tokens[4]))
        run_topic_search_command(tokens[2], limit, offset)
    elif tokens[1] == 'tree' and len(tokens) > 2:
        depth = 0 if len(tokens) < 4 else abs(int(tokens[3]))
        run_topic_tree_command(tokens[2], depth)
    elif tokens[1] == 'create' and len(tokens) > 2:
        parent_id = 1 if len(tokens) < 4 else int(tokens[3])
        if '.' in tokens[2]:
            raise ValueError('topics may not contain periods')
        run_topic_create_command(tokens[2], parent_id)
    elif tokens[1] == 'follow' and len(tokens) > 2:
        if current_screen_name is None:
            print_no_user()
        else:
            run_topic_follow_command(tokens[2])
    elif tokens[1] == 'followers' and len(tokens) > 2:
        run_topic_followers_command(tokens[2])
    elif tokens[1] == 'unfollow' and len(tokens) > 2:
        if current_screen_name is None:
            print_no_user()
        else:
            run_topic_unfollow_command(tokens[2])
    else:
        print_bad_command(tokens)

def prompt_topic_ids(prompt='topics:\n'):
    topic_ids = prompt_block_text(prompt).split()
    i = 0
    while i < len(topic_ids):
        topic_ids[i] = int(topic_ids[i])
        i += 1
    return topic_ids

def prompt_post_search_params():
    post_search_params = dict()
    post_search_params['screen_name'] = prompt_line_no_whitespace('screen_name: ')
    post_search_params['created_at_start'] = input('created_at_start: ')
    post_search_params['created_at_end'] = input('created_at_end: ')
    post_search_params['topic_ids'] = prompt_topic_ids()
    post_search_params['group_id'] = prompt_line_no_whitespace('group_id: ')
    post_search_params['limit'], post_search_params['offset'] = prompt_limit_offset()
    return post_search_params

def run_post_search_command():
    post_search_params = prompt_post_search_params()
    posts = social.api.post_search(post_search_params)
    social.display.summarize_posts(posts)

def run_post_create_command():
    parent_id_str = prompt_line_no_whitespace('parent_id: ')
    parent_id = None if parent_id_str == '' else int(parent_id_str)
    content = prompt_block_text('content: ')
    topic_ids = prompt_topic_ids()
    group_id = prompt_line_no_whitespace('group_id: ');
    post_id = social.api.post_create(parent_id, current_screen_name, content, topic_ids, group_id)
    print('[INFO] Created with post_id={}'.format(post_id))

def run_post_view_command(post_id):
    post, full_topics, reactions = social.api.post_view(current_screen_name, post_id)
    social.display.post_view(post, full_topics, reactions)

def run_post_tree_command(post_id, depth):
    posts = social.api.post_tree(post_id, depth)
    social.display.post_tree(posts)

def run_post_react_command(post_id):
    reaction_types = social.api.reaction_type_list()
    reaction_types_str = ', '.join([r['name'] for r in reaction_types])
    reaction = prompt_line_no_whitespace('Choose a reaction ({}): '.format(reaction_types_str))
    social.api.post_react(current_screen_name, post_id, reaction)

def run_post_command(tokens):
    if tokens[1] == 'search':
        run_post_search_command()
    elif tokens[1] == 'create':
        if current_screen_name is None:
            print_no_user()
        else:
            run_post_create_command()
    elif tokens[1] == 'view' and len(tokens) > 2:
        run_post_view_command(tokens[2])
    elif tokens[1] == 'tree' and len(tokens) > 2:
        depth = 0 if len(tokens) < 4 else abs(int(tokens[3]))
        run_post_tree_command(tokens[2], depth)
    elif tokens[1] == 'react' and len(tokens) > 2:
        if current_screen_name is None:
            print_no_user()
        else:
            run_post_react_command(tokens[2])
    else:
        print_bad_command(tokens)

def run_notifications_update_command(screen_name):
    social.api.notifications_update(screen_name)

def run_notifications_view_command():
    notifications = social.api.notifications(current_screen_name)
    social.display.notifications_view(notifications)

def run_notifications_command(tokens):
    if len(tokens) > 1 and tokens[1] == 'update':
        if current_screen_name is None:
            print_no_user()
        else:
            run_notifications_update_command(current_screen_name)
    elif len(tokens) == 1:
        run_notifications_view_command()
    else:
        print_bad_command(tokens)

def prompt_new_group_info():
    name = input('name: ')
    description = prompt_block_text('description: ')
    return {
        'name': name,
        'description': description
    }

def prompt_group_search_params():
    group_search_params = dict()
    group_search_params['name'] = input('name: ')
    group_search_params['description'] = prompt_block_text('description: ')
    group_search_params['created_at_start'] = input('created_at_start: ')
    group_search_params['created_at_end'] = input('created_at_end: ')
    group_search_params['limit'], group_search_params['offset'] = prompt_limit_offset()
    return group_search_params

def run_group_create_command(screen_name):
    group_info = prompt_new_group_info()
    group_id = social.api.group_create(screen_name, group_info)
    print('[INFO] Created with group_id={}'.format(group_id))

def run_group_search_command():
    group_search_params = prompt_group_search_params()
    groups = social.api.group_search(group_search_params)
    social.display.summarize_groups(groups)

def run_group_members_command(group_id):
    users = social.api.group_members(group_id)
    social.display.summarize_users(users)

def run_group_view_command(group_id):
    group = social.api.group_view(group_id)
    social.display.group_view(group)

def run_group_join_command(group_id):
    social.api.group_join(current_screen_name, group_id)

def run_group_leave_command(group_id):
    social.api.group_leave(current_screen_name, group_id)

def run_group_command(tokens):
    if tokens[1] == 'create':
        if current_screen_name is None:
            print_no_user()
        else:
            run_group_create_command(current_screen_name);
    elif tokens[1] == 'search':
        run_group_search_command()
    elif tokens[1] == 'members' and len(tokens) > 2:
        run_group_members_command(tokens[2])
    elif tokens[1] == 'view' and len(tokens) > 2:
        run_group_view_command(tokens[2])
    elif tokens[1] == 'join' and len(tokens) > 2:
        if current_screen_name is None:
            print_no_user()
        else:
            run_group_join_command(tokens[2])
    elif tokens[1] == 'leave' and len(tokens) > 2:
        if current_screen_name is None:
            print_no_user()
        else:
            run_group_leave_command(tokens[2])
    else:
        print_bad_command(tokens)

def run_command(tokens):
    if tokens[0] == 'user':
        if (len(tokens) == 1):
            print('screen_name={}'.format(current_screen_name))
        else:
            run_user_command(tokens)
    elif tokens[0] == 'topic' and len(tokens) > 1:
        run_topic_command(tokens)
    elif tokens[0] == 'post' and len(tokens) > 1:
        run_post_command(tokens)
    elif tokens[0] == 'notifications':
        if current_screen_name is None:
            print_no_user()
        else:
            run_notifications_command(tokens)
    elif tokens[0] == 'group' and len(tokens) > 1:
        run_group_command(tokens)
    else:
        print_bad_command(tokens)

def command_loop():
    print_intro()

    while True:
        tokens = input('\n>>> ').split()
        if len(tokens) == 0:
            continue
        if tokens[0] == 'help':
            print_help()
            continue

        try:
            run_command(tokens)
        except (mysql.connector.Error, ValueError) as e:
            print('\n[ERROR] {}'.format(e))
        except KeyboardInterrupt:
            continue

def main():
    if not sys.stdin.isatty():
        sys.exit('[ERROR] stdin must be a tty')

    args = parse_args()

    try:
        social.api.mysql_conn = mysql.connector.connect(
            user=os.getenv('MYSQL_SOCIAL_NETWORK_USER'),
            host=args.host,
            port=args.port,
            password=os.getenv('MYSQL_SOCIAL_NETWORK_USER_PASSWORD'),
            database='social')
    except mysql.connector.Error as e:
        sys.exit('[ERROR] {}'.format(e))

    try:
        command_loop()
    except (EOFError, KeyboardInterrupt):
        print('Bye')
    finally:
        social.api.mysql_conn.close()
