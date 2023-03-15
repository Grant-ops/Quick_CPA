aaaa

from flask import Flask, render_template, url_for, redirect, request, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    results = db.relationship('Result', backref='user', lazy=True)

class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    questions = db.relationship('Question', backref='chapter', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String, nullable=False)
    choice_a = db.Column(db.String, nullable=False)
    choice_b = db.Column(db.String, nullable=False)
    choice_c = db.Column(db.String, nullable=False)
    choice_d = db.Column(db.String, nullable=False)
    correct_choice = db.Column(db.String, nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    correct = db.Column(db.Boolean, nullable=False)
    confidence = db.Column(db.String, nullable=True)

def create_and_populate_db():
    with app.app_context():
        db.create_all()

    sample_chapters = [
        {'name': 'Chapter 1'},
        {'name': 'Chapter 2'},
        {'name': 'Chapter 3'}
    ]
    for c in sample_chapters:
        chapter = Chapter(name=c['name'])
        db.session.add(chapter)
        db.session.commit()
        for i, q in enumerate(range(3)):
            question = Question(
                question=f'Question {i+1} for {chapter.name}',
                choice_a='A',
                choice_b='B',
                choice_c='C',
                choice_d='D',
                correct_choice='A',
                chapter_id=chapter.id
            )
            db.session.add(question)

    db.session.commit()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user is None:
            user = User(email=email)
            db.session.add(user)
            db.session.commit()
        return redirect(url_for('select_chapter', user_id=user.id))
    return render_template('login.html')

@app.route('/select_chapter', methods=['GET', 'POST'])
def select_chapter():
    if request.method == 'POST':
        user_id = request.args.get('user_id')
        chapter_id = request.form.get('chapter')
        if chapter_id:
            return redirect(url_for('exam', user_id=user_id, chapter_id=chapter_id))
        else:
            flash('Please select a chapter', 'warning')
            return redirect(url_for('select_chapter', user_id=user_id))
    chapters = Chapter.query.all()
    return render_template('select_chapter.html', chapters=chapters)

@app.route('/exam/<int:user_id>/<int:chapter_id>', methods=['GET', 'POST'])
def exam(user_id, chapter_id):
    user = User.query.get_or_404(user_id)
    chapter = Chapter.query.get_or_404(chapter_id)
    question = random.choice(Question.query.filter_by(chapter_id=chapter_id).all())
    if request.method == 'POST':
        user_choice = request.form['choice']
        correct = user_choice == question.correct_choice
        result = Result(user_id=user.id, question_id=question.id, correct=correct)
        db.session.add(result)
        db.session.commit()
        if correct:
            return redirect(url_for('exam', user_id=user.id, chapter_id=chapter.id))
        else:
            flash('Incorrect. Try again.')
    return render_template('exam.html', chapter=chapter, question=question,
                           choices=[question.choice_a, question.choice_b, question.choice_c, question.choice_d])


@app.route('/confidence/<int:result_id>', methods=['GET', 'POST'])
def confidence(result_id):
    result = Result.query.get_or_404(result_id)
    if request.method == 'POST':
        confidence = request.form['confidence']
        result.confidence = confidence
        db.session.commit()
        flash('Your confidence level has been recorded.')
        return redirect(url_for('exam', user_id=result.user_id, chapter_id=result.question.chapter_id))
    return render_template('confidence.html', result=result)


@app.route('/results/<int:user_id>')
def results(user_id):
    user = User.query.get_or_404(user_id)
    total_questions = len(user.results)
    correct_questions = sum(1 for r in user.results if r.correct)
    incorrect_questions = total_questions - correct_questions
    return render_template('results.html', user=user, correct_questions=correct_questions,
                           incorrect_questions=incorrect_questions)


if __name__ == '__main__':
    with app.app_context():
        create_and_populate_db()
    app.run(debug=True)
