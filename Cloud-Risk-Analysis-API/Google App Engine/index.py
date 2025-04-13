import os
from flask import Flask, request, jsonify
import yfinance as yf
from datetime import date, timedelta
import json
import http.client
import time
from ImageCharts import ImageCharts
from concurrent.futures import ThreadPoolExecutor
import boto3
import uuid
import math
os.environ['AWS_SHARED_CREDENTIALS_FILE'] = './cred'
app = Flask(__name__)

analysis_results = {
    "var95": [], "var99": [], "profit_loss": [],
    "avg_var95": 0, "avg_var99": 0, "total_profit_loss": 0,
    "chart_url": "", "time_cost": 0,
    "lambda_duration_ms": 0, "lambda_billed_duration_ms": 0,
    "lambda_memory_size_mb": 128
}

warmup_info = {
    "scale_ready": False, "total_billable_time": 0,
    "total_cost": 0.0, "runs": 0, "service": "",
    "ec2_instances": []
}

termination_info = {"scale_terminated": False}

EC2_IMAGE_ID = 'ami-07b2cc49c72a0bb9a'
EC2_INSTANCE_TYPE = 't2.micro'
EC2_KEY_NAME = 's-east-1kp'
EC2_SECURITY_GROUP_ID = 'SSH'

class StockAnalysisGAE:
    def __init__(self, h=0, d=0, t='', p=0):
        self.h, self.d, self.t, self.p = h, d, t, p
        self.lambda_host = 'lza0qf4e4l.execute-api.us-east-1.amazonaws.com'
        self.lambda_path = '/default/test'
        self.data = None
        self.signals = []
        self.close_prices = []
        self.ec2_client = boto3.client('ec2', region_name='us-east-1')
        self.chart_url = None

    def fetch_data_and_find_signals(self):
        today = date.today()
        time_past = today - timedelta(days=1095)
        symbol = 'AMZN'
        self.data = yf.download(symbol, start=time_past, end=today)
        self.data['Buy'] = 0
        self.data['Sell'] = 0

        body = 0.01
        for i in range(2, len(self.data)):
            if (self.data.Close[i] - self.data.Open[i]) >= body and self.data.Close[i] > self.data.Close[i - 1] and \
                    (self.data.Close[i - 1] - self.data.Open[i - 1]) >= body and self.data.Close[i - 1] > self.data.Close[i - 2] and \
                    (self.data.Close[i - 2] - self.data.Open[i - 2]) >= body:
                self.data.at[self.data.index[i], 'Buy'] = 1
            if (self.data.Open[i] - self.data.Close[i]) >= body and self.data.Close[i] < self.data.Close[i - 1] and \
                    (self.data.Open[i - 1] - self.data.Close[i - 1]) >= body and self.data.Close[i - 1] < self.data.Close[i - 2] and \
                    (self.data.Open[i - 2] - self.data.Close[i - 2]) >= body:
                self.data.at[self.data.index[i], 'Sell'] = 1

        self.signals = self.data[['Buy', 'Sell']].to_dict(orient='records')
        self.close_prices = self.data['Close'].tolist()

    def invoke_lambda(self, signals, close_prices):
        c = http.client.HTTPSConnection(self.lambda_host)
        payload = json.dumps({
            "signals": signals, "close_prices": close_prices,
            "h": self.h, "d": self.d, "t": self.t, "p": self.p
        })
        headers = {'Content-type': 'application/json'}
        c.request("POST", self.lambda_path, payload, headers)
        response = c.getresponse()
        response_data = response.read().decode('utf-8')

        print(f"Lambda response: {response_data[:500]}")  
        return response_data

    def run(self):
        start_time = time.time()
        self.fetch_data_and_find_signals()
        response = self.invoke_lambda(self.signals, self.close_prices)

        print("Full Lambda response:", response)

        try:
            lambda_response = json.loads(response)
            
            if 'body' in lambda_response:
                analysis_data = json.loads(lambda_response['body'])
                print("Parsed analysis data:", analysis_data)
            else:
                print("Warning: 'body' key not found in Lambda response.")
                return {"error": "Invalid response from Lambda"}

            analysis_results.update({
                'var95': analysis_data.get('Signal VaR95', []),
                'var99': analysis_data.get('Signal VaR99', []),
                'profit_loss': analysis_data.get('Signal Profit/Loss', []),
                'avg_var95': analysis_data.get('Average VaR95', 0),
                'avg_var99': analysis_data.get('Average VaR99', 0),
                'total_profit_loss': sum(analysis_data.get('Signal Profit/Loss', [])),
                'chart_url': self.get_chart_url()
            })

            print(f"Updated analysis results: {analysis_results}")  
            execution_details = lambda_response.get('executionDetails', {})
            analysis_results.update({
                'lambda_duration_ms': execution_details.get('duration_ms', 0),
                'lambda_billed_duration_ms': execution_details.get('billed_duration_ms', 0),
                'lambda_memory_size_mb': execution_details.get('memory_size_mb', 128)
            })

        except json.JSONDecodeError as e:
            print("Error decoding JSON:", e)
            return {"error": "Failed to decode Lambda response"}

        analysis_results['time_cost'] = time.time() - start_time
        return {"result": "ok"}

    def warm_up_ec2(self, runs):
        warmup_info.update({'runs': runs, 'service': 'ec2'})
        warmup_info['start_time'] = time.time() 

        for _ in range(runs):
            instance = self.ec2_client.run_instances(
                ImageId=EC2_IMAGE_ID, InstanceType=EC2_INSTANCE_TYPE,
                KeyName=EC2_KEY_NAME, SecurityGroupIds=[EC2_SECURITY_GROUP_ID],
                MinCount=1, MaxCount=1,
                TagSpecifications=[{
                    'ResourceType': 'instance',
                    'Tags': [{'Key': 'Name', 'Value': f'StockAnalysis-{uuid.uuid4()}'}]
                }]
            )
            warmup_info['ec2_instances'].append(instance['Instances'][0]['InstanceId'])

        waiter = self.ec2_client.get_waiter('instance_running')
        waiter.wait(InstanceIds=warmup_info['ec2_instances'])

        warmup_info['scale_ready'] = True
        return {"result": "ok"}

    def terminate_ec2_instances(self):
        if warmup_info['ec2_instances']:
            self.ec2_client.terminate_instances(InstanceIds=warmup_info['ec2_instances'])
            warmup_info['ec2_instances'] = []
        warmup_info['scale_ready'] = False
        termination_info['scale_terminated'] = True
        return {"result": "ok"}

    def get_chart_url(self):
        if self.chart_url is None:
            sig_vars9599 = self.get_sig_vars9599()
            
            if not sig_vars9599["var95"] and not sig_vars9599["var99"]:
                print("Both var95 and var99 lists are empty")  # Debug print
                return "No data available for chart"

            if not sig_vars9599["var95"]:
                sig_vars9599["var95"] = [0]
            if not sig_vars9599["var99"]:
                sig_vars9599["var99"] = [0]

            series_X_var95 = ",".join(map(str, range(len(sig_vars9599["var95"]))))
            series_Y_var95 = ",".join(map(str, sig_vars9599["var95"]))
            series_X_var99 = ",".join(map(str, range(len(sig_vars9599["var99"]))))
            series_Y_var99 = ",".join(map(str, sig_vars9599["var99"]))
            series_all = f"t:{series_X_var95}|{series_Y_var95}|{series_X_var99}|{series_Y_var99}"
            max_x = max(len(sig_vars9599["var95"]), len(sig_vars9599["var99"]))
            min_y = min(sig_vars9599["var95"] + sig_vars9599["var99"])
            max_y = max(sig_vars9599["var95"] + sig_vars9599["var99"])
            axis_range = f"0,0,{max_x}|1,{min_y},{max_y}"
            ch = (
                ImageCharts()
                .cht("lxy").chxt("x,y").chd(series_all)
                .chxr(axis_range).chs("800x800")
                .chco("fdb45c,27c9c2").chdl("var95|var99").chdlp("b")
            )
            self.chart_url = ch.to_url()
        return self.chart_url

    def get_sig_vars9599(self):
        return {
            "var95": analysis_results['var95'] or [],
            "var99": analysis_results['var99'] or []
        }

    def warm_up_lambda(self, runs):
        parallel = range(runs)
        warmup_info['runs'] = runs

        def warmup_request(id):
            try:
                c = http.client.HTTPSConnection(self.lambda_host)
                payload = json.dumps({
                    "signals": self.signals, "close_prices": self.close_prices,
                    "h": self.h, "d": self.d, "t": self.t, "p": self.p
                })
                c.request("POST", self.lambda_path, payload)
                response = c.getresponse()
                data = response.read().decode('utf-8')
                print(data, "from Thread", id)
                response_data = json.loads(data)
                execution_details = response_data.get('executionDetails', {})
                warmup_info['total_billable_time'] += execution_details.get('billed_duration_ms', 0)
                return data
            except IOError:
                print('Failed to open ', self.lambda_host)
            return f"unusual behaviour of {id}"

        with ThreadPoolExecutor() as executor:
            results = list(executor.map(warmup_request, parallel))
        warmup_info['scale_ready'] = True
        return results

