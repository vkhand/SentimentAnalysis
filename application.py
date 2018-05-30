from flask import Flask, render_template, request
from wtforms import Form, TextAreaField, TextField, validators
from flask_bootstrap import Bootstrap
import graphlab
import pickle
import sqlite3
import os
import numpy as np

# import HashingVectorizer from local dir
#from vectorizer import vect

# Preparing the Classifier
cur_dir = os.path.dirname(__file__)
model = graphlab.load_model('my_model')
db = os.path.join(cur_dir, 'reviews.db')

def classify(document):
	#label = {0: 'negative', 1: 'positive'}
	sf = graphlab.SFrame({'review':[document]})
	sf['word_count'] = graphlab.text_analytics.count_words(sf['review'])
	#X = vect.transform([document])
	#sf= graphlab.SFrame({'word_count':[{'a':1,'and':1,'loved':1,'weekend':1}]})
	y = model.predict(sf)
	proba = model.predict(sf,output_type='probability')
	ans=proba[0]
	if(y.any()==1):
		label='positive'
	else:
		label='negative'
	#proba = np.max(model.predict_proba(X))
	return label, ans

#(document, y):
	#X = vect.transform([document])
	#model.partial_fit(X, [y])

def sqlite_entry(path, document, y):
	conn = sqlite3.connect(path)
	c = conn.cursor()
	c.execute("INSERT INTO review_db(review, sentiment) VALUES (?,?)", (document, y))
	conn.commit()
	conn.close()

app = Flask(__name__)
Bootstrap(app)
class ReviewForm(Form):
	
	moviereview = TextAreaField('',
			[validators.DataRequired(), validators.length(min=15)])


@app.route('/')
def index():
	form = ReviewForm(request.form)
	return render_template('reviewform.html', form=form)

@app.route('/results', methods=['POST'])
def results():
	form = ReviewForm(request.form)
	if request.method == 'POST' and form.validate():
		review = request.form['moviereview']
		
		y, proba = classify(review)
		return render_template('results.html',
	content=review,
	prediction=y,
	probability=round(proba*100, 2))
	return render_template('reviewform.html', form=form)

@app.route('/thanks', methods=['POST'])
def feedback():
	feedback = request.form['feedback_button']
	review = request.form['review']
	prediction = request.form['prediction']
	inv_label = {'negative': 0, 'positive': 1}
	y = inv_label[prediction]
	if feedback == 'Incorrect':
		y = int(not(y))
	#train(review, y)
	sqlite_entry(db,review, y)
	return render_template('thanks.html')

if __name__ == '__main__':
	app.run(debug=True)
