# 🚀 안티그래비티 행동 지침: Python 데스크톱 앱 (CustomTkinter) 실전 마스터 가이드 v1.1

> **⚠️ 핵심 원칙**  
> 본 지침은 `CustomTkinter`와 `PyMuPDF(fitz)`를 기반으로 하는 데스크톱 앱 프로젝트에서 AI와 안정적이고 효율적으로 협업하기 위한 실전 운영 기준이다.  
> UI(화면)와 비즈니스 로직(PDF 제어)의 완벽한 분리(SoC)를 유지하며, 상용 소프트웨어 수준의 견고함을 목표로 한다.

---

# 0. 소통 및 버전 관리 원칙 (Vibe & Version Control)

## 의도 요약 및 승인
- 구현 전 사용자 요청 의도를 먼저 요약한다.
- 핵심 PDF 편집 엔진이나 대규모 UI 구조 변경은 사전 승인 후 진행한다.

## 버전 타이틀 명시
코드 수정 시 버전 정보를 명시한다.
예시: `(v1.0.1 툴바 UI 수정)`

## 에러 가시화 원칙
- 오류를 숨기지 않고 사용자에게 즉시 알린다.
- 데스크톱 환경에 맞게 `tkinter.messagebox` (showerror, showwarning) 등을 적극 활용한다.

---

# 1. 데스크톱 환경 최적화 및 UX

## 스케일링(DPI) 및 해상도 대응
- Windows 디스플레이 배율에 따라 캔버스 좌표계가 틀어질 수 있음을 항상 인지한다.
- 픽셀 좌표와 원본 PDF Point 좌표 간의 변환 공식을 코드 내에 명확히 주석으로 남긴다.

## [추가] 비동기 스레딩(Threading) 명문화 (UI Freezing 방지)
- 대용량 PDF 로드 및 고해상도 이미지 렌더링 작업은 반드시 `threading` 모듈을 사용해 백그라운드에서 처리한다.
- UI 업데이트는 `root.after()` 메서드를 통해 메인 스레드로 안전하게 전달(Thread-safe)하여 앱이 "응답 없음" 상태에 빠지지 않도록 한다.

## 가비지 컬렉션(GC) 방어 필수
- `Pillow` 이미지를 Tkinter 캔버스에 띄울 때, 파이썬 가비지 컬렉터가 이미지를 삭제하여 화면이 하얗게 변하는 버그를 철저히 방어한다. (`self.current_image = img` 로 참조 유지)

---

# 2. 모드별 코드 제공 전략

## [모드 A] 신규 기능/모듈 구축
- 파일 생성 시 정해진 아키텍처 규칙을 엄수한다 (`main.py`, `models/`, `ui/`, `services/`).
- **[추가] 상태 관리 설계 원칙 (Undo/Redo 대비):** `models/app_state.py` 설계 시, 작업 내역(Action History)을 리스트 형태의 스택(Stack)으로 관리하여 추후 `Ctrl+Z` (실행 취소) 기능 확장이 용이하도록 기반 구조를 마련한다.

## [모드 B] 기존 프로젝트 수정
- **관심사 분리(SoC) 원칙 절대 엄수**: `ui/` 폴더 내의 코드가 절대로 `fitz` 등 비즈니스 로직에 직접 접근하지 못하게 한다.

---

# 3. 메모리 관리 및 실전 예외 처리

## 메모리 릭(Leak) 방어
- 열어둔 PDF 문서(`fitz.Document`) 객체는 사용이 끝나거나 다른 파일을 열 때 반드시 `close()`를 호출하여 메모리를 해제한다.

## [추가] 한글 폰트(TTF) 명시적 매핑
- `PyMuPDF(fitz)`로 텍스트를 삽입할 때 가장 흔히 겪는 "한글 깨짐(네모 박스)" 현상을 방지한다.
- `editor_service.py`에서 새 텍스트를 오버레이할 때, 시스템 폰트(예: `C:\Windows\Fonts\malgun.ttf`) 또는 프로젝트 내장 TTF 파일을 명시적으로 로드(`fontfile` 파라미터 사용)하여 한글 렌더링을 보장한다.

## 다양한 PDF 테스트 시나리오 고려 및 Recovery 원칙
- 초고해상도, 1,000장 이상의 대용량, 암호/손상된 PDF 예외 처리(`fitz.FileDataError`).
- 파일 덮어쓰기 권한 오류 대비 `try-except` 적용 및 항상 `_수정본.pdf` 형태로 저장.

---

# 4. 위험도 기반 검증 시스템 (Validation System)

## Level 1 — Fast Patch (경미 수정)
- **대상:** 단순 UI 수정, 메시지 변경 / **검증:** 코드 자체 검토 1회

## Level 2 — Standard Validation (일반 기능 수정)
- **대상:** 신규 UI 컴포넌트, 상태 로직, 단순 이벤트 추가 / **검증:** 앱 실행(`python main.py`)을 통한 UI 교차 검증

## Level 3 — Hell Validation Loop (고위험 수정)
- **대상:** 좌표 매핑 공식, 마스킹 엔진, 스레딩 동시성 처리, 빌드 로직 / **검증:** 스크롤/배율 조절 후 정밀 점검. 오류 시 안전 롤백 보장.

---

# 5. 필수 수행: 빌드(Build) 및 배포 안정성

## [추가] 절대 경로 래퍼(Wrapper) 사용 (PyInstaller 대응)
- 추후 `.exe` 빌드 시 이미지 아이콘이나 폰트 파일을 찾지 못해 프로그램이 튕기는(Crash) 현상을 방지한다.
- 로컬 에셋을 불러올 때는 단순히 상대 경로를 쓰지 않고, `sys._MEIPASS`를 확인하여 런타임 절대 경로를 반환하는 `get_resource_path()` 유틸리티 함수를 무조건 거치도록 강제한다.

## 배포 및 저장 명령어
```powershell
git add .
git commit -m "[v1.x.x] 작업 내용 요약"
git push origin main
# PyInstaller 빌드 명령어: pyinstaller --noconsole --onefile ...
```
