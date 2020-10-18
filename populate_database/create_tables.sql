-- A user's personal information.
create table User(
    created_at datetime not null,
    description varchar(256),
    user_id bigint unsigned primary key auto_increment,
    location varchar(256),
    name varchar(64),
    screen_name varchar(64) unique not null,
    last_notified_at datetime not null
) charset=utf8mb4;

alter table User add index (created_at);
alter table User add index (screen_name);
alter table User add index (name);

-- A user may have multiple URL's in their profile.
create table UserUrl(
    user_id bigint unsigned,
    url varchar(2048) charset ascii,
    display_order int unsigned,
    primary key(user_id, url)
) charset=utf8mb4;

alter table UserUrl add foreign key (user_id) references User(user_id);

-- We escape SQL keyword `Group`.
create table `Group`(
    created_at datetime not null,
    description varchar(256),
    group_id bigint unsigned primary key auto_increment,
    name varchar(64) unique not null
) charset=utf8mb4;

alter table `Group` add index (created_at);

-- Group membership is a reciprocal relationship; members see each other's posts in the group.
create table UserGroup(
    user_id bigint unsigned,
    group_id bigint unsigned,
    primary key(user_id, group_id),
    index(group_id, user_id)
);

alter table UserGroup add foreign key (user_id) references User(user_id);
alter table UserGroup add foreign key (group_id) references `Group`(group_id);

-- User follows are directed edges.
create table FollowUser(
    follower_id bigint unsigned,
    followee_id bigint unsigned,
    primary key(follower_id, followee_id),
    index(followee_id, follower_id)
);

alter table FollowUser add foreign key (follower_id) references User(user_id);
alter table FollowUser add foreign key (followee_id) references User(user_id);

-- Posts are textual.
create table Post(
    user_id bigint unsigned not null,
    created_at datetime not null,
    post_id bigint unsigned primary key auto_increment,
    content text not null,
    parent_id bigint unsigned,
    group_id bigint unsigned,
) charset=utf8mb4;

alter table Post add foreign key(user_id) references User(user_id);
alter table Post add foreign key(parent_id) references Post(post_id);
alter table Post add foreign key(group_id) references `Group`(group_id);
alter table Post add index (created_at);

-- Attribute list for allowable reactions.
create table ReactionType(
    name varchar(64) primary key
) charset=utf8mb4;

-- Reactions made by users to posts.
create table Reaction(
    post_id bigint unsigned,
    user_id bigint unsigned,
    name varchar(64),
    primary key(post_id, user_id, name)
) charset=utf8mb4;

alter table Reaction add foreign key(name) references ReactionType(name);
alter table Reaction add foreign key(user_id) references User(user_id);
alter table Reaction add foreign key(post_id) references Post(post_id);

-- Topics are grouped in an immutable hierarchy.
create table Topic(
    topic_id bigint unsigned primary key auto_increment,
    name varchar(256) not null collate utf8mb4_bin,
    parent_id bigint unsigned not null,
    unique(name, parent_id)
) auto_increment = 2, charset=utf8mb4;

alter table Topic add foreign key(parent_id) references Topic(topic_id);
insert into Topic values(1, 'NO_PARENT', 1);

-- Posts may have multiple topics. Note that having a topic does not mean
-- having its children as topics.
create table PostTopic(
    post_id bigint unsigned,
    topic_id bigint unsigned,
    primary key(post_id, topic_id),
    index(topic_id, post_id)
);

alter table PostTopic add foreign key(post_id) references Post(post_id);
alter table PostTopic add foreign key(topic_id) references Topic(topic_id);

-- Users may follow topics.
create table FollowTopic(
    user_id bigint unsigned,
    topic_id bigint unsigned,
    primary key(user_id, topic_id),
    index(topic_id, user_id)
);

alter table FollowTopic add foreign key(user_id) references User(user_id);
alter table FollowTopic add foreign key(topic_id) references Topic(topic_id);

-- When a user reads a post by a followed user or with a followed topic which was posted AFTER the last notification
-- time (i.e. it is a pending notification), then we insert that post into this table. It will be skipped
-- (i.e. becomes a cancelled notification) the next time the user lists their notifications.
create table CancelledNotification(
    user_id bigint unsigned,
    post_id bigint unsigned,
    primary key(user_id, post_id)
);

alter table CancelledNotification add foreign key(user_id) references User(user_id);
alter table CancelledNotification add foreign key(post_id) references Post(post_id);