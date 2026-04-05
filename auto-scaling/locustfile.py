from locust import HttpUser, task, between, events
import random, string

def rand_email():
    return ''.join(random.choices(string.ascii_lowercase, k=8)) + "@loadtest.com"

class ShopUser(HttpUser):
    wait_time = between(1, 3)
    token = None

    def on_start(self):
        # Register + login a unique user per simulated user
        email = rand_email()
        self.client.post("/api/register", json={
            "name": "Load Tester",
            "email": email,
            "password": "test1234"
        })
        self.client.post("/api/login", json={
            "email": email,
            "password": "test1234"
        })

    @task(5)
    def browse_products(self):
        self.client.get("/api/products")

    @task(3)
    def view_homepage(self):
        self.client.get("/")

    @task(3)
    def view_product(self):
        pid = random.randint(1, 24)
        self.client.get(f"/api/products/{pid}")

    @task(2)
    def search_products(self):
        terms = ["merino", "keyboard", "yoga", "coffee", "serum", "book"]
        self.client.get(f"/api/search?q={random.choice(terms)}")

    @task(2)
    def get_reviews(self):
        pid = random.randint(1, 24)
        self.client.get(f"/api/products/{pid}/reviews")

    @task(2)
    def post_review(self):
        pid = random.randint(1, 24)
        self.client.post(f"/api/products/{pid}/reviews", json={
            "rating": random.randint(3, 5),
            "comment": random.choice([
                "Great product, highly recommend!",
                "Good quality for the price.",
                "Exactly as described.",
                "Fast delivery, works perfectly.",
                "Would buy again."
            ])
        })

    @task(2)
    def add_to_cart(self):
        self.client.post("/api/cart", json={
            "product_id": random.randint(1, 24),
            "quantity": random.randint(1, 3)
        })

    @task(1)
    def place_order(self):
        items = [{"id": random.randint(1,24), "name": "Product", "price": 49.99, "qty": 1}
                 for _ in range(random.randint(1, 3))]
        total = sum(i["price"] * i["qty"] for i in items)
        self.client.post("/api/orders", json={
            "items": items,
            "total": str(round(total, 2)),
            "shipping_address": "Test User, 123 Load St, Test City"
        })

    @task(1)
    def view_orders(self):
        self.client.get("/api/orders")

    @task(1)
    def health_check(self):
        self.client.get("/health")