def calculate_lambda_cost(duration_ms, billed_duration_ms, memory_size_mb, region="us-east-1"):
    memory_size_mb = int(memory_size_mb)
    request_cost_per_million = 0.20
    duration_cost_per_gb_second = 0.00001667
    duration_seconds = billed_duration_ms / 1000.0
    gb_seconds = (memory_size_mb / 1024.0) * duration_seconds
    duration_cost = gb_seconds * duration_cost_per_gb_second
    request_cost = request_cost_per_million / 1_000_000
    total_cost = duration_cost + request_cost
    return {
        "Total Cost": total_cost,
        "Duration Cost": duration_cost,
        "Request Cost": request_cost
    }
    
    
def calculate_ec2_cost(instance_type, duration_seconds, region="us-east-1"):
    
    ec2_prices = {
        "t2.micro": 0.0116,  # price per hour
    }
    
    if instance_type not in ec2_prices:
        raise ValueError(f"Unknown instance type: {instance_type}")
    
    price_per_hour = ec2_prices[instance_type]
    hours = math.ceil(duration_seconds / 3600)  
    total_cost = hours * price_per_hour
    
    return {
        "Total Cost": total_cost,
        "Hours Billed": hours,
        "Price Per Hour": price_per_hour
    }

# Flask Routes

