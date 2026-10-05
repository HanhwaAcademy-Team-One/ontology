# 온톨로지 첫 실습

처음 실행하는 경우 [저장소 README](../README.md)의 설치 방법을 먼저 확인하세요.
ex1~ex8을 마친 뒤에는 [고급 카페 응용](advanced/README.md)으로 이어집니다.
고급 응용은 추천과 제외 이유, 공급업체 영향 조회, 실제 주문 및 재고 저장을 다룹니다.

`ex1.py`는 Python 객체로 대상과 관계를 표현하는 준비 실습입니다.
`ex2.py`는 실제 RDF/OWL 문법으로 작성한 Turtle 파일을 읽는 실습입니다.

## 파일의 역할

- `data/cafe.ttl`: 클래스, 관계, 속성의 정의와 실제 사실을 저장합니다.
- `src/ontology_practice/ex2.py`: RDFLib로 파일을 읽고 조회합니다.
- `pyproject.toml`: 필요한 Python 라이브러리인 RDFLib를 기록합니다.

`.ttl`은 UTF-8 텍스트 파일입니다. 편집기에서 파일을 만들고 Turtle 문법으로
작성하면 됩니다. 온톨로지와 사실을 이번 예제에서는 한 파일에 함께 담았습니다.

## 실행

PowerShell에서 `D:\ontology` 폴더를 기준으로 실행합니다.

```powershell
.\.venv\Scripts\python.exe -m pip install "rdflib>=7.6,<8"
.\.venv\Scripts\python.exe ontology_practice\src\ontology_practice\ex2.py
```

## 읽는 순서

1. `ex:Customer a owl:Class .`: 손님이라는 종류를 정의합니다.
2. `ex:C001 a ex:Customer .`: C001은 손님이라고 기록합니다.
3. `ex:C001 ex:name "민수" .`: C001의 이름을 기록합니다.
4. `ex:C001 ex:buys ex:drink1 .`: 손님과 음료 사이의 구매 관계를 기록합니다.
5. Python의 `graph.parse(...)`가 파일을 읽습니다.
6. `graph.objects(...)`가 구매 관계를 따라 음료를 찾습니다.
7. `graph.query(...)`가 SPARQL 질문을 실행합니다.

`ex:`는 `https://example.org/cafe#`를 줄인 접두사입니다.
따라서 `ex:C001`은 `https://example.org/cafe#C001`이라는 식별자입니다.
이 주소는 이번 실습에서 대상을 식별하는 데 사용하며 웹 서버를 만들 필요는 없습니다.

`owl:ObjectProperty`는 대상 사이의 관계이고,
`owl:DatatypeProperty`는 문자열이나 참/거짓 같은 값으로 이어지는 속성입니다.

## 작은 실습

`cafe.ttl`의 다음 한 줄 앞에 `#`을 붙이고 Python을 다시 실행해보세요.

```turtle
ex:C001 ex:buys ex:drink1 .
```

민수의 구매 목록에는 파워에이드만 남고, 카페인 음료 구매자 조회에는 민수가
나오지 않습니다. Python 코드를 바꾸지 않아도 RDF 사실의 변화가 결과에 반영됩니다.

이 예제는 RDF를 읽고 조회합니다. 파일에 OWL 선언이 있어도 RDFLib의 `parse()`만으로
OWL의 의미에 따른 추론이 자동 실행되지는 않습니다. 추론기는 다음 실습에서 다룹니다.

## 다음 실습: 클래스 계층과 자동 추론

`data/cafe_reasoning.ttl`에는 커피가 음료의 하위 클래스라는 정의와,
아메리카노 한 잔인 `drink1`이 커피라는 사실을 기록했습니다.

```turtle
ex:Coffee rdfs:subClassOf ex:Drink .
ex:drink1 a ex:Coffee .
```

`rdfs:subClassOf`는 클래스 사이의 포함 관계입니다. 커피에 속하는 모든 개체는
음료에도 속합니다. 개체의 종류를 지정하는 `a`와 클래스 계층을 지정하는
`rdfs:subClassOf`를 구분해보세요.

```powershell
.\.venv\Scripts\python.exe -m pip install "owlrl>=7.6.2,<8"
.\.venv\Scripts\python.exe ontology_practice\src\ontology_practice\ex3.py
```

