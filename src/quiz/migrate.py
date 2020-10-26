#%%
import base64
from tinydb import TinyDB, Query
import os

# %%
db = TinyDB(os.path.join('/mnt/c/pcloud_ben/personal_project/quiz', 'question.json'))


#%%
for q in db.all():
    q['question_body'] = base64.b64encode(q['question_body'].encode()).decode('utf-8')
    for ch in q['choices']:
        ch['choice_body'] = base64.b64encode(ch['choice_body'].encode()).decode('utf-8')
    Question = Query()
    db.remove(Question.id == q["id"])
    db.insert(q)


