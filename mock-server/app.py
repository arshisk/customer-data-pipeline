import json
import os
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

# ─── App Setup ───────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

# ─── Load Customers from JSON file ───────────────────────────
# Build the path to customers.json relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CUSTOMERS_FILE = os.path.join(BASE_DIR, "data", "customers.json")

def load_customers():
    """Read and return all customers from the JSON file."""
    with open(CUSTOMERS_FILE, "r") as f:
        return json.load(f)


# ─── Routes ──────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint — used by Docker and assessors to verify service is up."""
    return jsonify({
        "status": "healthy",
        "service": "mock-server",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 200


@app.route("/api/customers", methods=["GET"])
def get_customers():
    """
    Return paginated list of customers.
    Query params:
      - page  (int, default 1)
      - limit (int, default 10)
    """
    # Read page and limit from query params, with defaults
    try:
        page  = int(request.args.get("page",  1))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        return jsonify({"error": "page and limit must be integers"}), 400

    # Basic validation
    if page < 1 or limit < 1:
        return jsonify({"error": "page and limit must be greater than 0"}), 400

    customers = load_customers()
    total     = len(customers)

    # Calculate slice indexes
    start = (page - 1) * limit
    end   = start + limit

    # Slice the list for this page
    paginated = customers[start:end]

    # Calculate total pages
    total_pages = (total + limit - 1) // limit

    return jsonify({
        "data":        paginated,
        "total":       total,
        "page":        page,
        "limit":       limit,
        "total_pages": total_pages
    }), 200


@app.route("/api/customers/<customer_id>", methods=["GET"])
def get_customer(customer_id):
    """
    Return a single customer by customer_id.
    Returns 404 if not found.
    """
    customers = load_customers()

    # Search for customer with matching ID
    customer = next(
        (c for c in customers if c["customer_id"] == customer_id),
        None
    )

    if customer is None:
        return jsonify({
            "error":       "Customer not found",
            "customer_id": customer_id
        }), 404

    return jsonify(customer), 200


# ─── Run ─────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)