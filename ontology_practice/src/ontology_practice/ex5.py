"""domain과 range로 관계 양쪽 개체의 종류를 추론합니다."""

from pathlib import Path

from owlrl import DeductiveClosure, OWLRL_Semantics
from rdflib import RDF, Graph, Namespace


def show_types(graph, ex):
    # 두 문장이 현재 그래프에 있는지 확인합니다.
    customer_fact = (ex.C002, RDF.type, ex.Customer)
    drink_fact = (ex.drink3, RDF.type, ex.Drink)
    print(f"'지수는 손님이다' 문장이 있나요? {customer_fact in graph}")
    print(f"'라테 한 잔은 음료다' 문장이 있나요? {drink_fact in graph}")


def main():
    ttl_path = Path(__file__).resolve().parents[2] / "data" / "cafe_domain_range.ttl"
    graph = Graph()
    graph.parse(ttl_path, format="turtle")
    ex = Namespace("https://example.org/cafe#")

    print("추론 전:")
    show_types(graph, ex)

    # 추론기가 buys 관계의 domain과 range 정의를 적용합니다.
    DeductiveClosure(OWLRL_Semantics).expand(graph)

    print("\n추론 후:")
    show_types(graph, ex)


if __name__ == "__main__":
    main()
