mysql_conn = None

def transaction(func):
    def transaction_func(*args, **kwargs):
        mysql_conn.start_transaction()
        try:
            res = func(*args, **kwargs)
        except Exception as e:
            mysql_conn.rollback()
            raise e
        mysql_conn.commit()
        return res
    return transaction_func

def mysql_query_all(sql, args, dictionary=True):
    cursor = mysql_conn.cursor(dictionary=dictionary)
    try:
        cursor.execute(sql, args)
        return cursor.fetchall()
    finally:
        cursor.close()

def mysql_query_one(sql, args, dictionary=True, buffered=True):
    cursor = mysql_conn.cursor(dictionary=dictionary, buffered=buffered)
    try:
        cursor.execute(sql, args)
        return cursor.fetchone()
    finally:
        cursor.close()

def mysql_insert_id(sql, args):
    cursor = mysql_conn.cursor()
    try:
        cursor.execute(sql, args)
        return cursor.lastrowid
    finally:
        cursor.close()

def mysql_statement_no_rows(sql, args):
    cursor = mysql_conn.cursor()
    try:
        cursor.execute(sql, args)
    finally:
        cursor.close()

@transaction
def user_create(user_info, user_links):
    sql = '''
    insert into User(created_at, description, location, name, screen_name, last_notified_at) values(
        utc_timestamp(),
        %(description)s,
        %(location)s,
        %(name)s,
        %(screen_name)s,
        utc_timestamp()
    );
    '''
    user_id = mysql_insert_id(sql, user_info)
    insert_user_links(user_id, user_links)

def insert_user_links(user_id, user_links):
    sql = '''
    insert into UserUrl(user_id, url, display_order) values(%s, %s, %s);
    '''
    i = 1
    for link in user_links:
        mysql_insert_id(sql, (user_id, link, i))
        i += 1

def delete_user_links(screen_name):
    sql = '''
    delete from UserUrl where user_id = (select user_id from User where screen_name = %s);
    '''
    mysql_statement_no_rows(sql, (screen_name,))

@transaction
def user_view(screen_name):
    user_info = get_user(screen_name)

    user_url_sql ='''
    select * from UserUrl where user_id = (select user_id from User where screen_name=%s) order by display_order;
    '''
    user_links = mysql_query_all(user_url_sql, (screen_name,))

    return user_info, user_links

def get_user(screen_name):
    user_sql = '''
        select * from User where screen_name = %s;
        '''
    return mysql_query_one(user_sql, (screen_name,))

@transaction
def user_update(user_info, user_links):
    update_sql = '''
    update User
    set description = %(description)s, location = %(location)s, name = %(name)s
    where screen_name = %(screen_name)s;
    '''
    mysql_statement_no_rows(update_sql, user_info)
    delete_user_links(user_info['screen_name'])

    user_id_sql = '''
    select user_id from User where screen_name = %s;
    '''
    user_id = mysql_query_one(user_id_sql, (user_info['screen_name'],))['user_id']
    insert_user_links(user_id, user_links)

@transaction
def user_search(user_search_params):
    screen_name = '%{}%'.format(user_search_params['screen_name'])
    name = '%{}%'.format(user_search_params['name'])
    description = '%{}%'.format(user_search_params['description'])
    location = '%{}%'.format(user_search_params['location'])

    created_at_start = ''
    if user_search_params['created_at_start']:
        created_at_start = 'and created_at >= "{}"'.format(user_search_params['created_at_start'])

    created_at_end = ''
    if user_search_params['created_at_end']:
        created_at_end = 'and created_at <= "{}"'.format(user_search_params['created_at_end'])

    limit_clause = ''
    if user_search_params['limit'] > 0:
        limit_clause = 'limit {}'.format(user_search_params['limit'])

    offset_clause = ''
    if user_search_params['offset'] > 0:
        offset_clause = 'offset {}'.format(user_search_params['offset'])

    sql = '''
    select * from User
    where screen_name like %s and name like %s and description like %s and location like %s
    {}
    {}
    {}
    {};
    '''.format(created_at_start, created_at_end, limit_clause, offset_clause)
    return mysql_query_all(sql, (screen_name, name, description, location))

