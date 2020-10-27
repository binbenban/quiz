#%%
from tinydb import TinyDB, Query
import os
import random
import base64
import re
from collections import Counter
# %%
DB_PATH = '/mnt/c/pcloud_ben/personal_project/quiz'
# %%
result_db = TinyDB(os.path.join(DB_PATH, 'result.json'))
# %%
result_db.all()[:10]
# %%
ids = [13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 33, 34, 35, 36, 14, -1, 39, 42, 43, 28, 38, 6, 44, 45, 47, 46, 48, 49, 50, 51, 52, 37, 53, 54, 55, 56, 57, 58, 59, 60, 62, 61, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83]
# %%
result_db.search(Query().id.any(ids))
# %%
Result = Query()
# %%
result_db.search(Result.id.one_of(ids))

# %%

# %%
