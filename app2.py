from flask import Flask, request, jsonify, render_template

from cron_descriptor import get_description
from datetime import datetime
from croniter import croniter

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index2.html')

@app.route('/parse', methods=['POST'])
def parse_cron():
    data = request.get_json()
    cron_expression = data.get('cron')
    try:
        # Generate description
        description = get_description(cron_expression)

        # Get next run time
        base_time = datetime.now()  # Use current time as base
        cron = croniter(cron_expression, base_time)
        next_run_time = cron.get_next(datetime)  # Get next run time in UTC

        # Format next run time
        next_run_time_str = next_run_time.strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({
            'description': description,
            'nextRunTime': next_run_time_str
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.run(host='0.0.0.0', port=5000, debug=True)
