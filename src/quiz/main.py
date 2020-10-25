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
    
    def generate(self, tag_list: list, size: int, times_wrong: int, last_wrong: bool):
        raw = db.generate_questions(tag_list, size, times_wrong, last_wrong)
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


@app.route("/", methods=["GET"])
@app.route("/quiz/generate", methods=["GET", "POST"])
def quiz_generate():
    if request.method == "GET":
        # go to page with selections
        return flask.render_template(
            "quiz_selection.html",
            title="Quiz Selection",
            tags=db.get_all_tags(),
        )
    if request.method == "POST":
        print(request.form)
        tags = request.form.getlist("tags")
        size = request.form.get("size")
        times_wrong = request.form.get("times_wrong")
        if times_wrong:
            times_wrong = int(times_wrong)
        last_wrong = request.form.get("last_wrong") is not None
        
        questions = qh.generate(tags, int(size), times_wrong, last_wrong)
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


@app.route("/question/edit", methods=["GET", "POST"])
def question_edit():
    if request.method == "GET":
        return flask.render_template(
            "question_edit.html",
            title="Maintain Questions",
            tags=db.get_all_tags(),
        )
    if request.method == "POST":
        print(request.form)
        res = db.search_questions(
            request.form.get("question_keyword"),
            request.form.getlist("tags"),
        )
        return flask.jsonify(res)


@app.route("/question/save", methods=["POST"])
def question_save():
    questions = eval(request.form.get("questions_found"))
    print(questions)
    db.update_questions(questions)
    return "updated"


@app.route("/question/create", methods=["GET", "POST"])
def question_create():
    if request.method == 'GET':
        return flask.render_template(
            "question_create.html",
            title="Input Questions",
            tags=db.get_all_tags(),
        )
    if request.method == "POST":
        print(request.form)
        if (
            not request.form.get("question_body") or
            not request.form.get("choice_A_body") or
            not request.form.get("choice_B_body") or
            not request.form.get("choice_C_body") or
            not request.form.get("choice_D_body") or
            not request.form.getlist("answer") or
            (not request.form.get("tags") and not request.form.get("tags_selection"))
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
    tags = []
    if form.get("tags"):
        tags += form.get("tags").split(",")
    if form.get("tags_selection"):
        tags_list = [x.strip() for x in form.get("tags_selection").split(",")]
        tags += tags_list
    question["tags"] = list(set(tags))
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
