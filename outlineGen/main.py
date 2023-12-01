# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, session, redirect, url_for
import openai
import re

app = Flask(__name__)
openai.api_key = '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'
app.config["SECRET_KEY"] = "ADSFASDFASDFASDF34A78ADSFHJASDH333"

@app.route('/')
def landing_page():
    return render_template('index.html')

@app.route('/form', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        print("Received form data:", request.form)  # Debugging: log received form data

        genre = request.form.get('genre')
        storyline = request.form.get('storyline')

        if not genre or not storyline:  # Check if required fields are present
            print("Error: Genre or Storyline missing.")
            return "Error: Genre or Storyline missing.", 400

        characters = [request.form.get(f'character{i}') for i in range(1, 6) if request.form.get(f'character{i}')]

        if not characters:  # Check if at least one character is present
            print("Error: No characters provided.")
            return "Error: No characters provided.", 400

    if request.method == 'POST' and 'genre' in request.form:
        genre = request.form['genre']
        character1 = request.form['character1']
        character2 = request.form['character2']
        storyline = request.form['storyline']

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "write a concise outline divided in six brief sentences"},
                {"role": "user", "content": f"with a genre of {genre}"},
                {"role": "user", "content": f"character 1 name {character1}"},
                {"role": "user", "content": f"character 2 name {character2}"},
                {"role": "user", "content": f"with a storyline of: {storyline}"},
                {"role": "user", "content": "act as creative fiction writer; Each section will be connected with the previos one, it will maintain the genre and characters, be creative and detailed"},
            ],
            temperature=1,
            max_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0

        )

        # Log the AI Response
        print("AI Response:", response["choices"][0]["message"]["content"])

        # Process the AI response
        try:
            answer = response["choices"][0]["message"]["content"]
            print("AI Response:", answer)  # Debug: print the actual response

            # Adjusted regular expression to split on numbered sections
            outline_parts = re.split(r'\b\d+\.\s', answer)
            if len(outline_parts) < 2:
                raise ValueError("Invalid outline format")

            outline_parts.pop(0)  # Remove the first item
            session['outline_parts'] = outline_parts
            return redirect(url_for('outline'))

        except (KeyError, IndexError, ValueError) as e:
            print(f"Error processing response: {e}")
            # Fallback: Use the entire response as a single part
            session['outline_parts'] = [answer]
            return redirect(url_for('outline'))
        
    # Render the form page for GET request
    return render_template('form.html')


@app.route('/outline', methods=['GET', 'POST'])
def outline():
    if request.method == 'POST':
        # Check if we're modifying a part of the outline
        if 'sentence' in request.form and 'modsentence' in request.form:
            sentence_number = int(request.form["sentence"]) - 1
            modsentence = request.form['modsentence']

            outline_parts = session.get('outline_parts', [])
            if 0 <= sentence_number < len(outline_parts):
                outline_parts[sentence_number] = modsentence
                session['outline_parts'] = outline_parts

    return render_template('outline.html', outline_parts=session.get('outline_parts', []))

@app.route('/ai_modify', methods=['POST'])
def ai_modify():
    if 'sentence' in request.form and 'modsentence' in request.form:
        sentence_number = int(request.form["sentence"]) - 1
        modsentence = request.form['modsentence']

        outline_parts = session.get('outline_parts', [])
        if 0 <= sentence_number < len(outline_parts):
            # Retrieve the current outline part to be modified
            current_part = outline_parts[sentence_number]

            # Construct the prompt for OpenAI, including the unchanged parts
            prompt = "Here is the current outline:\n"
            for i, part in enumerate(outline_parts):
                prompt += f"{i+1}. {part}\n"
            prompt += f"\nPlease rewrite the following part with more creativity but maintain same plot as previously created, detail, and specificity, while maintaining the same genre and characters, and without altering the setting. Keep the narrative engaging and avoid generic descriptions.\nPart to modify: {modsentence}"

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )

            # Extract the modified part from the response
            modified_response = response.choices[0].message["content"].strip()
            
            # Split the response to get the updated part
            updated_parts = re.split(r'\d+\.\s+', modified_response)[1:]

            # Update only the specific part of the outline
            if len(updated_parts) > sentence_number:
                outline_parts[sentence_number] = updated_parts[sentence_number]
                session['outline_parts'] = outline_parts

        # Redirect back to the outline route with a query parameter for the modified part
        return redirect(url_for('outline', modified_part=sentence_number))

    # If the form data is not as expected, redirect to the outline page without modifications
    return redirect(url_for('outline'))

       
@app.route('/reset', methods=['POST'])
def reset():
    session.pop('outline_parts', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=4000)