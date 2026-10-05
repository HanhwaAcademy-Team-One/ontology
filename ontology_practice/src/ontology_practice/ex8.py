"""입력 데이터를 검사하고, 검사에 통과한 데이터만 파일로 저장합니다."""

from pathlib import Path

from pyshacl import validate
from rdflib import RDF, Graph
from rdflib.namespace import SH


def validate_and_save(input_path, shapes, output_path):
    graph = Graph()
    graph.parse(input_path, format="turtle")

    # conforms는 검사 통과 여부, report는 발견한 오류를 담은 RDF 그래프입니다.
    conforms, report, _ = validate(
        data_graph=graph,
        shacl_graph=shapes,
        inference="none",
    )

    print(f"\n입력: {input_path.name}")
    print(f"검사 통과: {conforms}")

    if not conforms:
        errors = []
        for result in report.subjects(RDF.type, SH.ValidationResult):
            focus = report.value(result, SH.focusNode)
            path = report.value(result, SH.resultPath)
            for message in report.objects(result, SH.resultMessage):
                target_id = str(focus).rsplit("#", 1)[-1]
                property_name = str(path).rsplit("#", 1)[-1]
                errors.append(f"- {target_id} / {property_name}: {message}")
        for error in sorted(errors):
            print(error)
        print("검사 실패: 이 입력은 저장하지 않습니다.")
        return False

    # 저장 여부는 Python의 이 분기가 결정합니다. SHACL 자체가 저장을 막지는 않습니다.
    graph.serialize(destination=output_path, format="turtle", encoding="utf-8")
    print(f"저장 완료: {output_path.name}")
    return True


def main():
    data_dir = Path(__file__).resolve().parents[2] / "data"
    shapes = Graph()
    shapes.parse(data_dir / "cafe_shapes.ttl", format="turtle")
    output_path = data_dir / "cafe_validated.ttl"

    # 같은 요구사항으로 잘못된 입력과 정상 입력을 각각 검사합니다.
    validate_and_save(data_dir / "cafe_invalid.ttl", shapes, output_path)
    validate_and_save(data_dir / "cafe.ttl", shapes, output_path)


if __name__ == "__main__":
    main()
