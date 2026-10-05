# 온톨로지 학습과 고급 카페 응용

처음에는 Python 객체로 개념·개체·관계를 익히고, 이후 RDF/OWL 추론과 SHACL 검사를
학습합니다. 마지막에는 추천과 주문으로 재고가 실제로 바뀌는 응용을 실행합니다.

이번 저장소에는 두 가지 고급 산출물이 있습니다.

1. **어려운 응용:** 고객 조건·예산·수량·매장 재고를 함께 검사하는 메뉴 추천과 주문 저장.
2. **복잡한 온톨로지:** 메뉴·레시피·재료·알레르기 성분·공급업체·지역·재고·주문 모델.

## 설치

Python 3.12 이상이 필요합니다. 아래 명령은 저장소 루트에서 PowerShell로 실행합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

이미 `.venv`가 있다면 설치 명령만 실행하면 됩니다. `requirements.txt`는 검증한
버전을 고정하고, 프로젝트의 `pyproject.toml`에는 허용 버전 범위를 기록했습니다.
별도 API 키, 데이터베이스, 외부 서버는 필요하지 않습니다.

## 먼저 실행해보기

```powershell
.\.venv\Scripts\python.exe ontology_practice\src\ontology_practice\advanced_cafe.py demo
```

샘플 고객 민수의 결과는 다음과 같습니다. `demo`는 원본 샘플을 사용하는 읽기 전용 명령입니다.

| 메뉴 | 결과 | 이유 |
|---|---|---|
| 아메리카노 | 조건 일치 | 3,000원, 재고 충분 |
| 귀리 라테 | 조건 일치 | 4,500원, 재고 충분 |
| 우유 라테 | 제외 | 우유 제외 조건, 식물성 재료 조건 불일치 |
| 말차 라테 | 제외 | 말차 재고 0g |
| 참깨 쿠키 | 제외 | 참깨 제외 조건 |

결과 JSON에는 재료별 필요량·현재 재고·알레르기 성분·공급업체도 포함됩니다.

## 추천 후 실제 주문하기

```powershell
# 현재 상태를 기준으로 추천
.\.venv\Scripts\python.exe ontology_practice\src\ontology_practice\advanced_cafe.py recommend --customer Minsu

# 귀리 라테 한 잔을 주문하고 재고 및 주문을 저장
.\.venv\Scripts\python.exe ontology_practice\src\ontology_practice\advanced_cafe.py order --menu OatLatte

# 저장된 재고를 다시 읽어 추천
.\.venv\Scripts\python.exe ontology_practice\src\ontology_practice\advanced_cafe.py recommend --customer Minsu
```

첫 주문 뒤 원두는 80g에서 62g, 귀리 음료는 300g에서 100g으로 바뀝니다.
다시 귀리 라테를 주문하면 귀리 음료 200g이 필요하므로 거절됩니다.
거절된 주문은 재고나 저장 파일을 변경하지 않습니다.

주문은 `outputs/advanced/state.ttl`에 저장됩니다. 다른 실습 상태를 사용하려면
각 명령에 `--state outputs/my-session.ttl`을 지정하세요. 존재하지 않는 상태 경로는
원본 샘플로 시작합니다. `recommend`와 `impact`는 상태 파일을 만들지 않습니다.

```powershell
# 두 잔, 총예산 10,000원 조건
.\.venv\Scripts\python.exe ontology_practice\src\ontology_practice\advanced_cafe.py recommend --quantity 2 --budget 10000

# 카페인을 피하는 다른 고객
.\.venv\Scripts\python.exe ontology_practice\src\ontology_practice\advanced_cafe.py recommend --customer Jisu

# 공급업체 재료를 사용하는 메뉴 추적
.\.venv\Scripts\python.exe ontology_practice\src\ontology_practice\advanced_cafe.py impact --supplier BeanSupplier
```

공급업체 영향 분석은 재료 출처로 연결된 메뉴를 조회합니다. 실제 회수 명령이나
운영 중단을 수행하지 않습니다.

## 어디부터 읽을까요?

| 경로 | 내용 |
|---|---|
| [기초 튜토리얼](ontology_practice/README.md) | ex1~ex8: 객체, RDF, 추론, SPARQL, SHACL |
| [고급 응용 설명](ontology_practice/advanced/README.md) | 처리 흐름, 모델 설계, 변경 실습 |
| [기능 요구사항](ontology_practice/advanced/REQUIREMENTS.md) | 기능 범위와 완료 기준 |
| [온톨로지 스키마](ontology_practice/advanced/ontology.ttl) | OWL 클래스·속성·속성 체인·조건 클래스 |
| [샘플 사실](ontology_practice/advanced/sample_data.ttl) | 고객, 메뉴, 레시피, 재고 |
| [검사 요구사항](ontology_practice/advanced/shapes.ttl) | SHACL 필수값·수량·자료형·중복 검사 |
| [응용 코드](ontology_practice/src/ontology_practice/advanced_cafe.py) | 추천, 제외 이유, 주문, 저장 |

## 검증

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s ontology_practice\tests -v
```

13개 테스트는 속성 체인과 클래스 분류, 고객 조건, 수량·가격·재고 계산,
정보 누락과 중복 재고 거절, 주문 저장·재조회, 거절 시 파일 보존, 주문 잠금을 검증합니다.
테스트의 저장 파일은 임시 디렉터리에 생성하므로 실제 실습 재고를 소비하지 않습니다.

## 데이터와 운영 범위

샘플의 고객과 공급업체, 재료 프로필은 학습용 데이터입니다. 추천은 입력한 조건과
데이터가 일치한다는 뜻이며 실제 제품의 알레르기 적합성을 보장하지 않습니다.
`profileComplete=true`는 입력자가 재료의 성분·카페인·식단 정보를 완성했다는 표시입니다.
이 값이 누락되거나 거짓이면 검사를 통과하지 못합니다.

OWL의 개방 세계 가정에서 사실이 없다는 것만으로 부정 사실을 얻지는 않습니다.
응용은 검사에 통과한 샘플 프로필을 완전한 목록으로 취급하는 정책을 명시적으로 사용합니다.
가격·재고 산술과 파일 저장은 Python이 처리하고, 관계와 클래스 추론은 OWL이 처리합니다.

한 주문은 한 종류의 메뉴와 수량을 처리합니다. 결제·배송·교차오염 모델·인증·원격 DB는
포함하지 않습니다. 로컬 파일 잠금과 원자적 교체로 동일 상태 파일의 주문을 처리하며,
분산 서버나 트랜잭션 DB를 구현한 예제는 아닙니다.

## 참고 문서

- [W3C RDF 입문](https://www.w3.org/TR/rdf11-primer/)
- [W3C OWL 입문: 속성 체인](https://www.w3.org/TR/owl2-primer/#Property_Chains)
- [W3C SHACL](https://www.w3.org/TR/shacl/)
- [RDFLib](https://rdflib.readthedocs.io/en/stable/apidocs/rdflib.graph/)
- [pySHACL](https://github.com/RDFLib/pySHACL)
