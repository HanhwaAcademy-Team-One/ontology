"""같은 변수를 이용해 관계를 연결하고, FILTER로 결과를 좁힙니다."""

from pathlib import Path

from rdflib import Graph


def main():
    ttl_path = Path(__file__).resolve().parents[2] / "data" / "cafe.ttl"
    graph = Graph()
    graph.parse(ttl_path, format="turtle")

    # 질문 1: 누가 어떤 음료를 구매했나요?
    all_purchases_query = """
        PREFIX ex: <https://example.org/cafe#>

        SELECT ?customerName ?drinkName
        WHERE {
            ?customer a ex:Customer .
            ?customer ex:name ?customerName .
            ?customer ex:buys ?drink .
            ?drink a ex:Drink .
            ?drink ex:name ?drinkName .
        }
        ORDER BY ?customer ?drink
    """

    print("전체 구매 목록:")
    for customer_name, drink_name in graph.query(all_purchases_query):
        print(f"{customer_name} → {drink_name}")

    # 질문 2: 카페인이 있는 음료의 구매만 보여주세요.
    caffeine_query = """
        PREFIX ex: <https://example.org/cafe#>

        SELECT ?customerName ?drinkName
        WHERE {
            ?customer a ex:Customer .
            ?customer ex:name ?customerName .
            ?customer ex:buys ?drink .
            ?drink a ex:Drink .
            ?drink ex:name ?drinkName .
            ?drink ex:hasCaffeine ?hasCaffeine .

            FILTER(?hasCaffeine = true)
        }
        ORDER BY ?customer ?drink
    """

    print("\n카페인 음료 구매 목록:")
    for customer_name, drink_name in graph.query(caffeine_query):
        print(f"{customer_name} → {drink_name}")


if __name__ == "__main__":
    main()