`ex3.py`는 같은 SPARQL 질문을 추론 전과 후에 실행합니다. 추론 전에는
`drink1`을 음료라고 기록한 문장이 없어 음료 조회 결과가 비어 있습니다.
이는 음료가 아니라고 판정한 것이 아니라, 현재 그래프에 해당 문장이 없다는 뜻입니다.
추론 후에는 `drink1`이 음료라는 문장이 추가되어 아메리카노가 조회됩니다.

추론을 실행하는 부분은 다음 한 줄입니다.

```python
DeductiveClosure(OWLRL_Semantics).expand(graph)
```

`owlrl`은 OWL 2 RL 범위의 규칙을 적용하는 라이브러리이며, 이번에 적용하는
클래스 계층 규칙은 RDFS에서도 정의됩니다. 추론 결과는 실행 중인 메모리의
그래프에 추가되며, `.ttl` 파일을 자동으로 수정하지 않습니다.

작은 실습: `ex:Coffee rdfs:subClassOf ex:Drink .` 앞에 `#`을 붙이고 다시
실행해보세요. 계층 관계가 없으면 추론 후에도 음료 조회 결과가 비어 있습니다.

## SPARQL 실습: 관계 연결과 조건 검색

`ex4.py`는 `cafe.ttl`에서 손님과 구매한 음료를 함께 찾습니다.

```powershell
.\.venv\Scripts\python.exe ontology_practice\src\ontology_practice\ex4.py
```

`?customer ex:buys ?drink .`는 손님과 음료를 연결하는 패턴입니다.
다른 패턴에도 같은 변수명을 쓰면 같은 대상을 가리켜야 합니다.
`?customer ex:name ?customerName .`과 `?drink ex:name ?drinkName .`으로
각 대상의 이름을 가져옵니다. `SELECT`는 결과에 보여줄 변수를 지정합니다.

두 번째 쿼리는 `?drink ex:hasCaffeine ?hasCaffeine .`으로 카페인 값을 찾고,
`FILTER(?hasCaffeine = true)`로 값이 참인 결과만 남깁니다.
이 값은 `.ttl`에 저장된 사실이며, `ex4.py`는 추론기를 실행하지 않습니다.

작은 실습: 두 번째 쿼리의 `FILTER(?hasCaffeine = true)`를
`FILTER(?hasCaffeine = false)`로 바꾸고 다시 실행해보세요.
두 번째 목록에는 파워에이드가 나와야 합니다. 출력 제목도 조건에 맞게 바꿔보세요.

## 관계의 의미: domain과 range

`data/cafe_domain_range.ttl`은 구매 관계의 양쪽 대상이 어떤 종류인지 정의합니다.

```turtle
ex:buys rdfs:domain ex:Customer .
ex:buys rdfs:range ex:Drink .
ex:C002 ex:buys ex:drink3 .
```

`domain`은 이 관계의 주어가 속하는 클래스, `range`는 목적어가 속하는 클래스를
지정합니다. 따라서 추론기는 C002를 손님으로, drink3을 음료로 분류합니다.
파일에는 이 두 개체의 종류를 직접 작성하지 않았습니다.

```powershell
.\.venv\Scripts\python.exe ontology_practice\src\ontology_practice\ex5.py
```

추론 전에는 두 종류 문장이 그래프에 없고, 추론 후에는 추가됩니다.
문장이 없다는 것은 해당 종류가 아니라고 판정했다는 뜻이 아닙니다.

이 정의는 타입을 추론하는 의미를 가집니다. 잘못된 구매 관계를 입력했을 때
자동으로 입력을 거부하는 검사 규칙은 아닙니다. 데이터 검사 방법은 이후
SHACL 실습에서 다룹니다.

작은 실습: `ex:buys rdfs:range ex:Drink .` 앞에 `#`을 붙이고 실행해보세요.
추론 후 손님 문장은 생기지만, 음료 문장은 생기지 않아야 합니다.

## 역관계: owl:inverseOf

`data/cafe_inverse.ttl`은 `buys`와 `boughtBy`가 서로 역관계라고 정의합니다.

```turtle
ex:buys owl:inverseOf ex:boughtBy .
ex:C001 ex:buys ex:drink1 .
```

추론기는 위의 정의와 사실에서 다음 문장을 얻습니다.

```turtle
ex:drink1 ex:boughtBy ex:C001 .
```

관계의 주어와 목적어를 바꾸면서 관계 이름도 `buys`에서 `boughtBy`로 바꿉니다.
`drink1 buys C001`이라는 문장을 만드는 것은 아닙니다.

```powershell
.\.venv\Scripts\python.exe ontology_practice\src\ontology_practice\ex6.py
```

