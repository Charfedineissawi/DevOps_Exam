from flask import Flask, render_template, request, redirect, url_for
from prometheus_client import Counter, Gauge, Summary, generate_latest, CONTENT_TYPE_LATEST
import time
import functools

app = Flask(__name__)

# Updated product structure with code, description, and price
products = {
    1: {'description': 'Apple', 'price': 0.5},
    2: {'description': 'Banana', 'price': 0.3},
    3: {'description': 'Orange', 'price': 0.4},
    4: {'description': 'Mango', 'price': 1.0}
}

# Prometheus metrics
request_counter = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint'])
sales_counter = Counter('sales_total', 'Total Sales', ['product'])
sales_amount_counter = Counter('sales_amount_total', 'Total Sales Amount', ['product'])
active_products_gauge = Gauge('active_products', 'Number of active products')

# New metrics as requested
views_by_product = Counter('views_by_product', 'Views By Product', ['product'])
sales_duration = Summary('sales_duration', 'Sales Duration')

# Decorator for measuring endpoint execution time
def timing_decorator(metric):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = f(*args, **kwargs)
            execution_time = time.time() - start_time
            metric.observe(execution_time)
            return result
        return wrapper
    return decorator

# Update the active products gauge
active_products_gauge.set(len(products))

sales_history = []

@app.route('/')
def index():
    request_counter.labels(method='GET', endpoint='/').inc()
    return render_template('index.html', products=products)

@app.route('/calculate', methods=['POST'])
def calculate():
    request_counter.labels(method='POST', endpoint='/calculate').inc()
    product_code = int(request.form['product'])
    product_info = products.get(product_code)

    if product_info is None:
        return "Invalid product", 400

    # Track views by product
    views_by_product.labels(product=product_info['description']).inc()

    quantity = int(request.form['quantity'])
    total = quantity * product_info['price']
    sales_history.append({
        'product': product_info['description'],
        'quantity': quantity,
        'total': total
    })
    # Update Prometheus metrics for this sale
    sales_counter.labels(product=product_info['description']).inc(quantity)
    sales_amount_counter.labels(product=product_info['description']).inc(total)
    
    return render_template('result.html', product=product_info['description'], quantity=quantity, total=total)

@app.route('/sales')
@timing_decorator(sales_duration)
def sales():
    request_counter.labels(method='GET', endpoint='/sales').inc()
    return render_template('sales.html', sales=sales_history)

@app.route('/back')
def back():
    return redirect(url_for('index'))

@app.route('/metrics')
def metrics():
    request_counter.labels(method='GET', endpoint='/metrics').inc()
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')