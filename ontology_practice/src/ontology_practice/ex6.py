"""역관계를 추론하고 음료에서 구매자로 연결을 따라갑니다."""

from pathlib import Path

from owlrl import DeductiveClosure, OWLRL_Semantics
from rdflib import Graph


def show_buyers(graph):
    # boughtBy 관계만 사용해 아메리카노 한 잔의 구매자를 찾습니다.
    query = """
        PREFIX ex: <https://example.org/cafe#>

        SELECT DISTINCT ?name
        WHERE {
            ex:drink1 ex:boughtBy ?customer .
            ?customer ex:name ?name .
        }
        ORDER BY ?name
    """
    names = [str(name) for (name,) in graph.query(query)]
    print(f"boughtBy 관계로 찾은 구매자: {names}")


def main():
    ttl_path = Path(__file__).resolve().parents[2] / "data" / "cafe_inverse.ttl"
    graph = Graph()
    graph.parse(ttl_path, format="turtle")

    print("추론 전:")
    show_buyers(graph)

    DeductiveClosure(OWLRL_Semantics).expand(graph)

    print("\n추론 후:")
    show_buyers(graph)


if __name__ == "__main__":
    main()