@transaction
def user_follow(current_screen_name, screen_name):
    sql = '''
    insert into FollowUser(follower_id, followee_id) values(
        (select user_id from User where screen_name=%s), 
        (select user_id from User where screen_name=%s)
    );
    '''
    mysql_statement_no_rows(sql, (current_screen_name, screen_name))

@transaction
def user_unfollow(current_screen_name, screen_name):
    sql = '''
    delete from FollowUser where
    follower_id = (select user_id from User where screen_name=%s) and
    followee_id = (select user_id from User where screen_name=%s)
    '''
    mysql_statement_no_rows(sql, (current_screen_name, screen_name))

@transaction
def user_follows(screen_name):
    return get_user_follows(screen_name)

def get_user_follows(screen_name):
    follow_user_sql = '''
        select * from User where user_id in (select followee_id from FollowUser where follower_id = 
        (select user_id from User where screen_name=%s));
        '''
    return mysql_query_all(follow_user_sql, (screen_name,))

@transaction
def user_followers(screen_name):
    sql = '''
    select * from User where user_id in (select follower_id from FollowUser where followee_id =
    (select user_id from User where screen_name=%s));
    '''
    return mysql_query_all(sql, (screen_name,))

@transaction
def topic_search(name, limit, offset):
    name = '%{}%'.format(name)

    limit_clause = ''
    if limit > 0:
        limit_clause = 'limit {}'.format(limit)

    offset_clause = ''
    if offset > 0:
        offset_clause = 'offset {}'.format(offset)

    sql = '''
    with recursive TopicAncestor(ancestor_id, topic_id, ancestor_parent_id, full_topic) as(
        select topic_id, topic_id, parent_id, convert(name, char(65535)) from Topic
        where name like %s
        union
        select Topic.topic_id, TopicAncestor.topic_id, Topic.parent_id, concat(name, '.', full_topic) from Topic
        inner join TopicAncestor on TopicAncestor.ancestor_parent_id = Topic.topic_id
        where Topic.topic_id > 1
    ) select ancestor_id as root_id, topic_id, full_topic from TopicAncestor where ancestor_parent_id = 1 {} {};
    '''.format(limit_clause, offset_clause)
    return mysql_query_all(sql, (name,))

@transaction
def topic_tree(topic_id, depth):
    depth_clause = ''
    if depth > 0:
        depth_clause = 'where FullTopic.depth < {}'.format(depth)

    sql = '''
    with recursive FullTopic(root_id, topic_id, name, parent_id, depth, full_topic) as(
        select topic_id, topic_id, name, parent_id, 1, convert(name, char(65535)) from Topic where topic_id = %s
        union
        select FullTopic.root_id, Topic.topic_id, Topic.name, Topic.parent_id, FullTopic.depth + 1, concat(full_topic, '.', Topic.name) from Topic
        inner join FullTopic on FullTopic.topic_id = Topic.parent_id
        {}
    )
    select * from FullTopic;
    '''.format(depth_clause)
    return mysql_query_all(sql, (topic_id,))

@transaction
def topic_create(name, parent_id):
    insert_sql = '''
    insert into Topic(name, parent_id) values(%s, %s);
    '''
    topic_id = mysql_insert_id(insert_sql, (name, parent_id))

    select_sql = '''
    with recursive TopicAncestor(ancestor_id, topic_id, ancestor_parent_id, full_topic) as(
        select topic_id, topic_id, parent_id, convert(name, char(65535)) from Topic
        where topic_id = %s
        union
        select Topic.topic_id, TopicAncestor.topic_id, Topic.parent_id, concat(name, '.', full_topic) from Topic
        inner join TopicAncestor on TopicAncestor.ancestor_parent_id = Topic.topic_id
        where Topic.topic_id > 1
    ) select * from TopicAncestor where ancestor_parent_id = 1;
    '''
    return mysql_query_one(select_sql, (topic_id,))

@transaction
def topic_follow(current_screen_name, topic_id):
    sql = '''
    insert into FollowTopic(user_id, topic_id) values (
        (select user_id from User where screen_name = %s),
        %s
    );
    '''
    mysql_statement_no_rows(sql, (current_screen_name, topic_id))

