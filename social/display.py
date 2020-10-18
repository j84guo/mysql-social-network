import tabulate

def limit_width(s, max_width=32):
    if s is None:
        return s
    if len(s) > max_width:
        s = s[0:max_width] + '...'
    return s

def summarize_users(users):
    output = [{
        'screen_name': d['screen_name'],
        'location': limit_width(d['location']),
        'description': limit_width(d['description']),
        'created_at': d['created_at']
    } for d in users]
    print(tabulate.tabulate(output, headers='keys', tablefmt='pretty'))

def view_user(user, user_urls):
    print(tabulate.tabulate([{
        'screen_name': user['screen_name'],
        'location': user['location'],
        'description': user['description'],
        'created_at': user['created_at']
    }], headers='keys', tablefmt='pretty'))

    user_urls_output = [{
        'url': d['url']
    } for d in user_urls]
    print(tabulate.tabulate(user_urls_output, headers='keys', tablefmt='pretty'))

def summarize_groups(groups):
    output = [{
        'group_id': d['group_id'],
        'name': d['name'],
        'description': d['description'],
        'created_at': d['created_at']
    } for d in groups]
    print(tabulate.tabulate(output, headers='keys', tablefmt='pretty'))

def notifications_view(notifications):
    summarize_posts(notifications)

def summarize_posts(posts):
    output = [{
        'screen_name': d['screen_name'],
        'content': limit_width(d['content']),
        'created_at': d['created_at'],
        'post_id': d['post_id']
    } for d in posts]
    print(tabulate.tabulate(output, headers='keys', tablefmt='pretty'))

def summarize_topics(topics):
    output = [{
        'root_id': d['root_id'],
        'topic_id': d['topic_id'],
        'full_topic': d['full_topic']
    } for d in topics]
    print(tabulate.tabulate(output, headers='keys', tablefmt='pretty'))

def build_tree_layers(nodes):
    if nodes[0]['depth'] != 1:
        raise ValueError('unexpected depth={}'.format(nodes))

    depth = 0
    layers = []
    for topic in nodes:
        if topic['depth'] == depth + 1:
            layers.append([])
            depth += 1
        layers[-1].append(topic)

    return layers

def pre_order_traversal(layers, is_parent, i, j, print_node):
    print_node(layers[i][j])

    if i == len(layers) - 1:
        return

    for c in range(len(layers[i + 1])):
        if is_parent(layers[i][j], layers[i + 1][c]):
            pre_order_traversal(layers, is_parent, i + 1, c, print_node)

def print_topic_node(topic):
    print((topic['depth'] - 1) * '   ', end='')
    print('|- ', end='')
    print('{} ({})'.format(topic['name'], topic['topic_id']))

def topic_tree(topics):
    if len(topics) == 0:
        return

    layers = build_tree_layers(topics)
    pre_order_traversal(
        layers,
        lambda t1, t2: t1['topic_id'] == t2['parent_id'],
        0,
        0,
        print_topic_node
    )

def print_post_node(post):
    print((post['depth'] - 1) * '   ', end='')
    print('|- ', end='')
    print('(post_id={} screen_name={}, content={}, created_at={})'.format(
        post['post_id'],
        post['screen_name'],
        limit_width(post['content'], max_width=128),
        limit_width(str(post['created_at']), max_width=10)
    ))

def post_tree(posts):
    if len(posts) == 0:
        return

    layers = build_tree_layers(posts)
    pre_order_traversal(
        layers,
        lambda t1, t2: t1['post_id'] == t2['parent_id'],
        0,
        0,
        print_post_node
    )

def summarize_reactions(reactions):
    print(tabulate.tabulate(reactions, headers='keys', tablefmt='pretty'))

def post_view(post, full_topics, reactions):
    print(
'''
created_at: {}
screen_name: {}
content: {}
'''.format(
        post['created_at'],
        post['screen_name'],
        post['content']
    ))
    summarize_reactions(reactions)
    summarize_topics(full_topics)

def group_view(group):
    print(
'''
group_id: {}
name: {}
description: {}
created_at: {}'''.format(group['group_id'], group['name'], group['description'], group['created_at']))
