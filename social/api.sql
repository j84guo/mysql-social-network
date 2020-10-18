-- 1. Create user
insert into User(created_at, description, location, name, screen_name, last_notified_at) values(
    utc_time(),
    "[optional] description",
    "[optional] location",
    "[optional] name",
    "[required] screen_name",
    utc_timestamp()
);
-- 1.1 insert each link (TODO: max number of links)
insert into UserUrl(user_id, url, display_order) values(568770232, "[required] url", 1);

-- 2. Update (your) user description, location, links, name
update User
    set description = "[optional] new description", location = "[optional] new location", name = "[optional] new name"
    where user_id = 568770232;
-- Delete old links and insert new
delete from UserUrl where user_id = 568770232;
insert into UserUrl(user_id, url, display_order) values(568770232, "[required] new url", 1);

-- 3. Search users by name, screen_name, created_at, location, description (TODO: generate query dynamically)
select * from User
    where name like '%' and screen_name like '%' and created_at > '2006-03-21 20:50:14'
    and created_at < '2006-04-21 20:50:14' and location like '%' and description like '%';

-- TODO: Figure out group posts, notifications, follows (if any)
-- 4. Create group
-- 5. Join/leave group
-- 6. Search groups

-- 7. Follow/unfollow user
insert into FollowUser(follower_id, followee_id) values(568770232, 568770233);
delete from FollowUser where follower_id = 568770232 and followee_id = 568770233;

-- 8. Follow/unfollow topic
insert into FollowTopic(user_id, topic_id) values(568770232, 391196)
delete from FollowTopic where user_id = 568770232 and topic_id = 391196;

-- 9. Make initial post
-- 10. Reply to post
-- 11. React to post (and undo reaction)
--
-- 12. List posts by a author, created date, multiple topics
--       > Fetch an entire tree rooted at some post_id
with recursive PostTree(root_id, post_id, created_at, full_path, depth) as (
    select P.post_id, P.post_id, P.created_at, convert(P.post_id, char(65535)), 1 from Post as P
    where P.post_id = 1239894107868344320
    union
    select PT.root_id, P.post_id, P.created_at, concat(PT.full_path, ',', P.post_id), depth + 1 from Post as P
    inner join PostTree as PT on P.parent_id = PT.post_id
)
select * from PostTree;
--       > Group results by tree when displaying (TODO: add Post.root_id)
--       > Allow option to view subtree and entire tree for given post
--       > Viewing by author or topic causes read timestamps to be updated, which affects notifications
--       > Listing is done for one author or one topic at a time. This allows us to implement "read flags" with a simple
--         timestamp for each author and topic. As mentioned above, these timestamps are used by notifications.
--       > Allow option to view latest or within date range. Read time should not be updated if the date range is prior
--         to the current read time.

-- 13. Search topics
--       > Find full topics (and their topic_id, root_id) by name, full name. This can also resolve topic trees.
with recursive FullTopic(root_id, topic_id, full_topic) as(
    select topic_id, topic_id, convert(name, char(65535)) from Topic where parent_id = 1
    union
    select FullTopic.root_id, Topic.topic_id, concat(full_topic, '.', name) from Topic
    inner join FullTopic on FullTopic.topic_id = Topic.parent_id
)
select * from FullTopic where full_topic like '%coronavirus%';

--       > Resolve a topic's root id
with recursive TopicAncestor(ancestor_id, topic_id, ancestor_parent_id, full_topic) as(
    select topic_id, topic_id, parent_id, convert(name, char(65535)) from Topic
    where topic_id = 616829
    union
    select Topic.topic_id, TopicAncestor.topic_id, Topic.parent_id, concat(name, '.', full_topic) from Topic
    inner join TopicAncestor on TopicAncestor.ancestor_parent_id = Topic.topic_id
    where Topic.topic_id > 1
) select * from TopicAncestor where ancestor_parent_id = 1;

-- 14. Add a new topic (cannot delete topics) when posting
--       > Make child of existing topic (based on search results)
--       > Specify full name
insert into Topic(name, parent_id) values('new_topic_name', 60);

-- 15. View notifications (cleared when you read from authors/topics)
--       > For each followed author and topic, find the posts made since their last notification time. We do not notify
--         the user of posts already viewed (those in CancelledNotification).
--       > After viewing notifications, the user's entries in CancelledNotification should be deleted and the user's
--         last notification time should be updated (TODO: maybe require explicitly clearing notifications).
-- New posts from followed authors since last read
select P.user_id, P.post_id, P.created_at, P.content, P.parent_id from User U
inner join FollowUser FU on U.user_id = FU.follower_id
inner join Post P on FU.followee_id = P.user_id
where U.user_id = 568770232 and P.created_at > U.last_notified_at
    and P.post_id not in (select CN.post_id from CancelledNotification CN where CN.user_id = U.user_id);
-- New posts from followed topics since last read
select U.user_id, U.last_notified_at, PT.post_id, PT.topic_id, P.created_at from User U
inner join FollowTopic FT on U.user_id = FT.user_id
inner join PostTopic PT on FT.topic_id = PT.topic_id
inner join Post P on PT.post_id = P.post_id
where U.user_id = 568770232 and P.created_at > U.last_notified_at
    and P.post_id not in (select CN.post_id from CancelledNotification CN where CN.user_id = U.user_id);

-- Combined notifications
select * from Post P inner join User U on P.user_id = U.user_id,
(select user_id as u from User where screen_name = "jackson") as tmp where
P.created_at > (select last_notified_at from User where user_id = u) and (
    P.user_id in (select followee_id from FollowUser where follower_id = u) or
    exists (
        select * from PostTopic PT where PT.post_id = P.post_id and PT.topic_id in (
            select FT.topic_id from FollowTopic FT where FT.user_id = u
        )
    )
)
-- Clear notifications (in the client, include a button to reload notifications)
update User set last_notified_at = utc_timestamp() where user_id = 568770232;
delete from CancelledNotification where user_id = 568770232;

-- * Deactivate user
--       > Can no longer be followed or searched
-- * Deactivate group
--       > Can no longer by joined or searched