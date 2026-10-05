class Customer:
    def __init__(self, customer_id, name):
        self.customer_id = customer_id
        self.name = name
        self.purchased_drinks = []

    def buy(self, drink):
        self.purchased_drinks.append(drink)


class Drink:
    def __init__(self, product_name, has_caffeine):
        self.product_name = product_name
        self.has_caffeine = has_caffeine


# 구체적인 대상 만들기
minsu = Customer("C001", "민수")
americano = Drink("아메리카노", True)
powerade = Drink("파워에이드", False)
# 대상 사이에 관계 만들기
minsu.buy(americano)
minsu.buy(powerade)
# 관계를 따라가며 정보 확인하기
for drink in minsu.purchased_drinks:
    print(f"[{minsu.customer_id}] {minsu.name}는 {"카페인이 있는" if drink.has_caffeine else "카페인이 없는"} {drink.product_name}를 구매했다.")

# 처음에는 카페인 음료 구매 여부를 False로 둔다.
is_caffeine_buyer = False

for drink in minsu.purchased_drinks:
    if drink.has_caffeine:
        is_caffeine_buyer = True
        break  # 하나라도 찾았으므로 검색을 끝낸다.

if is_caffeine_buyer:
    print(f"[{minsu.customer_id}] {minsu.name}는 카페인 음료 구매자다.")