@transaction
def user_topics(screen_name):
    return get_user_topics(screen_name)

def get_user_topics(screen_name):
    user_topics_sql = '''
    with recursive TopicAncestor(ancestor_id, topic_id, ancestor_parent_id, full_topic) as(
        select topic_id, topic_id, parent_id, convert(name, char(65535)) from Topic
        where topic_id in (select topic_id from FollowTopic where user_id = (select user_id from User where screen_name = %s))
        union
        select Topic.topic_id, TopicAncestor.topic_id, Topic.parent_id, concat(name, '.', full_topic) from Topic
        inner join TopicAncestor on TopicAncestor.ancestor_parent_id = Topic.topic_id
        where Topic.topic_id > 1
    ) select ancestor_id as root_id, topic_id, full_topic from TopicAncestor where ancestor_parent_id = 1;
    '''
    return mysql_query_all(user_topics_sql, (screen_name,))

@transaction
def topic_followers(topic_id):
    sql = '''
    select * from User where exists (select * from FollowTopic where FollowTopic.topic_id = %s and FollowTopic.user_id = User.user_id);
    '''
    return mysql_query_all(sql, (topic_id,))

@transaction
def topic_unfollow(current_screen_name, topic_id):
    sql = '''
    delete from FollowTopic where user_id = (select user_id from User where screen_name = %s) and topic_id = %s;
    '''
    mysql_statement_no_rows(sql, (current_screen_name, topic_id))

@transaction
def post_search(post_search_params):
    screen_name = post_search_params['screen_name']
    if screen_name == '':
        screen_name = '%'

    created_at_start = ''
    if post_search_params['created_at_start']:
        created_at_start = 'and created_at >= "{}"'.format(post_search_params['created_at_start'])

    created_at_end = ''
    if post_search_params['created_at_end']:
        created_at_end = 'and created_at <= "{}"'.format(post_search_params['created_at_end'])

    topic_clause = ''
    if len(post_search_params['topic_ids']) > 0:
        topic_clause = '''
        and exists (
            select * from PostTopic where PostTopic.post_id = Post.post_id and PostTopic.topic_id
            in ({})
        )
        '''.format(','.join([str(topic_id) for topic_id in post_search_params['topic_ids']]))

    group_clause = ''
    if post_search_params['group_id'] != '':
        group_clause = 'and group_id={}'.format(int(post_search_params['group_id']))

    limit_clause = ''
    if post_search_params['limit'] > 0:
        limit_clause = 'limit {}'.format(post_search_params['limit'])

    offset_clause = ''
    if post_search_params['offset'] > 0:
        offset_clause = 'offset {}'.format(post_search_params['offset'])

    sql = '''
    select
    Post.post_id,
    (select screen_name from User where User.user_id = Post.user_id) as screen_name,
    Post.user_id,
    Post.created_at,
    Post.content,
    Post.parent_id 
    from Post where
    user_id in (select user_id from User where screen_name like %s)
    {}
    {}
    {}
    {}
    {}
    {}
    '''.format(created_at_start, created_at_end, topic_clause, group_clause, limit_clause, offset_clause)
    return mysql_query_all(sql, (screen_name,))

def is_group_valid(current_screen_name, group_id):
    group_sql = '''
    select * from `Group` where group_id = %s;
    '''
    if mysql_query_one(group_sql, (group_id,)) is None:
        return False

    user_group_sql = '''
    select * from UserGroup where 
    user_id = (select user_id from User where screen_name = %s) and
    group_id = %s;
    '''
    if mysql_query_one(user_group_sql, (current_screen_name, group_id)) is None:
        return False

    return True

@transaction
def post_create(parent_id, current_screen_name, content, topic_ids, group_id):
    if group_id == '':
        group_id = None
    elif not is_group_valid(current_screen_name, group_id):
        raise ValueError('group_id={} is invalid'.format(group_id))

    post_sql = '''
    insert into Post(user_id, created_at, content, parent_id, group_id) values (
        (select user_id from User where screen_name = %s),
        utc_timestamp(),
        %s,
        %s,
        %s
    );
    '''
    post_id = mysql_insert_id(post_sql, (current_screen_name, content, parent_id, group_id))

    topic_sql = '''
    insert into PostTopic (post_id, topic_id) values (%s, %s);
    '''
    for topic_id in topic_ids:
        mysql_statement_no_rows(topic_sql, (post_id, topic_id))
    return post_id

