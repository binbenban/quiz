from tinydb import TinyDB, Query
import os
import random


class Database:
    def __init__(self, db_path):
        # cur_dir = os.path.abspath(os.path.dirname(__file__))
        self.question_db = TinyDB(os.path.join(db_path, 'question.json'))
        self.result_db = TinyDB(os.path.join(db_path, 'result.json'))

    def generate_questions(self, tag_list: list, size: int) -> list:
        Question = Query()
        all_res = self.question_db.search(Question.tags.any(tag_list))
        random.shuffle(all_res)
        return all_res[:size]

    def save_question(self, question):
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
        return list(tags)

    def search_questions(self, question_keyword: str, tags: list) -> list:
        Question = Query()
        all_res = self.question_db.search(Question.tags.any(tags))
        if question_keyword:
            all_res = [
                x
                for x in all_res 
                if question_keyword in x["question_body"]
            ]
        return all_res

    def update_questions(self, questions: list):
        for q in questions:
            Question = Query()
            self.question_db.remove(Question.id == q["id"])
            self.question_db.insert(q)
