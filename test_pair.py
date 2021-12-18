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

not_users_pair = [
('chatid_user_2', 'chatid_user_5'),
('chatid_user_3', 'chatid_user_2'),
('chatid_user_6', 'chatid_user_3'),
]


def pairup(users, not_users_pair):
    random.shuffle(users)
    partners = deque(users)
    partners.rotate()
    new = list(zip(users, partners))
    if any(user in new for user in not_users_pair):
    	return pairup(users, not_users_pair)
    else:	
    	return new

pprint(pairup(users, not_users_pair))