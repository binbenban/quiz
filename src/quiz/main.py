import copy
import os
from flask import Flask, request
import flask
import string
import random
from datetime import datetime
from config import Config
import db_conn


class QuestionHandler:
    def __init__(self):
        self.questions = []
    
    def generate(self, tag_list: list, size: int):
        raw = db.generate_questions(tag_list, size)
        self.questions = self.enrich_questions(raw)
        return self.questions

    def enrich_questions(self, questions):
        for ix, q in enumerate(questions):
            q["session_id"] = ix + 1
            choices = q["choices"]
            select_options = list(string.ascii_uppercase[:len(choices)])
            random.shuffle(select_options)

            for jx, ch in enumerate(choices):
                ch["option"] = select_options[jx]
            choices.sort(key=lambda x: x["option"])
        return questions


app = Flask(__name__)
app.config.from_object(Config)
db = db_conn.Database(app.config['DB_PATH'])
qh = QuestionHandler()


@app.route("/quiz/generate", methods=["GET"])
def quiz_generate():
    tags = request.args.get('tags')
    size = request.args.get('size')
    questions = qh.generate(tags.split(","), int(size))
    return flask.render_template(
        "quiz.html",
        title="Quiz",
        questions=questions,
    )


@app.route("/quiz/submit", methods=["POST"])
def quiz_submit():
    # for each question, get submitted answer
    res = []
    for q in qh.questions:
        rec = {}
        rec["session_id"] = q["session_id"]
        rec["id"] = q["id"]
        rec["choices"] = q["choices"]
        rec["answers"] = [ch["option"] for ch in q["choices"] if ch.get("is_answer")]
        rec["submitted"] = request.form.getlist(str(q["session_id"]))
        if isinstance(rec["submitted"], str):
            rec["submitted"] = list(rec["submitted"])
        if rec["answers"] == rec["submitted"]:
            rec["result"] = '<div style="color:green;">CORRECT</div>'
        else:
            rec["result"] = f'<div style="color:red;">WRONG. Answer is {rec["answers"]}</div>'
        res.append(rec)
    _save_result(res)
    return flask.jsonify(res)


@app.route("/question/input", methods=["GET", "POST"])
def question_input():
    if request.method == 'GET':
        # go to input page
        return flask.render_template(
            "question.html",
            title="Input Questions",
        )
    if request.method == "POST":
        if (
            not request.form.get("question_body") or
            not request.form.get("choice_A_body") or
            not request.form.get("choice_B_body") or
            not request.form.get("choice_C_body") or
            not request.form.get("choice_D_body") or
            not request.form.getlist("answer") or
            not request.form.get("tags")
        ):
            return "don't leave any field blank! not saved."

        _save_question(request.form)
        return "question saved."


def _save_question(form):
    question = {}
    question["id"] = db.get_next_question_id()
    question["question_body"] = form.get("question_body")
    choices = []
    for option in ["A", "B", "C", "D"]:
        choice = {}
        choice["choice_body"] = form.get(f"choice_{option}_body")
        if option in form.getlist("answer"):
            choice["is_answer"] = 1
        choices.append(choice)
    question["choices"] = choices
    question["tags"] = form.get("tags").split(",")
    db.save_question(question)


def _save_result(res):
    # format result
    to_save = []
    for rec in res:
        rec_new = {}
        rec_new["id"] = rec["id"]
        rec_new["correct_answer"] = [ch["choice_body"] for ch in rec["choices"] if ch.get("is_answer")]
        rec_new["submitted_answer"] = [ch["choice_body"] for ch in rec["choices"] if ch["option"] in rec["submitted"]]
        rec_new["correct"] = rec_new["correct_answer"] == rec_new["submitted_answer"]
        rec_new["timestamp"] = datetime.now().strftime("%Y%m%d %H:%M:%S")
        to_save.append(rec_new)
    db.save_result(to_save)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000, debug=True)
