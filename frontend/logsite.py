#!/usr/bin/env python
from flask import Flask, render_template, request
from flask_pymongo import PyMongo
from dotenv import dotenv_values
from urllib.parse import quote_plus
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from math import ceil
from flask_bootstrap import Bootstrap5
import logging
from flask_paginate import Pagination, get_page_parameter



secrets = dotenv_values('.env')

uri = 'mongodb://{}:{}@mongo:27017/logbot?authsource={}'.format(secrets['MONGO_USER'], secrets['MONGO_PASS'], 'logbot')

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

app.secret_key = secrets['FLASK_SECRET_KEY']
app.config["MONGO_URI"] = uri
bootstrap = Bootstrap5(app)
csrf = CSRFProtect(app)

mongo = PyMongo(app, uri)

ITEMS_PER_PAGE = 9

class SearchForm(FlaskForm):
    
    query = StringField('', validators=[DataRequired()], render_kw={"placeholder": "Search..."})

@app.route("/", methods=['GET','POST'])
def home():
    page = request.args.get('page', 1, type=int)
    
    form = SearchForm()

    if form.validate_on_submit():
        query = form.query.data
        page=1
    else:
        query = ''
    
    if not query:
        query = request.args.get('query','')
    
    
    form.query.default = query
    form.process()
    
    data = paginate(query, ['created', 1], page=page)
    results = data['data']
    if results:
        count = data['metadata'][0]['totalCount']
    else:
        count = 0
    total_pages = ceil( count / ITEMS_PER_PAGE )

    pagination = Pagination(page=page, total=count, per_page=ITEMS_PER_PAGE,  css_framework='bootstrap5', href='?page={}&query={}'.format('{0}', query))

    return render_template('index.html', data=results, form=form, count=count, page=page, query=query, total_pages=total_pages, pagination=pagination)



def paginate(query, sort, page=1):
    match_channel = {'$match': { 'channel.name': 'gbclyde'}}
    match_deleted = {'$match': { 'deleted': False}}
    match_prompt  = {'$match': { 'prompt': { '$regex': query ,'$options': 'i'}}}
    meta = {'$facet': { 
                     'metadata': [{ '$count': 'totalCount'}],
                     'data': [{'$skip': (page - 1) * ITEMS_PER_PAGE}, {'$limit': ITEMS_PER_PAGE}]
            }}
   
    pipeline = [match_channel,
                match_deleted,
                match_prompt,
                meta
                ]

    return list(mongo.db.ai_interactions.aggregate(pipeline))[0]

@app.context_processor
def link_processor():
    def thumbnail(filename):
        """Insert thumnail into image filepath to serve up the smaller image"""
        name, ext = filename.split('.')
        return '.'.join([name, 'thumb', ext])
    return dict(thumbnail=thumbnail)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