@app.route('/analyse', methods=['POST'])
def analyse():
    params = request.get_json()
    h, d, t, p = int(params['h']), int(params['d']), params['t'], int(params['p'])
    analysis = StockAnalysisGAE(h, d, t, p)
    result = analysis.run()
    return jsonify(result)

@app.route('/warmup', methods=['POST'])
def warmup():
    params = request.get_json()
    service = params.get('s')
    runs = int(params.get('r', 1))

    analysis = StockAnalysisGAE()
    analysis.fetch_data_and_find_signals()

    if service == "lambda":
        analysis.warm_up_lambda(runs)
        warmup_info['service'] = 'lambda'
        return jsonify({"result": "ok"})
    elif service == "ec2":
        result = analysis.warm_up_ec2(runs)
        warmup_info['service'] = 'ec2'
        return jsonify(result)
    else:
        return jsonify({"error": "Invalid service specified"}), 400

@app.route('/scaled_ready', methods=['GET'])
def scaled_ready():
    return jsonify({"warm": warmup_info['scale_ready']})

@app.route('/get_warmup_cost', methods=['GET'])
def get_warmup_cost():
    if warmup_info['service'] == 'lambda':
        duration_cost_per_gb_second = 0.00001667  # $0.00001667 per GB-second
        request_cost_per_million = 0.20  # $0.20 per 1 million requests
        memory_size_mb = warmup_info.get('memory_size_mb', 128)
        total_duration_seconds = warmup_info['total_billable_time'] / 1000  # Convert ms to seconds
        gb_seconds = (memory_size_mb / 1024.0) * total_duration_seconds
        total_duration_cost = gb_seconds * duration_cost_per_gb_second
        total_request_cost = (warmup_info['runs'] / 1_000_000) * request_cost_per_million
        total_cost = total_duration_cost + total_request_cost
        return jsonify({
            "billable_time_ms": warmup_info['total_billable_time'],
            "billable_time_seconds": total_duration_seconds,
            "gb_seconds": gb_seconds,
            "duration_cost": total_duration_cost,
            "request_cost": total_request_cost,
            "total_cost": total_cost
        })
    
    elif warmup_info['service'] == 'ec2':
        instance_hour_price = 0.0116  # t2.micro price per hour in us-east-1
        start_time = warmup_info.get('start_time')
        if start_time is None:
            return jsonify({"error": "Start time not set for EC2 instances"}), 400
        total_instance_hours = len(warmup_info['ec2_instances']) * (time.time() - start_time) / 3600
        total_instance_hours = math.ceil(total_instance_hours)
        
        total_cost = total_instance_hours * instance_hour_price
        
        return jsonify({
            "instances": len(warmup_info['ec2_instances']),
            "total_instance_hours": total_instance_hours,
            "cost_per_instance_hour": instance_hour_price,
            "total_cost": total_cost
        })
    
    else:
        return jsonify({"error": "No active service"}), 400

