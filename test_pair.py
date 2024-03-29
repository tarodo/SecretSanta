from pprint import pprint
import random
from collections import deque


users = [
'chatid_user_1',
'chatid_user_2',
'chatid_user_3',
'chatid_user_4',
'chatid_user_5',
'chatid_user_6',
]



def get_created_pair(users=None):
    user_pairs=[]
    for user in range(len(users)):
        user_pair = users[user], users[(user+1)%(len(users))]
        user_pairs.append(user_pair)
    return user_pairs

not_user_pairs = [
('chatid_user_2', 'chatid_user_5'),
('chatid_user_3', 'chatid_user_2'),
('chatid_user_6', 'chatid_user_3'),
]



def pairup(users, not_user_pairs):
    random.shuffle(users)
    partners = deque(users)
    partners.rotate()
    new_pairs = list(zip(users, partners))
    if any(pair in new_pairs for pair in not_user_pairs):
    	return pairup(users, not_user_pairs)
    else:	
    	return new_pairs

pprint(pairup(users, not_user_pairs))