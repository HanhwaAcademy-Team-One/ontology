"""같은 관계가 이어질 때 추이성을 이용해 새로운 연결을 추론합니다."""

from pathlib import Path

from owlrl import DeductiveClosure, OWLRL_Semantics
from rdflib import Graph


def show_regions(graph):
    query = """
        PREFIX ex: <https://example.org/cafe#>

        SELECT DISTINCT ?name
        WHERE {
            ex:cafe1 ex:partOf ?region .
            ?region ex:name ?name .
        }
        ORDER BY ?name
    """
    names = [str(name) for (name,) in graph.query(query)]
    print(f"카페가 속한 지역: {names}")


def main():
    ttl_path = Path(__file__).resolve().parents[2] / "data" / "cafe_transitive.ttl"
    graph = Graph()
    graph.parse(ttl_path, format="turtle")

    print("추론 전:")
    show_regions(graph)

    DeductiveClosure(OWLRL_Semantics).expand(graph)

    print("\n추론 후:")
    show_regions(graph)


if __name__ == "__main__":
    main()
