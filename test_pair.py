from pprint import pprint
import random
from collections import deque


users = ['user_1', 'user_2', 'user_3', 'user_4', 'user_5', 'user_6',]


def get_created_pair(users):
    user_pairs=[]
    for user in range(len(users)):
        user_pair = users[user],'готовит подарок для',users[(user+1)%(len(users))]
        user_pairs.append(user_pair)
    return user_pairs


def pairup(users):
    random.shuffle(users)
    partners = deque(users)
    partners.rotate()
    return dict(zip(users, partners))

pprint(get_created_pair(users))
print()
pprint(pairup(users))