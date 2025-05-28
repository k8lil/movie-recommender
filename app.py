from flask import Flask, request, render_template
from recommendation import get_similar_movies

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    recommendations = []
    message = ""
    input_title = ""

    if request.method == 'POST':
        input_title = request.form.get('movie')
        if input_title:
            result = get_similar_movies(input_title)
            if result is None:
                message = f"Sorry, couldn't find any movie matching '{input_title}'. Please try again."
            else:
                matched_title, recommendations = result
                if matched_title.lower() != input_title.lower():
                    message = f"Showing results for closest match: '{matched_title}'"
        else:
            message = "Please enter a movie title."

    return render_template('index.html', recommendations=recommendations, message=message, input_title=input_title)

if __name__ == '__main__':
    app.run(debug=True)
