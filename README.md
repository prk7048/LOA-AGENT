# 🛡️ LOA AGENT - 사용자 맞춤형 스케줄링 및 데이터 시각화 서비스

![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31-red?logo=streamlit)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)

> **"게임 데이터를 넘어, 나만의 비서를 만들다."**
> Lost Ark Open API를 활용하여 다중 계정 캐릭터 데이터를 수집하고, 사용자 정의 주기(Interval)에 따라 워크플로우를 자동화하는 웹 서비스입니다.

---

## 프로젝트 미리보기

---

## 핵심 기능 및 기술적 특징 (Key Features)

### 1. 고성능 데이터 동기화 (ETL)
- **병렬 처리(Parallel Processing):** `ThreadPoolExecutor`를 도입하여 다수 캐릭터(10+)의 상세 정보 조회 시 발생하는 Network I/O 병목을 해결 (속도 80% 개선).
- **데이터 정합성 보장:** API의 일시적 오류로 인한 전투력 하락을 방지하기 위해 'Max Value Upsert' 알고리즘 적용.

### 2. 지연 평가(Lazy Evaluation) 리셋 시스템
- 별도의 스케줄러 서버(Cron) 없이, **Request 시점**에 마지막 수행 시간을 계산하여 상태를 초기화하는 경량화 로직 구현.
- **커스텀 주기 지원:** 단순 일일/주간 리셋뿐만 아니라, 사용자가 설정한 **N일 간격(Interval)** 리셋 로직 구현.

### 3. 데이터 시각화 및 경영 지표
- **목표 기반 대시보드:** 목표 날짜까지의 예상 수익을 실시간으로 계산하여 시각화.
- **다중 계정 지원:** 콤마(,) 구분자를 활용한 멀티 계정 파싱 및 통합 관리.

---

## 기술 스택 (Tech Stack)

| Category | Technology | Description |
| :--- | :--- | :--- |
| **Backend & Frontend** | Python, Streamlit | 빠른 MVP 검증 및 UI/UX 구현 |
| **Database** | PostgreSQL | 관계형 데이터 저장 및 트랜잭션 관리 |
| **Infrastructure** | Docker, Docker Compose | 환경 일치성 보장 및 컨테이너 오케스트레이션 |
| **API** | Lost Ark Open API | RESTful API 데이터 수집 |

---

## 설치 및 실행 방법 (Installation)

이 프로젝트는 Docker 환경에서 실행하는 것을 권장합니다.

1. **저장소 클론**
   ```bash
   git clone [https://github.com/prk7048/LOA-AGENT.git](https://github.com/prk7048/LOA-AGENT.git)
   cd LOA-AGENT```

2. 환경 변수 설정 (.env)
    프로젝트 루트에 .env 파일을 생성하고 API 키를 입력합니다.
    ```
    LOSTARK_API_KEY=your_api_key_here
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=password
    POSTGRES_DB=loa_db
    ```
3. **Docker 실행**
    ```
    docker-compose up -d --build
    ```
4. 접속
    브라우저에서 http://localhost:8501 접속

## 트러블 슈팅 (Troubleshooting)
### API 데이터 타입 불일치 문제
- **문제:** API 응답 중 `CombatPower` 필드가 숫자형이 아닌 문자열(`"1,743.76"`)로 반환되어 Type Casting Error 발생.
- **해결:** 데이터 파싱 레이어(Layer)를 두어 `,` 제거 및 `float` -> `int` 변환 과정을 거쳐 안정성 확보.

### 동기화 속도 저하 문제
- **문제:** 순차적(Sequential) API 호출로 인해 사용자 대기 시간이 길어짐.
- **해결:** Python `concurrent.futures`를 활용한 멀티 스레딩 도입으로 I/O Blocking 시간 단축.
    
---

## 주요 기능 (Key Features)
1.  **Integrated Dashboard:** 숙제 체크, 골드 수급 현황, 원정대 정보를 한눈에 파악
2.  **Market Intelligence:** 경매장 시세 추적 및 효율적인 아이템 구매 가이드
3.  **Growth Diary:** 아이템 레벨/전투력 성장 추이 시각화 및 회고(Diary) 기능
4.  **AI Commander:** 게임 패치 노트, 시장 동향, 내 스펙을 종합 분석하여 성장 방향성 제안

---

## 향후 개선 계획 (Future Roadmap)
- **Backend Migration:** 트래픽 증가 시 Python의 GIL(Global Interpreter Lock) 한계를 극복하기 위해 **Java (Spring Boot)** 또는 **Node.js (NestJS)**로 백엔드 서버 분리 예정.
- **ORM 도입:** 현재의 Raw Query 방식을 JPA/TypeORM 등으로 고도화하여 유지보수성 향상.
- **Client-Side Rendering:** Streamlit의 한계를 넘어 React/Vue.js를 도입하여 사용자 경험(UX) 고도화.
