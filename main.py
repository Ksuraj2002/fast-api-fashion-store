from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI()

# data

products = [
    {"id": 1, "name": "Casual Shirt", "brand": "Zara", "category": "Shirt", "price": 1500, "sizes_available": ["S","M","L"], "in_stock": True},
    {"id": 2, "name": "Slim Jeans", "brand": "Levis", "category": "Jeans", "price": 2500, "sizes_available": ["M","L"], "in_stock": True},
    {"id": 3, "name": "Running Shoes", "brand": "Nike", "category": "Shoes", "price": 4000, "sizes_available": ["8","9","10"], "in_stock": False},
    {"id": 4, "name": "Summer Dress", "brand": "H&M", "category": "Dress", "price": 2000, "sizes_available": ["S","M"], "in_stock": True},
    {"id": 5, "name": "Leather Jacket", "brand": "Zara", "category": "Jacket", "price": 5000, "sizes_available": ["M","L"], "in_stock": False},
    {"id": 6, "name": "Formal Shirt", "brand": "Arrow", "category": "Shirt", "price": 1800, "sizes_available": ["S","M","L","XL"], "in_stock": True}
]

orders = []
wishlist = []
order_counter = 1

def find_product(product_id: int):
    return next((p for p in products if p["id"] == product_id), None)


def calculate_order_total(price, quantity, gift_wrap, season_sale=False):
    base = price * quantity
    breakdown = {
        "base": base,
        "season_discount": 0,
        "bulk_discount": 0,
        "gift_wrap_cost": 0
    }

    if season_sale:
        d = base * 0.15
        breakdown["season_discount"] = d
        base -= d

    if quantity >= 5:
        d = base * 0.05
        breakdown["bulk_discount"] = d
        base -= d

    if gift_wrap:
        wrap = 50 * quantity
        breakdown["gift_wrap_cost"] = wrap
        base += wrap

    breakdown["final_total"] = base
    return breakdown


def filter_products_logic(category=None, brand=None, max_price=None, in_stock=None):
    result = products

    if category is not None:
        result = [p for p in result if p["category"].lower() == category.lower()]
    if brand is not None:
        result = [p for p in result if p["brand"].lower() == brand.lower()]
    if max_price is not None:
        result = [p for p in result if p["price"] <= max_price]
    if in_stock is not None:
        result = [p for p in result if p["in_stock"] == in_stock]

    return result


# MODELS

class OrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_id: int = Field(..., gt=0)
    size: str = Field(..., min_length=1)
    quantity: int = Field(..., gt=0, le=10)
    delivery_address: str = Field(..., min_length=10)
    gift_wrap: bool = False
    season_sale: bool = False


class NewProduct(BaseModel):
    name: str = Field(..., min_length=2)
    brand: str = Field(..., min_length=2)
    category: str = Field(..., min_length=2)
    price: int = Field(..., gt=0)
    sizes_available: List[str]
    in_stock: bool = True


class WishlistOrderRequest(BaseModel):
    customer_name: str
    delivery_address: str = Field(..., min_length=10)

# BASIC ROUTES

@app.get("/")
def home():
    return {"message": "Welcome to TrendZone Fashion Store"}


@app.get("/products/summary")
def summary():
    in_stock = sum(p["in_stock"] for p in products)
    brands = list(set(p["brand"] for p in products))

    category_count = {}
    for p in products:
        category_count[p["category"]] = category_count.get(p["category"], 0) + 1

    return {
        "total": len(products),
        "in_stock": in_stock,
        "out_of_stock": len(products) - in_stock,
        "brands": brands,
        "category_count": category_count
    }


@app.get("/products")
def get_products():
    return {
        "products": products,
        "total": len(products),
        "in_stock_count": sum(p["in_stock"] for p in products)
    }





@app.get("/products/filter")
def filter_products(category: Optional[str] = None,
                    brand: Optional[str] = None,
                    max_price: Optional[int] = None,
                    in_stock: Optional[bool] = None):
    result = filter_products_logic(category, brand, max_price, in_stock)
    return {"results": result, "total": len(result)}



@app.get("/products/search")
def search_products(keyword: str):
    result = [
        p for p in products
        if keyword.lower() in p["name"].lower()
        or keyword.lower() in p["brand"].lower()
        or keyword.lower() in p["category"].lower()
    ]

    if not result:
        return {"message": "No products found"}

    return {"results": result, "total_found": len(result)}



@app.get("/products/sort")
def sort_products(sort_by: str = "price", order: str = "asc"):
    if sort_by not in ["price", "name", "brand", "category"]:
        raise HTTPException(400, "Invalid sort field")

    reverse = order == "desc"

    result = sorted(products, key=lambda x: x[sort_by], reverse=reverse)

    return {"sorted_by": sort_by, "order": order, "results": result}



@app.get("/products/page")
def paginate(page: int = 1, limit: int = 3):
    start = (page - 1) * limit
    end = start + limit

    total_pages = (len(products) + limit - 1) // limit

    return {
        "page": page,
        "total_pages": total_pages,
        "results": products[start:end]
    }