def is_post_relevant(current_screen_name, post, full_topics):
    user = get_user(current_screen_name)
    if post['created_at'] < user['last_notified_at']:
        return False

    followed_users = get_user_follows(current_screen_name)
    for followed_user in followed_users:
        if followed_user['user_id'] == post['user_id']:
            return True

    followed_topics = get_user_topics(current_screen_name)
    for topic in followed_topics:
        for full_topic in full_topics:
            if topic['topic_id'] == full_topic['topic_id']:
                return True

    return False

def cancel_pending_notification(current_screen_name, post, full_topics):
    relevant = is_post_relevant(current_screen_name, post, full_topics)
    if not relevant:
        return

    sql = '''
    insert ignore into CancelledNotification(user_id, post_id) values(
        (select user_id from User where screen_name = %s), 
        %s
    );
    '''
    mysql_statement_no_rows(sql, (current_screen_name, post['post_id']))

@transaction
def post_view(current_screen_name, post_id):
    post_sql = '''
    select U.screen_name, P.user_id, P.post_id, P.content, P.created_at, P.parent_id from Post P
    inner join User U on P.user_id = U.user_id where P.post_id = %s;
    '''
    post = mysql_query_one(post_sql, (post_id,))
    if post is None:
        return None, None, None

    topic_sql = '''
    with recursive TopicAncestor(ancestor_id, topic_id, ancestor_parent_id, full_topic) as(
        select topic_id, topic_id, parent_id, convert(name, char(65535)) from Topic
        where topic_id in (select topic_id from PostTopic where post_id = %s)
        union
        select Topic.topic_id, TopicAncestor.topic_id, Topic.parent_id, concat(name, '.', full_topic) from Topic
        inner join TopicAncestor on TopicAncestor.ancestor_parent_id = Topic.topic_id
        where Topic.topic_id > 1
    ) select ancestor_id as root_id, topic_id, full_topic from TopicAncestor where ancestor_parent_id = 1;
    '''
    full_topics = mysql_query_all(topic_sql, (post_id,))

    reaction_sql = '''
    select Reaction.name as reaction_name, count(*) as reaction_num
    from Reaction where post_id = %s group by reaction_name;
    '''
    reactions = mysql_query_all(reaction_sql, (post_id,))

    if current_screen_name is not None:
        cancel_pending_notification(current_screen_name, post, full_topics)

    return post, full_topics, reactions

@transaction
def post_tree(post_id, depth):
    depth_clause = ''
    if depth > 0:
        depth_clause = 'where PT.depth < {}'.format(depth)

    sql = '''
    with recursive PostTree(user_id, content, root_id, post_id, parent_id, created_at, full_path, depth) as (
        select 
        P.user_id, P.content, P.post_id, P.post_id, P.parent_id, P.created_at, convert(P.post_id, char(65535)), 1 from Post as P
        where P.post_id = %s
        union
        select P.user_id, P.content, PT.root_id, P.post_id, P.parent_id, P.created_at, concat(PT.full_path, ',', P.post_id), depth + 1 from Post as P
        inner join PostTree as PT on P.parent_id = PT.post_id
        {}
    )
    select U.screen_name, PT.content, PT.root_id, PT.post_id, PT.parent_id, PT.created_at, PT.full_path, PT.depth
    from PostTree PT inner join User U on PT.user_id = U.user_id;
    '''.format(depth_clause)
    return mysql_query_all(sql, (post_id,))

@transaction
def reaction_type_list():
    sql = '''
    select name from ReactionType;
    '''
    return mysql_query_all(sql, ())

@transaction
def post_react(screen_name, post_id, reaction):
    sql = '''
    insert into Reaction(user_id, post_id, name) values (
        (select user_id from User where screen_name = %s),
        %s,
        %s
    );
    '''
    mysql_statement_no_rows(sql, (screen_name, post_id, reaction))

