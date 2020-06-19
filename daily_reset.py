from myproject import *
import os
import random

def resetPosts():
    for i in Post.query.all():
        db.session.delete(i)
    for k in Event_Post.query.all():
        db.session.delete(k)
    db.session.commit()
    
    for i in os.listdir('static/uploads/posts'):
        os.remove(os.path.join('static/uploads/posts', i))

    for i in os.listdir('static/uploads/event_posts'):
        os.remove(os.path.join('static/uploads/event_posts', i))

def resetComments():
    for i in Comment.query.all():
        db.session.delete(i)
    db.session.commit()

def updateStreaks():
    for user in User.query.all():
        user.accepted_coins = 0
        if user.posts:
            user.post_streak = user.post_streak + 1 
        else:     
            user.post_streak = 0
        user.event = 0
        
    db.session.commit()



if __name__ == '__main__':
    updateStreaks()
    resetPosts()
    resetComments()
    ranked_users = rankUsers()
    try:
        ranked_users[0].coins = ranked_users[0].coins + 20
    except:
        print("no first place")
    try:
        ranked_users[1].coins = ranked_users[1].coins + 10
    except:
        print("no second place")
    try:
        ranked_users[2].coins = ranked_users[2].coins + 5
    except:
        print("no third place")

    Title.generateDailyTitles()
    #post_streak