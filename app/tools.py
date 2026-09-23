def get_order_status(order_id: str) -> str:
    orders = {
        "1001": "已支付,正在配送",
        "1002": "待支付",
        "1003": "已完成"
    }
    return orders.get(order_id, "没有找到这个订单")