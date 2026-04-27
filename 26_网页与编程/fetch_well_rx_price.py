# -*- coding: utf-8 -*-
"""
算法实现：26_网页与编程 / fetch_well_rx_price

本文件实现 fetch_well_rx_price 相关的算法功能。
"""

if __name__ == "__main__":
    # Enter a drug name and a zip code
    drug_name = input("Enter drug name: ").strip()
    zip_code = input("Enter zip code: ").strip()

    pharmacy_price_list: list | None = fetch_pharmacy_and_price_list(
        drug_name, zip_code
    )

    if pharmacy_price_list:
        print(f"\nSearch results for {drug_name} at location {zip_code}:")
        for pharmacy_price in pharmacy_price_list:
            name = pharmacy_price["pharmacy_name"]
            price = pharmacy_price["price"]

            print(f"Pharmacy: {name} Price: {price}")
    else:
        print(f"No results found for {drug_name}")