`ex6.py`는 추론 전후에 `boughtBy` 관계로 구매자를 조회합니다. 추론 전에는
그 관계가 없으므로 결과가 비고, 추론 후에는 민수가 나옵니다.
구매자가 존재하지 않았다는 뜻은 아닙니다. 원래의 `buys` 관계로 구매자를
조회하는 SPARQL 질문도 작성할 수 있습니다.

작은 실습: `ex:buys owl:inverseOf ex:boughtBy .` 앞에 `#`을 붙이고 다시
실행해보세요. 역관계 정의가 없으면 `boughtBy` 조회는 추론 후에도 비어 있습니다.

## 추이적 관계: owl:TransitiveProperty

`data/cafe_transitive.ttl`에서는 장소가 더 큰 지역에 속하는 `partOf` 관계를
추이적 관계로 정의합니다.

```turtle
ex:partOf a owl:TransitiveProperty .
ex:cafe1 ex:partOf ex:Gangnam .
ex:Gangnam ex:partOf ex:Seoul .
```

추론기는 `ex:cafe1 ex:partOf ex:Seoul .`이라는 연결을 추가합니다.
같은 관계 R에 대해 A→B와 B→C에서 A→C를 얻는 것이 추이성입니다.

```powershell
.\.venv\Scripts\python.exe ontology_practice\src\ontology_practice\ex7.py
```

추론 전에는 카페에서 한 번의 `partOf` 관계로 조회되는 지역이 강남구뿐입니다.
추론 후에는 서울도 직접 연결되어 같은 쿼리로 조회됩니다.

모든 관계에 추이성을 적용하는 것은 아닙니다. 예를 들어 'A가 B를 안다'와
'B가 C를 안다'만으로 A가 C를 안다고 할 수 없습니다. 관계의 의미에 맞게
추이성을 정의해야 합니다.

작은 실습: `ex:partOf a owl:TransitiveProperty .` 앞에 `#`을 붙이고
실행해보세요. 추론 후에도 카페에서 직접 연결된 지역은 강남구만 조회됩니다.

## 데이터 검사와 저장: SHACL

`ex8.py`는 입력 데이터를 검사한 뒤, 통과한 경우에만 파일을 저장합니다.
이번 실습은 추론 규칙을 추가하는 대신 실제 입력 처리 흐름을 만듭니다.

- `data/cafe_shapes.ttl`: 이름 필수, 카페인 여부의 값 형식 같은 검사 요구사항
- `data/cafe_invalid.ttl`: 이름 누락과 잘못된 카페인 값이 있는 입력
- `data/cafe.ttl`: 정상 입력
- `data/cafe_validated.ttl`: 검사에 통과한 입력을 저장한 결과

```powershell
.\.venv\Scripts\python.exe -m pip install "pyshacl>=0.40,<1"
.\.venv\Scripts\python.exe ontology_practice\src\ontology_practice\ex8.py
```

잘못된 입력은 오류를 출력하고 저장을 건너뜁니다. 이어서 정상 입력이 검사에
통과하면 `cafe_validated.ttl`로 저장합니다. 다시 실행하면 통과한 데이터로
이 결과 파일을 갱신합니다. 입력 파일과 요구사항 파일은 수정하지 않습니다.

SHACL 검사 자체는 통과 여부와 오류 보고서를 돌려줍니다. 검사 실패 시 저장을
건너뛰는 것은 Python 코드의 결정입니다. 이번 실습은 `inference="none"`으로
실행하므로 입력에 명시된 손님과 음료를 대상으로 검사합니다.

검사 요구사항의 기본 문법은 다음과 같습니다.

```turtle
sh:path ex:hasCaffeine ;
sh:minCount 1 ;
sh:maxCount 1 ;
sh:datatype xsd:boolean ;
```

이는 카페인 속성 값이 정확히 하나 필요하고, 그 값이 참/거짓 형식이어야 한다는
뜻입니다. 세미콜론은 같은 주어에 대한 다음 속성을 이어 쓰는 Turtle 문법입니다.
대괄호는 여기서 별도 ID 없이 검사 항목을 묶는 데 사용합니다.

작은 실습: `cafe_invalid.ttl`에 `ex:C003 ex:name "민호" .`를 추가하고,
`ex:drink_bad ex:hasCaffeine "모름" .`의 `"모름"`을 따옴표 없는 `false`로
바꿔보세요. 두 오류를 수정하면 이 입력도 검사에 통과하여 저장됩니다.
