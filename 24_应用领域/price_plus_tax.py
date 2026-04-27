# -*- coding: utf-8 -*-

"""

算法实现：24_应用领域 / price_plus_tax



本文件实现 price_plus_tax 相关的算法功能。

"""



from typing import Tuple





def calculate_vat(price: float, vat_rate: float = 0.13) -> Tuple[float, float]:

    """

    增值税计算



    参数：

        price: 不含税价格

        vat_rate: 增值税率（默认13%）



    返回：(税后价格, 税额)

    """

    tax_amount = price * vat_rate

    total_price = price + tax_amount

    return total_price, tax_amount





def calculate_vat_from_total(total: float, vat_rate: float = 0.13) -> Tuple[float, float]:

    """

    从含税价反算不含税价和税额



    参数：

        total: 含税总价格

        vat_rate: 增值税率



    返回：(不含税价格, 税额)

    """

    price = total / (1 + vat_rate)

    tax_amount = total - price

    return price, tax_amount





def calculate_sales_tax(price: float, tax_rate: float = 0.08) -> Tuple[float, float]:

    """

    销售税计算



    参数：

        price: 商品价格

        tax_rate: 销售税率



    返回：(含税价格, 税额)

    """

    tax_amount = price * tax_rate

    return price + tax_amount, tax_amount





def calculate_multiple_items(items: list, vat_rate: float = 0.13,

                             discount: float = 0.0) -> dict:

    """

    多商品计算



    参数：

        items: 商品列表，每项为 (名称, 单价, 数量)

        vat_rate: 增值税率

        discount: 整单折扣率



    返回：账单明细

    """

    subtotal = 0.0

    details = []



    for name, unit_price, quantity in items:

        item_total = unit_price * quantity

        subtotal += item_total

        details.append({

            'name': name,

            'unit_price': unit_price,

            'quantity': quantity,

            'item_total': item_total

        })



    # 折扣

    discount_amount = subtotal * discount

    subtotal_after_discount = subtotal - discount_amount



    # 税额

    vat_amount = subtotal_after_discount * vat_rate

    total = subtotal_after_discount + vat_amount



    return {

        'items': details,

        'subtotal': subtotal,

        'discount': discount_amount,

        'subtotal_after_discount': subtotal_after_discount,

        'vat_rate': vat_rate,

        'vat_amount': vat_amount,

        'total': total

    }





def price_with_service_charge(base_price: float,

                              service_rate: float = 0.10,

                              vat_rate: float = 0.06) -> Tuple[float, float, float]:

    """

    含服务费的计算



    参数：

        base_price: 基价

        service_rate: 服务费率

        vat_rate: 增值税税率



    返回：(服务费, 税额, 总价)

    """

    service_charge = base_price * service_rate

    taxable_amount = base_price + service_charge

    vat = taxable_amount * vat_rate

    total = taxable_amount + vat



    return service_charge, vat, total





def calculate_tip_and_split(total_amount: float,

                            tip_percent: float = 0.15,

                            num_people: int = 1) -> dict:

    """

    计算小费和分账



    参数：

        total_amount: 总金额（含税）

        tip_percent: 小费比例

        num_people: 分账人数



    返回：分账明细

    """

    tip_amount = total_amount * tip_percent

    total_with_tip = total_amount + tip_amount

    per_person = total_with_tip / num_people



    return {

        'original_total': total_amount,

        'tip_percent': tip_percent,

        'tip_amount': tip_amount,

        'total_with_tip': total_with_tip,

        'num_people': num_people,

        'per_person': per_person

    }





def format_currency(amount: float, symbol: str = "¥") -> str:

    """

    格式化货币显示



    参数：

        amount: 金额

        symbol: 货币符号



    返回：格式化字符串

    """

    return f"{symbol}{amount:,.2f}"





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 商品价格与税费计算测试 ===\n")



    # 基本增值税计算

    price = 100.0

    vat_rate = 0.13



    total, tax = calculate_vat(price, vat_rate)

    print(f"增值税计算：")

    print(f"  不含税价格: {format_currency(price)}")

    print(f"  税率: {vat_rate*100}%")

    print(f"  税额: {format_currency(tax)}")

    print(f"  含税价格: {format_currency(total)}")



    print()



    # 反算

    print("含税价反算：")

    total = 113.0

    price, tax = calculate_vat_from_total(total, vat_rate)

    print(f"  含税价格: {format_currency(total)}")

    print(f"  不含税: {format_currency(price)}")

    print(f"  税额: {format_currency(tax)}")



    print()



    # 多商品计算

    print("多商品购物车：")

    cart = [

        ("可口可乐", 3.00, 2),

        ("薯片", 6.50, 3),

        ("面包", 5.00, 1),

    ]



    bill = calculate_multiple_items(cart, vat_rate=0.13, discount=0.05)



    print(f"  小计: {format_currency(bill['subtotal'])}")

    print(f"  折扣(5%): -{format_currency(bill['discount'])}")

    print(f"  折后小计: {format_currency(bill['subtotal_after_discount'])}")

    print(f"  增值税(13%): {format_currency(bill['vat_amount'])}")

    print(f"  总计: {format_currency(bill['total'])}")



    print()



    # 小费分账

    print("小费和分账：")

    receipt = calculate_tip_and_split(bill['total'], tip_percent=0.15, num_people=3)

    print(f"  原始金额: {format_currency(receipt['original_total'])}")

    print(f"  小费(15%): {format_currency(receipt['tip_amount'])}")

    print(f"  含小费总计: {format_currency(receipt['total_with_tip'])}")

    print(f"  每人: {format_currency(receipt['per_person'])}")



    print()

    print("说明：")

    print("  - 不同国家/地区的税率不同")

    print("  - 中国增值税有13%、9%、6%等档次")

    print("  - 美国销售税由各州自行规定")

