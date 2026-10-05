"""Turtle 파일을 읽고, 관계를 따라 조회하는 첫 RDF 실습입니다."""

from pathlib import Path

from rdflib import Graph, Namespace


def main():
    # 현재 터미널 위치와 관계없이 이 스크립트를 기준으로 파일을 찾습니다.
    ttl_path = Path(__file__).resolve().parents[2] / "data" / "cafe.ttl"

    # RDFLib가 Turtle 문장을 읽어 RDF 그래프로 만듭니다.
    graph = Graph()
    graph.parse(ttl_path, format="turtle")
    ex = Namespace("https://example.org/cafe#")

    print(f"읽은 파일: {ttl_path.name}")
    print(f"트리플 수: {len(graph)}")

    # C001에서 buys 관계로 연결된 음료를 찾습니다.
    customer = ex.C001
    customer_name = graph.value(customer, ex.name)

    print("\n민수의 구매 목록:")
    for drink in sorted(graph.objects(customer, ex.buys), key=str):
        drink_name = graph.value(drink, ex.name)
        has_caffeine = graph.value(drink, ex.hasCaffeine).toPython()
        caffeine_text = "있음" if has_caffeine else "없음"
        print(f"[C001] {customer_name}: {drink_name} (카페인 {caffeine_text})")

    # SPARQL은 RDF 그래프에 질문하는 언어입니다.
    # 아래 질문은 '카페인이 있는 음료를 구매한 손님의 ID와 이름은?'입니다.
    # 저장된 사실을 조회하며, OWL 추론기를 실행하는 예제는 아닙니다.
    query = """
        PREFIX ex: <https://example.org/cafe#>

        SELECT DISTINCT ?customer ?name
        WHERE {
            ?customer a ex:Customer .
            ?customer ex:name ?name .
            ?customer ex:buys ?drink .
            ?drink ex:hasCaffeine true .
        }
        ORDER BY ?customer
    """

    print("\n카페인 음료 구매자 (SPARQL 조회):")
    for customer_id, name in graph.query(query):
        short_id = str(customer_id).removeprefix(str(ex))
        print(f"[{short_id}] {name}")


if __name__ == "__main__":
    main()