@app.route('/get_endpoints', methods=['GET'])
def get_endpoints():
    base_url = request.url_root.rstrip('/')  # Get the base URL of the application
    endpoints = [
        {
            "endpoint": f"curl -X POST -H 'Content-Type: application/json' -d '{{\"s\": \"lambda\", \"r\": 3}}' {base_url}/warmup"
        },
        {
            "endpoint": f"curl -X GET {base_url}/scaled_ready"
        },
        {
            "endpoint": f"curl -X GET {base_url}/get_warmup_cost"
        },
        {
            "endpoint": f"curl -X GET {base_url}/get_endpoints"
        },
        {
            "endpoint": f"curl -X POST -H 'Content-Type: application/json' -d '{{\"h\": 5, \"d\": 10, \"t\": \"Buy\", \"p\": 3}}' {base_url}/analyse"
        },
        {
            "endpoint": f"curl -X GET {base_url}/reset"
        },
        {
            "endpoint": f"curl -X GET {base_url}/terminate"
        },
        {
            "endpoint": f"curl -X GET {base_url}/scaled_terminated"
        },
        {
            "endpoint": f"curl -X GET {base_url}/get_sig_vars9599"
        },
        {
            "endpoint": f"curl -X GET {base_url}/get_avg_vars9599"
        },
        {
            "endpoint": f"curl -X GET {base_url}/get_sig_profit_loss"
        },
        {
            "endpoint": f"curl -X GET {base_url}/get_tot_profit_loss"
        },
        {
            "endpoint": f"curl -X GET {base_url}/get_chart_url"
        },
        {
            "endpoint": f"curl -X GET {base_url}/get_time_cost"
        }
    ]
    return jsonify(endpoints)

@app.route('/reset', methods=['GET'])
def reset():
    global analysis_results
    analysis_results = {
        "var95": [], "var99": [], "profit_loss": [],
        "avg_var95": 0, "avg_var99": 0, "total_profit_loss": 0,
        "chart_url": "", "time_cost": 0,
        "lambda_duration_ms": 0, "lambda_billed_duration_ms": 0,
        "lambda_memory_size_mb": 128
    }
    return jsonify({"result": "ok"})

@app.route('/terminate', methods=['GET'])
def terminate():
    if warmup_info['service'] == 'lambda':
        warmup_info['scale_ready'] = False
        termination_info['scale_terminated'] = True
        return jsonify({"result": "ok"})
    elif warmup_info['service'] == 'ec2':
        analysis = StockAnalysisGAE()
        return analysis.terminate_ec2_instances()
    else:
        return jsonify({"error": "No active service to terminate"}), 400

@app.route('/resources_terminated', methods=['GET'])
def resources_terminated():
    return jsonify({"terminated": termination_info.get('resources_terminated', False)})


@app.route('/get_sig_vars9599', methods=['GET'])
def get_sig_vars9599():
    return jsonify({
        "var95": analysis_results['var95'],
        "var99": analysis_results['var99']
    })

@app.route('/get_avg_vars9599', methods=['GET'])
def get_avg_vars9599():
    return jsonify({
        "var95": analysis_results['avg_var95'],
        "var99": analysis_results['avg_var99']
    })

@app.route('/get_sig_profit_loss', methods=['GET'])
def get_sig_profit_loss():
    return jsonify({
        "profit_loss": analysis_results['profit_loss']
    })

@app.route('/get_tot_profit_loss', methods=['GET'])
def get_tot_profit_loss():
    return jsonify({
        "profit_loss": analysis_results['total_profit_loss']
    })

@app.route('/get_chart_url', methods=['GET'])
def chart_url():
    analysis = StockAnalysisGAE()
    analysis.fetch_data_and_find_signals()
    url = analysis.get_chart_url()
    return jsonify({"url": url})

@app.route('/get_time_cost', methods=['GET'])
def get_time_cost():
    service = warmup_info.get('service')
    
    if service == 'lambda':
        lambda_cost_details = calculate_lambda_cost(
            analysis_results['lambda_duration_ms'],
            analysis_results['lambda_billed_duration_ms'],
            analysis_results['lambda_memory_size_mb']
        )
        return jsonify({
            "service": "lambda",
            "execution_time": analysis_results['time_cost'],
            "lambda_cost": lambda_cost_details
        })
    elif service == 'ec2':
        start_time = warmup_info.get('start_time')
        if start_time is None:
            return jsonify({"error": "EC2 start time not available"}), 400
        
        duration_seconds = time.time() - start_time
        ec2_cost_details = calculate_ec2_cost(
            EC2_INSTANCE_TYPE, 
            duration_seconds
        )
        return jsonify({
            "service": "ec2",
            "execution_time": duration_seconds,
            "ec2_cost": ec2_cost_details
        })
    else:
        return jsonify({"error": "No active service or unknown service type"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

