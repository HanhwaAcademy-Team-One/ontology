"""클래스 계층을 정의하고, 추론 전후의 조회 결과를 비교합니다."""

from pathlib import Path

from owlrl import DeductiveClosure, OWLRL_Semantics
from rdflib import RDF, Graph, Namespace


def show_drinks(graph):
    # 음료(Drink)로 분류되어 있는 대상을 조회합니다.
    query = """
        PREFIX ex: <https://example.org/cafe#>

        SELECT DISTINCT ?name
        WHERE {
            ?drink a ex:Drink .
            ?drink ex:name ?name .
        }
        ORDER BY ?name
    """
    names = [str(name) for (name,) in graph.query(query)]
    print(f"음료 조회 결과: {names}")


def main():
    ttl_path = Path(__file__).resolve().parents[2] / "data" / "cafe_reasoning.ttl"
    graph = Graph()
    graph.parse(ttl_path, format="turtle")
    ex = Namespace("https://example.org/cafe#")

    # Turtle의 'a'는 RDF.type과 같습니다.
    drink_fact = (ex.drink1, RDF.type, ex.Drink)

    print("추론 전:")
    print(f"'drink1은 음료다' 문장이 그래프에 있나요? {drink_fact in graph}")
    show_drinks(graph)

    # OWL 2 RL 추론기가 클래스 계층 등의 의미를 적용합니다.
    # 결과는 메모리의 그래프에 추가됩니다. 원본 Turtle 파일은 덮어쓰지 않습니다.
    DeductiveClosure(OWLRL_Semantics).expand(graph)

    print("\n추론 후:")
    print(f"'drink1은 음료다' 문장이 그래프에 있나요? {drink_fact in graph}")
    show_drinks(graph)


if __name__ == "__main__":
    main()