@app.get("/products/browse")
def browse_products(
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    in_stock: Optional[bool] = None,
    max_price: Optional[int] = None,
    sort_by: str = "price",
    order: str = "asc",
    page: int = 1,
    limit: int = 3
):
    result = products

    # FILTER + SEARCH
    if keyword:
        result = [p for p in result if keyword.lower() in p["name"].lower()
                  or keyword.lower() in p["brand"].lower()
                  or keyword.lower() in p["category"].lower()]

    if category:
        result = [p for p in result if p["category"].lower() == category.lower()]

    if brand:
        result = [p for p in result if p["brand"].lower() == brand.lower()]

    if in_stock is not None:
        result = [p for p in result if p["in_stock"] == in_stock]

    if max_price is not None:
        result = [p for p in result if p["price"] <= max_price]

    # SORT
    if sort_by not in ["price", "name", "brand", "category"]:
        raise HTTPException(400, "Invalid sort field")

    result = sorted(result, key=lambda x: x[sort_by], reverse=(order == "desc"))

    # PAGINATION
    start = (page - 1) * limit
    end = start + limit
    total_pages = (len(result) + limit - 1) // limit

    return {
        "total_results": len(result),
        "page": page,
        "total_pages": total_pages,
        "results": result[start:end]
    }


@app.get("/products/{product_id}")
def get_product(product_id: int):
    p = find_product(product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    return p


@app.get("/orders")
def get_orders():
    return {
        "orders": orders,
        "total": len(orders),
        "total_revenue": sum(o.get("total", 0) for o in orders)
    }


@app.post("/orders")
def create_order(order: OrderRequest):
    global order_counter

    p = find_product(order.product_id)
    if not p:
        raise HTTPException(404, "Product not found")

    if not p["in_stock"]:
        raise HTTPException(400, "Out of stock")

    if order.size not in p["sizes_available"]:
        raise HTTPException(400, f"Available sizes: {p['sizes_available']}")

    breakdown = calculate_order_total(p["price"], order.quantity, order.gift_wrap, order.season_sale)

    new_order = {
        "order_id": order_counter,
        "customer_name": order.customer_name,
        "product": p["name"],
        "quantity": order.quantity,
        "total": breakdown["final_total"]
    }

    orders.append(new_order)
    order_counter += 1

    return new_order



@app.post("/products", status_code=201)
def add_product(product: NewProduct):
    for p in products:
        if p["name"].lower() == product.name.lower() and p["brand"].lower() == product.brand.lower():
            raise HTTPException(400, "Product exists")

    new_id = max(p["id"] for p in products) + 1
    new_product = product.dict()
    new_product["id"] = new_id
    products.append(new_product)

    return new_product


@app.put("/products/{product_id}")
def update_product(product_id: int, price: Optional[int] = None, in_stock: Optional[bool] = None):
    p = find_product(product_id)
    if not p:
        raise HTTPException(404, "Not found")

    if price is not None:
        p["price"] = price
    if in_stock is not None:
        p["in_stock"] = in_stock

    return p


@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    p = find_product(product_id)
    if not p:
        raise HTTPException(404, "Not found")

    if any(o["product"] == p["name"] for o in orders):
        raise HTTPException(400, "Cannot delete product with orders")

    products.remove(p)
    return {"message": "Deleted"}



@app.post("/wishlist/add")
def add_wishlist(customer_name: str, product_id: int, size: str):
    p = find_product(product_id)
    if not p:
        raise HTTPException(404, "Product not found")

    if size not in p["sizes_available"]:
        raise HTTPException(400, f"Sizes: {p['sizes_available']}")

    if any(w["customer_name"] == customer_name and w["product_id"] == product_id and w["size"] == size for w in wishlist):
        raise HTTPException(400, "Already added")

    wishlist.append({"customer_name": customer_name, "product_id": product_id, "size": size})
    return {"message": "Added"}


@app.get("/wishlist")
def get_wishlist():
    total = 0
    result = []

    for w in wishlist:
        p = find_product(w["product_id"])
        if p:
            total += p["price"]
            result.append({**w, "price": p["price"], "name": p["name"]})

    return {"items": result, "total_value": total}


@app.delete("/wishlist/remove")
def remove_wishlist(customer_name: str, product_id: int):
    for w in wishlist:
        if w["customer_name"] == customer_name and w["product_id"] == product_id:
            wishlist.remove(w)
            return {"message": "Removed"}

    raise HTTPException(404, "Not found")


@app.post("/wishlist/order-all", status_code=201)
def order_all(req: WishlistOrderRequest):
    global order_counter

    user_items = [w for w in wishlist if w["customer_name"] == req.customer_name]

    if not user_items:
        raise HTTPException(400, "Wishlist empty")

    created = []
    total = 0

    for w in user_items:
        p = find_product(w["product_id"])
        if not p or not p["in_stock"]:
            continue

        cost = p["price"]

        order = {
            "order_id": order_counter,
            "customer_name": req.customer_name,
            "product": p["name"],
            "quantity": 1,
            "total": cost
        }

        orders.append(order)
        created.append(order)
        total += cost
        order_counter += 1

    wishlist[:] = [w for w in wishlist if w["customer_name"] != req.customer_name]

    return {"orders": created, "grand_total": total}