@transaction
def notifications(screen_name):
    followed_user_sql = '''
    select 
    P.user_id, P.post_id, P.content, P.created_at, P.parent_id, U.screen_name 
    from Post P inner join User U on P.user_id = U.user_id, 
    (select user_id as u from User where screen_name = %s) as tmp 
    where
    P.created_at > (select last_notified_at from User where user_id = u) and (
        P.user_id in (select followee_id from FollowUser where follower_id = u) or
        exists (
            select * from PostTopic PT where PT.post_id = P.post_id and PT.topic_id in (
                select FT.topic_id from FollowTopic FT where FT.user_id = u
            )
        )
    ) and (
        P.post_id not in (
            select CN.post_id from CancelledNotification CN where CN.user_id = u
        )
    )
    '''
    return mysql_query_all(followed_user_sql, (screen_name,))

@transaction
def notifications_update(screen_name):
    update_sql = '''
    update User set last_notified_at = utc_timestamp() where screen_name = %s;
    '''
    mysql_statement_no_rows(update_sql, (screen_name,))

    delete_sql = '''
    delete from CancelledNotification where user_id =
    (select user_id from User where screen_name = %s);
    '''
    mysql_statement_no_rows(delete_sql, (screen_name,))

@transaction
def user_groups(screen_name):
    return get_user_groups(screen_name)

def get_user_groups(screen_name):
    sql = '''
        select G.group_id, G.created_at, G.name, G.description from `Group` as G
        inner join UserGroup UG using(group_id)
        where UG.user_id = (select user_id from User where screen_name = %s);
        '''
    return mysql_query_all(sql, (screen_name,))


@transaction
def group_create(screen_name, group_info):
    group_sql = '''
    insert into `Group` (created_at, description, name) values(
        utc_timestamp(),
        %s,
        %s
    );
    '''
    group_id = mysql_insert_id(group_sql, (group_info['description'], group_info['name']))

    user_group_sql = '''
    insert into UserGroup(user_id, group_id) values(
        (select user_id from User where screen_name = %s),
        %s
    );
    '''
    mysql_statement_no_rows(user_group_sql, (screen_name, group_id))
    return group_id

@transaction
def group_search(group_search_params):
    name = '%{}%'.format(group_search_params['name'])
    description = '%{}%'.format(group_search_params['description'])

    created_at_start = ''
    if group_search_params['created_at_start']:
        created_at_start = 'and created_at >= "{}"'.format(group_search_params['created_at_start'])

    created_at_end = ''
    if group_search_params['created_at_end']:
        created_at_end = 'and created_at <= "{}"'.format(group_search_params['created_at_end'])

    limit_clause = ''
    if group_search_params['limit'] > 0:
        limit_clause = 'limit {}'.format(group_search_params['limit'])

    offset_clause = ''
    if group_search_params['offset'] > 0:
        offset_clause = 'offset {}'.format(group_search_params['offset'])

    sql = '''
        select * from `Group`
        where name like %s and description like %s
        {}
        {}
        {}
        {};
        '''.format(created_at_start, created_at_end, limit_clause, offset_clause)
    return mysql_query_all(sql, (name, description))

@transaction
def group_members(group_id):
    sql = '''
    select * from User U where exists (
        select * from UserGroup UG where UG.user_id = U.user_id and UG.group_id = %s
    ); 
    '''
    return mysql_query_all(sql, (group_id,))

@transaction
def group_view(group_id):
    sql = '''
    select * from `Group` where group_id = %s;
    '''
    return mysql_query_one(sql, (group_id,))

@transaction
def group_join(screen_name, group_id):
    user_group_sql = '''
        insert into UserGroup(user_id, group_id) values(
            (select user_id from User where screen_name = %s),
            %s
        );
        '''
    mysql_statement_no_rows(user_group_sql, (screen_name, group_id))

@transaction
def group_leave(screen_name, group_id):
    user_group_sql = '''
        delete from UserGroup where user_id = 
            (select user_id from User where screen_name = %s)
        and group_id = %s;
        '''
    mysql_statement_no_rows(user_group_sql, (screen_name, group_id))
