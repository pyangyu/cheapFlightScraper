from flask import Flask, render_template, request

app = Flask(__name__)

# Sample list of airports - you can expand this later
AIRPORTS = [
    "Beijing Capital International Airport (PEK)",
    "Shanghai Pudong International Airport (PVG)",
    "Guangzhou Baiyun International Airport (CAN)",
    "Shenzhen Bao'an International Airport (SZX)",
    "Chengdu Shuangliu International Airport (CTU)"
]

@app.route('/', methods=['GET', 'POST'])
def index():
    selected_from = None
    selected_to = None
    
    if request.method == 'POST':
        selected_from = request.form.get('from_airport')
        selected_to = request.form.get('to_airport')
    
    return render_template('index.html', 
                         airports=AIRPORTS,
                         selected_from=selected_from,
                         selected_to=selected_to)

if __name__ == '__main__':
    app.run(debug=True) 