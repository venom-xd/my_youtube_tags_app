from flask import Flask, request, jsonify, render_template
from cron_descriptor import get_description
from datetime import datetime
from croniter import croniter
import requests
from bs4 import BeautifulSoup
import pandas as pd

app = Flask(__name__)

@app.route('/')
def index():
    data = generate_dashboard_data()
    return render_template('index2.html', gmp_data=data['gmp_data'], upcoming_ipo_data=data['upcoming_ipo_data'])


@app.route('/color_picker')
def color_picker():
    return render_template('color_picker.html') 

@app.route('/cron')
def cron():
    return render_template('cron.html') 

@app.route('/parse', methods=['POST'])
def parse_cron():
    data = request.get_json()
    cron_expression = data.get('cron')
    try:
        description = get_description(cron_expression)
        base_time = datetime.now()
        cron = croniter(cron_expression, base_time)
        next_run_time = cron.get_next(datetime)
        next_run_time_str = next_run_time.strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({
            'description': description,
            'nextRunTime': next_run_time_str
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/ipo-watch')
def ipo_watch():
    # URL of the IPO GMP list
    url = "https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/"
    
    # Fetch the page
    response = requests.get(url)
    if response.status_code != 200:
        return f"Failed to fetch data, status code: {response.status_code}", 500

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the GMP table
    table = soup.find('table')

    if not table:
        return "No table found", 500  # Return an error message if no table is found

    # Extract table rows
    ipo_data = []
    for row in table.find_all('tr')[1:]:  # Skip the header row
        cols = row.find_all('td')
        if len(cols) > 1:  # Ensure there are enough columns
            ipo_data.append([col.get_text(strip=True) for col in cols])

    # Render the table on your website
    return render_template('ipo_watch.html', ipo_data=ipo_data)



@app.route('/upcomingipo')  # New route for Upcoming IPOs
def upcoming_ipo():
    # URL of the upcoming IPO calendar
    url = "https://ipowatch.in/upcoming-ipo-calendar-ipo-list/"
    
    # Fetch the page
    response = requests.get(url)
    if response.status_code != 200:
        return f"Failed to fetch data, status code: {response.status_code}", 500

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the upcoming IPO table
    table = soup.find('table')

    if not table:
        return "No table found", 500  # Return an error message if no table is found

    # Extract table rows
    ipo_data = []
    for row in table.find_all('tr')[1:]:  # Skip the header row
        cols = row.find_all('td')
        if len(cols) > 1:  # Ensure there are enough columns
            ipo_data.append([col.get_text(strip=True) for col in cols])

    # Render the table on your website
    return render_template('upcoming_ipo.html', ipo_data=ipo_data)


def generate_dashboard_data():
    # Fetch IPO GMP data
    gmp_url = "https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/"
    gmp_response = requests.get(gmp_url)
    gmp_data = []

    if gmp_response.status_code == 200:
        gmp_soup = BeautifulSoup(gmp_response.text, 'html.parser')
        gmp_table = gmp_soup.find('table')
        
        if gmp_table:
            for row in gmp_table.find_all('tr')[1:]:  # Skip header
                cols = row.find_all('td')
                if len(cols) > 1:
                    gmp_data.append([col.get_text(strip=True) for col in cols])
                    if len(gmp_data) == 5:  # Limit to 5 entries
                        break

    # Fetch Upcoming IPO data
    upcoming_url = "https://ipowatch.in/upcoming-ipo-calendar-ipo-list/"
    upcoming_response = requests.get(upcoming_url)
    upcoming_ipo_data = []

    if upcoming_response.status_code == 200:
        upcoming_soup = BeautifulSoup(upcoming_response.text, 'html.parser')
        upcoming_table = upcoming_soup.find('table')
        
        if upcoming_table:
            for row in upcoming_table.find_all('tr')[1:]:  # Skip header
                cols = row.find_all('td')
                if len(cols) > 1:
                    upcoming_ipo_data.append([col.get_text(strip=True) for col in cols])
                    if len(upcoming_ipo_data) == 5:  # Limit to 5 entries
                        break

    # Combine the data to pass to the template
    return {
        'gmp_data': gmp_data,
        'upcoming_ipo_data': upcoming_ipo_data
    }



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
