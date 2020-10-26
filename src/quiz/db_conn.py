from tinydb import TinyDB, Query
import os
import random
import base64
from collections import Counter


class Database:
    def __init__(self, db_path):
        # cur_dir = os.path.abspath(os.path.dirname(__file__))
        self.question_db = TinyDB(os.path.join(db_path, 'question.json'))
        self.result_db = TinyDB(os.path.join(db_path, 'result.json'))

    def generate_questions(
        self, tag_list: list, size: int, times_wrong: int = 0, last_wrong: bool = False
    ) -> list:
        questions = self.question_db.search(Query().tags.any(tag_list))

        if times_wrong:
            wrong_results = [x for x in self.result_db.search(Query().correct == False)]
            wrong_id_counts = Counter([x["id"] for x in wrong_results])
            wrong_ids = [k for k, v in wrong_id_counts.items() if v >= times_wrong]
            # filter by ids
            questions = [x for x in questions if x["id"] in wrong_ids]
        
        if last_wrong:
            questions_temp = []
            ids = [x["id"] for x in questions]
            all_results = [x for x in self.result_db.search(Query().id.any(ids))]
            for q in questions:
                # search the last result in all_results
                last_timestamp = "00000000 00:00:00"
                last_result = None
                for r in all_results:
                    if r["id"] == q["id"]:
                        if r["timestamp"] > last_timestamp:
                            last_timestamp = r["timestamp"]
                            last_result = r["correct"]
                if not last_result:  # not found or last wrong
                    questions_temp.append(q)
            questions = questions_temp

        random.shuffle(questions)
        return questions[:size]

    def save_question(self, question):
        Question = Query()
        exists = self.question_db.search(Question.id == question['id'])
        if exists:
            self.question_db.remove(Question.id == question['id'])
        self.question_db.insert(question)

    def save_result(self, result):
        for r in result:
            self.result_db.insert(r)

    def get_next_question_id(self):
        od = sorted(self.question_db.all(), key=lambda x: x["id"])
        return od[-1]["id"] + 1

    def get_all_tags(self):
        tags = set()
        for q in self.question_db.all():
            for tag in q.get("tags", []):
                tags.add(tag)
        return sorted(list(tags))

    def search_questions(self, question_keyword: str, tags: list) -> list:
        Question = Query()
        res = self.question_db.search(Question.tags.any(tags))
        if question_keyword:
            res = [
                x for x in res 
                if question_keyword.lower() in \
                    str(base64.b64decode(x["question_body"].encode()).lower())
            ]
        return res

    def update_questions(self, questions: list):
        for q in questions:
            Question = Query()
            self.question_db.remove(Question.id == q["id"])
            self.question_db.insert(q)

    def search_question_by_qid(self, qid: int) -> dict:
        Question = Query()
        res = self.question_db.search(Question.id == qid)
        if res:
            return res[0]
        else:
            return None

    def delete_question_by_id(self, qid: int):
        Question = Query()
        self.question_db.remove(Question.id == qid)
