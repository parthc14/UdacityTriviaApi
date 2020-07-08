import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
    CORS(app, resources={r'/*': {'origins': '*'}})
    '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization, true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET, PATCH, POST, DELETE, OPTIONS')
        return response
    '''
  @TODO:
  Create an endpoint to handle GET requests
  for all available categories.
  '''
    @app.route("/categories", methods=["GET"])
    def retrieve_all_categories():
        categories = {}
        selection = Category.query.order_by(Category.id).all()
        for category in selection:
            categories[category.id] = category.type
        return jsonify({
            "success": True,
            "categories": categories
        })
    '''
  @TODO:
  Create an endpoint to handle GET requests for questions,
  including pagination (every 10 questions).
  This endpoint should return a list of questions,
  number of total questions, current category, categories.

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions.
  '''
    def paginate_questions(request, selection):
        page = request.args.get('page', 1, type=int)
        start = (page - 1)*QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE
        current_questions = [question.format() for question in selection]
        return current_questions[start:end]

    @app.route('/questions')
    def retrieve_all_questions():

        selection = Question.query.order_by(Question.id).all()
        questions = paginate_questions(request, selection)
        if len(questions) == 0:
            abort(404)

        categories_query = Category.query.order_by(Category.type).all()
        categories = {}
        for category in categories_query:
            categories[category.id] = category.type
        return jsonify({
            "success": True,
            "questions": questions,
            "total_questions": len(Question.query.all()),
            "categories": categories,
            "current-categories": None
        })

    '''
  @TODO:
  Create an endpoint to DELETE question using a question ID.
    
  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page.
  '''
    @app.route('/questions/<int:question_id>', methods=["DELETE"])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()
            question.delete()
            return jsonify({
                "success": True,
                "deleted": question_id
            })
        except:
            abort(422)
    '''
  @TODO:
  Create an endpoint to POST a new question,
  which will require the question and answer text,
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab,
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.
  '''
    @app.route('/questions', methods=["POST"])
    def add_question():
        body = request.get_json()

        if ('question' not in body) and ('answer' not in body) and ('difficulty' not in body) and ('category' not in body):
            abort(422)

        question = body['question']
        answer = body['answer']
        difficulty = body['difficulty']
        category = body['category']

        try:
            new_question = Question(
                question=question, answer=answer, difficulty=difficulty, category=category)
            new_question.insert()

            return jsonify({
                "success": True,
                "new_question": new_question.id
            })

        except:
            abort(422)

    '''
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
    @app.route('/questions/search', methods=['POST'])
    def search_question():
        body = request.get_json()
        search_query = body.get('searchTerm', None)

        if not body:
            abort(404)

        if search_query:
            search_results = search_results = Question.query.filter(
                Question.question.ilike(f'%{search_query}%')).all()

        question = [question.format() for question in search_results]
        return jsonify({
            "success": True,
            "questions": question,
            "total_question": len(search_results)
        })
    '''
  @TODO: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def retrieve_questions_by_category(category_id):
        try:
            question = Question.query.filter(
                Question.category == str(category_id)).all()
            questions = [quest.format() for quest in question]
            return jsonify({
                'success': True,
                'questions': questions,
                'total_questions': len(questions),
                'current_category': category_id
            })
        except:
            abort(404)

    '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
    @app.route('/quizzes', methods=["POST"])
    def play_quiz():
        body = request.get_json()
        if not body:
            abort(404)

        previous_questions = body.get('previous_questions')
        quiz_category = body.get('quiz_category')

        if (quiz_category['id'] == 0):
            selection = Question.query.all()
        else:
            category_id = int(quiz_category.get('id'))
            selection = Question.query.filter_by(category == category_id).all()

        def generate_rand_questions():
            return selection[random.randint(0, len(selection)-1)]

        next_random_question = generate_rand_questions()

        is_new_question = True

        while is_new_question:
            if next_random_question.id in previous_questions:
                next_random_question = generate_rand_questions()
            else:
                is_new_question = False

        return jsonify({
            "success": True,
            "question": next_random_question.format()
        })

    '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'resource not found'
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'unprocessable'
        }), 422
    return app
