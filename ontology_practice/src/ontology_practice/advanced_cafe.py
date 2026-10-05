"""고급 응용: 검증 → OWL 추론 → 추천 → 주문/재고 저장.

이 예제의 추천은 제공한 실습 데이터의 조건 일치 결과입니다.
모든 가격은 원, 재료 사용량과 재고는 g 단위입니다.
"""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal
import json
import os
from pathlib import Path
import re
import tempfile
from uuid import uuid4

from owlrl import DeductiveClosure, OWLRL_Semantics
from pyshacl import validate
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef, XSD
from rdflib.namespace import SH


PROJECT = Path(__file__).resolve().parents[2]
ASSETS = PROJECT / "advanced"
DEFAULT_STATE = PROJECT.parent / "outputs" / "advanced" / "state.ttl"
EX = Namespace("https://example.org/cafe-ops#")


class DomainError(ValueError):
    """요구사항이나 입력 데이터 때문에 작업을 진행할 수 없는 경우입니다."""


def entity_id(name):
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", name):
        raise DomainError("ID에는 영문자로 시작하는 영문, 숫자, 밑줄만 사용할 수 있습니다.")
    return EX[name]


def label(graph, entity):
    return str(graph.value(entity, RDFS.label) or str(entity).rsplit("#", 1)[-1])


def load_data(state=None, seed=None):
    source = Path(state) if state is not None and Path(state).exists() else Path(seed or ASSETS / "sample_data.ttl")
    return Graph().parse(source, format="turtle")


def knowledge_graph(data):
    graph = Graph().parse(ASSETS / "ontology.ttl", format="turtle")
    graph += data
    return graph


def validate_data(data):
    """하위 클래스만 해석하는 RDFS 검사 후, 문제가 있으면 추론/주문을 중단합니다."""
    conforms, report, _ = validate(
        data_graph=knowledge_graph(data),
        shacl_graph=str(ASSETS / "shapes.ttl"),
        inference="rdfs",
    )
    if not conforms:
        messages = []
        for result in report.subjects(RDF.type, SH.ValidationResult):
            node = report.value(result, SH.focusNode)
            path = report.value(result, SH.resultPath)
            message = report.value(result, SH.resultMessage)
            messages.append(f"{str(node).rsplit('#', 1)[-1]} / {str(path).rsplit('#', 1)[-1]}: {message}")
        raise DomainError("SHACL 데이터 검사 실패:\n" + "\n".join(sorted(messages)))


def prepare(data):
    validate_data(data)
    graph = knowledge_graph(data)
    DeductiveClosure(OWLRL_Semantics).expand(graph)
    return graph


def stock_index(graph, store):
    stocks = {}
    for stock in graph.subjects(EX.stockStore, store):
        ingredient = graph.value(stock, EX.stockIngredient)
        available = graph.value(stock, EX.availableGrams).toPython()
        stocks[ingredient] = (stock, Decimal(available))
    return stocks


def recommend(graph, customer=EX.Minsu, store=EX.GangnamStore, quantity=1, budget=None):
    if quantity < 1:
        raise DomainError("수량은 1 이상이어야 합니다.")
    if (customer, RDF.type, EX.Customer) not in graph:
        raise DomainError(f"알 수 없는 고객: {customer}")
    if (store, RDF.type, EX.Store) not in graph:
        raise DomainError(f"알 수 없는 매장: {store}")
    budget = int(graph.value(customer, EX.budget)) if budget is None else budget
    if budget < 0:
        raise DomainError("예산은 0 이상이어야 합니다.")

    vegan_only = graph.value(customer, EX.veganOnly).toPython()
    avoid_caffeine = graph.value(customer, EX.avoidCaffeine).toPython()
    avoided = set(graph.objects(customer, EX.avoidsAllergen))
    stocks = stock_index(graph, store)
    catalog_query = (ASSETS / "queries" / "menu_catalog.rq").read_text(encoding="utf-8")
    menus = {}
    for menu, name, price, requirement, ingredient, grams in graph.query(catalog_query, initBindings={"store": store}):
        item = menus.setdefault(menu, {"name": str(name), "price": int(price), "requirements": {}})
        requirements = item["requirements"]
        requirements[ingredient] = requirements.get(ingredient, Decimal(0)) + Decimal(grams.toPython()) * quantity

    decisions = []
    for menu, item in sorted(menus.items(), key=lambda entry: (entry[1]["price"], str(entry[0]))):
        reasons = []
        total = item["price"] * quantity
        if total > budget:
            reasons.append(f"BUDGET: 합계 {total}원 > 예산 {budget}원")
        for allergen in sorted(avoided & set(graph.objects(menu, EX.containsAllergen)), key=str):
            reasons.append(f"ALLERGEN: 제외 성분 {label(graph, allergen)}")
        if avoid_caffeine and (menu, RDF.type, EX.CaffeinatedMenu) in graph:
            reasons.append("CAFFEINE: 카페인 재료를 포함한 메뉴")

        required_rows = []
        for ingredient, needed in sorted(item["requirements"].items(), key=lambda entry: str(entry[0])):
            available = stocks.get(ingredient, (None, Decimal(0)))[1]
            if vegan_only and not graph.value(ingredient, EX.isVegan).toPython():
                reasons.append(f"NON_VEGAN: {label(graph, ingredient)}")
            if available < needed:
                reasons.append(f"STOCK: {label(graph, ingredient)} 필요 {needed}g / 재고 {available}g")
            required_rows.append({"ingredient_id": str(ingredient), "ingredient": label(graph, ingredient),
                                  "needed_g": str(needed), "available_g": str(available)})

        decisions.append({"menu_id": str(menu), "name": item["name"], "unit_price": item["price"],
                          "quantity": quantity, "total_price": total, "eligible": not reasons,
                          "reasons": reasons, "ingredients": required_rows,
                          "allergens": sorted(label(graph, value) for value in graph.objects(menu, EX.containsAllergen)),
                          "suppliers": sorted(label(graph, value) for value in graph.objects(menu, EX.menuSuppliedBy))})
    return decisions


