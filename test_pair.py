from pprint import pprint
import random
from collections import deque


users = [
{'chatid_user_1': ['phone_user_1', 'username_1']},
{'chatid_user_2': ['phone_user_2', 'username_2']},
{'chatid_user_3': ['phone_user_3', 'username_3']},
{'chatid_user_4': ['phone_user_4', 'username_3']},
{'chatid_user_5': ['phone_user_5', 'username_3']},
{'chatid_user_6': ['phone_user_6', 'username_3']},
]


def get_created_pair(users):
    user_pairs=[]
    for user in range(len(users)):
        user_pair = users[user], users[(user+1)%(len(users))]
        user_pairs.append(user_pair)
    return user_pairs


def pairup(users):
    random.shuffle(users)
    partners = deque(users)
    partners.rotate()
    return list(zip(users, partners))

pprint(get_created_pair(users))
print()
pprint(pairup(users))