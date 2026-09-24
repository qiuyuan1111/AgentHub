from app.rag import search_knowledge_base

def get_order_status(order_id: str) -> str:
    orders = {
        "1001": "已支付,正在配送",
        "1002": "待支付",
        "1003": "已完成"
    }
    return orders.get(order_id, "没有找到这个订单")

def get_product_stock(product_id: str) -> str:
    products = {
        "P001":"库存25件",
        "P002":"库存0件",
        "P003":"库存102件"
    }

    return products.get(product_id, "没有找到这个商品")
TOOL_FUNCTIONS = {
    "get_order_status":get_order_status,
    "get_product_stock":get_product_stock,
    "search_knowledge_base":search_knowledge_base
}