def supplier_impact(graph, supplier):
    if (supplier, RDF.type, EX.Supplier) not in graph:
        raise DomainError(f"알 수 없는 공급업체: {supplier}")
    query = (ASSETS / "queries" / "supplier_impact.rq").read_text(encoding="utf-8")
    return [{"menu_id": str(menu), "menu": str(menu_name), "ingredient": str(ingredient_name)}
            for menu, menu_name, ingredient_name in graph.query(query, initBindings={"supplier": supplier})]


@contextmanager
def state_lock(state):
    """동일 상태 파일에 대한 주문을 직렬화합니다. 다른 주문은 재시도하도록 실패합니다."""
    state.parent.mkdir(parents=True, exist_ok=True)
    lock_path = state.with_suffix(state.suffix + ".lock")
    try:
        lock_file = lock_path.open("x", encoding="utf-8")
    except FileExistsError as error:
        raise DomainError(f"다른 주문이 처리 중입니다. 잠시 후 재시도하세요: {lock_path}") from error
    try:
        with lock_file:
            lock_file.write(str(os.getpid()))
        yield
    finally:
        lock_path.unlink()


def save_atomic(data, state):
    """임시 파일을 완성한 뒤 교체하므로 독자는 부분 저장된 RDF를 읽지 않습니다."""
    state.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=state.parent, suffix=".ttl", delete=False) as file:
        temporary = Path(file.name)
    try:
        data.serialize(destination=temporary, format="turtle", encoding="utf-8")
        temporary.replace(state)
    finally:
        temporary.unlink(missing_ok=True)


def place_order(state, menu, customer=EX.Minsu, store=EX.GangnamStore, quantity=1, budget=None):
    state = Path(state).resolve()
    with state_lock(state):
        # 추천 시점의 재고를 믿지 않고 잠금 안에서 최신 상태를 다시 검사합니다.
        data = load_data(state)
        graph = prepare(data)
        decisions = recommend(graph, customer, store, quantity, budget)
        decision = next((item for item in decisions if item["menu_id"] == str(menu)), None)
        if decision is None:
            raise DomainError("이 매장에서 제공하지 않는 메뉴입니다.")
        if not decision["eligible"]:
            raise DomainError("주문 조건 불일치: " + "; ".join(decision["reasons"]))

        stocks = stock_index(graph, store)
        for row in decision["ingredients"]:
            stock, available = stocks[URIRef(row["ingredient_id"])]
            data.set((stock, EX.availableGrams, Literal(available - Decimal(row["needed_g"]), datatype=XSD.decimal)))

        order = EX["Order_" + uuid4().hex]
        line = EX["Line_" + uuid4().hex]
        timestamp = datetime.now(timezone.utc).isoformat()
        for triple in [
            (order, RDF.type, EX.Order), (order, EX.orderedBy, customer), (order, EX.orderStore, store),
            (order, EX.hasLine, line), (order, EX.totalPrice, Literal(decision["total_price"], datatype=XSD.integer)),
            (order, EX.createdAt, Literal(timestamp, datatype=XSD.dateTime)),
            (line, RDF.type, EX.OrderLine), (line, EX.lineMenu, menu),
            (line, EX.lineQuantity, Literal(quantity, datatype=XSD.integer)),
            (line, EX.lineUnitPrice, Literal(decision["unit_price"], datatype=XSD.integer)),
        ]:
            data.add(triple)

        validate_data(data)
        save_atomic(data, state)
        return {"order_id": str(order), "customer": label(graph, customer), "store": label(graph, store),
                "menu": decision["name"], "quantity": quantity, "total_price": decision["total_price"],
                "used_ingredients": decision["ingredients"], "saved_to": str(state)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("demo", help="원본 샘플로 읽기 전용 추천과 공급망 추론을 확인")
    for command in ("recommend", "order", "impact"):
        sub = commands.add_parser(command)
        sub.add_argument("--state", type=Path, default=DEFAULT_STATE)
        if command == "impact":
            sub.add_argument("--supplier", default="PlantSupplier")
        else:
            sub.add_argument("--customer", default="Minsu")
            sub.add_argument("--store", default="GangnamStore")
            sub.add_argument("--quantity", type=int, default=1)
            sub.add_argument("--budget", type=int)
            if command == "order":
                sub.add_argument("--menu", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            graph = prepare(load_data())
            result = {"customer": "민수", "recommendations": recommend(graph),
                      "supplier_impact": supplier_impact(graph, EX.PlantSupplier),
                      "store_regions": sorted(label(graph, value) for value in graph.objects(EX.GangnamStore, EX.inRegion))}
        elif args.command == "order":
            result = place_order(args.state, entity_id(args.menu), entity_id(args.customer),
                                 entity_id(args.store), args.quantity, args.budget)
        else:
            graph = prepare(load_data(args.state))
            if args.command == "impact":
                result = supplier_impact(graph, entity_id(args.supplier))
            else:
                result = recommend(graph, entity_id(args.customer), entity_id(args.store), args.quantity, args.budget)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (DomainError, OSError) as error:
        parser.exit(2, f"오류: {error}\n")


if __name__ == "__main__":
    main()
