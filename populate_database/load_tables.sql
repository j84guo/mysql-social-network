-- Use large buffer pool size to facilitate loading
set global innodb_buffer_pool_size = 1024 * 1024 * 1024 * 8;

-- Disable fk's while loading
set foreign_key_checks = 'OFF';

load data infile '/var/lib/mysql-files/Post.csv' into table Post
    fields terminated by ',' lines terminated by '\n'
    (user_id, created_at, post_id, content, parent_id)
    set group_id = null;

load data infile '/var/lib/mysql-files/User.csv' into table User
    fields terminated by ',' lines terminated by '\n'
    (created_at, description, user_id, location, name, screen_name)
    set last_notified_at = utc_timestamp();

load data infile '/var/lib/mysql-files/UserUrl.csv' into table UserUrl
    fields terminated by ',' lines terminated by '\n'
    (user_id, url, display_order);

load data infile '/var/lib/mysql-files/Topic.csv' into table Topic
    fields terminated by ',' lines terminated by '\n'
    (topic_id, name, parent_id, root_id);

load data infile '/var/lib/mysql-files/PostTopic.csv' into table PostTopic
    fields terminated by ',' lines terminated by '\n'
    (post_id, topic_id);

load data infile '/var/lib/mysql-files/FollowUser.csv' into table FollowUser
    fields terminated by ',' lines terminated by '\n'
    (follower_id, followee_id);

-- Re-enable foreign key checks
set foreign_key_checks = 'ON';
-- Null any non-existent parent pointers (we only fetch a subset of Twitter's entire website)
update Post set parent_id = null where parent_id not in (select * from (select post_id from Post) as tmp);

-- Insert default reactions
insert into ReactionType(name) values('like');
insert into ReactionType(name) values('dislike');