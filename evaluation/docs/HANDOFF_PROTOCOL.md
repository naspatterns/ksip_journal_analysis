# 세션 인계 프로토콜 (HANDOFF)

> 멀티 컴퓨터로 작업하기 위한 *세션 경계의 의식*.
> 환경 자체 셋업은 [`ENVIRONMENT.md`](./ENVIRONMENT.md).
> 현재 위치는 [`SESSION_STATE.md`](./SESSION_STATE.md).

---

## 세션 시작 시

```bash
# 1. 작업 디렉토리로 이동
cd <path-to>/ksip_journal_analysis

# 2. 최신 상태 받기
git checkout main
git pull origin main

# 3. 환경 검증
.venv/bin/python evaluation/scripts/check_env.py

# 4. 현재 위치 파악 — 가장 중요
cat evaluation/docs/SESSION_STATE.md

# 5. 마지막 검증 결과 확인 (선택)
cat evaluation/output/verification/verify_summary.md | head -30
```

→ `SESSION_STATE.md` 의 **"⏳ 진행 중인 토론"** 과 **"다음 세션 권장 첫 행동"** 부터 작업 재개.

---

## 세션 종료 시

```bash
# 1. 현재 상태 확인
git status
git diff --stat

# 2. 변경 commit
git add <specific-files>
git commit -m "..."

# 3. SESSION_STATE.md 갱신 (필수)
#    - "마지막 갱신" 날짜
#    - "Phase 진행도" 의 상태 표시
#    - "⏳ 진행 중인 토론" 의 새 dependent 결정
#    - "다음 세션 권장 첫 행동"
$EDITOR evaluation/docs/SESSION_STATE.md
git add evaluation/docs/SESSION_STATE.md
git commit -m "session: <한 줄 요약>"

# 4. push (다른 컴퓨터에서 받을 수 있게)
git push origin main
```

→ push 까지 마쳐야 다른 컴퓨터에서 이어 받음.

---

## 워크트리에서 작업한 경우 — main 으로 머지

Claude Code 는 자체 worktree 브랜치 (`claude/<temp-name>`) 에서 작업.
이 브랜치는 임시 — main 으로 머지해야 정식 사용:

```bash
# 워크트리 브랜치 이름 확인
git branch --show-current
# 예: claude/festive-elgamal-1dd4b3

# 1. 메인 작업 디렉토리로 (worktree 가 아닌)
cd <main-project-root>

# 2. main 으로 전환
git checkout main

# 3. 최신 main pull
git pull origin main

# 4. 워크트리 브랜치를 main 으로 머지
git merge claude/festive-elgamal-1dd4b3
# (--no-ff 권장 — 머지 커밋 보존)
git merge --no-ff claude/festive-elgamal-1dd4b3 -m "merge: worktree <topic>"

# 5. 충돌 발생 시 해소 (대개 evaluation/ 와 main 쪽이 직교라 충돌 적음)

# 6. push
git push origin main

# 7. 워크트리 정리 (선택)
git worktree remove .claude/worktrees/festive-elgamal-1dd4b3
git branch -d claude/festive-elgamal-1dd4b3
```

---

## 두 컴퓨터에서 동시에 변경했을 때 — 충돌 처리

```bash
# pull 시 충돌
git pull origin main
# Auto-merging xxx
# CONFLICT (content): Merge conflict in yyy

# 1. 충돌 파일 확인
git status

# 2. 어느 쪽 살릴지 결정 (사용자 판단)
#    - 코드: 보통 양쪽 변경을 합침
#    - parquet: 어느 한쪽으로 통일하고 build_data.py 재실행
#    - dictionary yml: 양쪽 entry 합집합

# 3. 해소 후 commit
git add <resolved-files>
git commit
git push origin main
```

---

## raw 데이터 변경 시 (KCI 재다운로드 등)

```
1. 한 컴퓨터에서 raw 받음 (gitignored)
2. cloud (Drive/Dropbox/scp) 로 *별도* 동기화
3. 다른 컴퓨터에서 raw 받은 후 → build_data.py 재실행
   .venv/bin/python scripts/build_data.py
4. 갱신된 parquet 4개 commit + push
```

→ raw 자체는 git 에 안 들어가도, parquet 산출물은 git 으로 다른 컴퓨터에 전파.

---

## SESSION_STATE.md 갱신 체크리스트 (세션 종료 시)

- [ ] **"마지막 갱신"** 날짜 갱신
- [ ] **"Phase 진행도"** 상태 표시 (✅/⏳/⏸ 변동)
- [ ] **"⏳ 진행 중인 토론"** — 새 미결 결정이 있으면 등재, 해소된 것은 RESOLVED 표시
- [ ] **"직전 커밋 정보"** — HEAD 해시 + 메시지 갱신
- [ ] **"잔여 OPEN 이슈"** — ISSUES.md 와 sync 확인
- [ ] **"다음 세션 권장 첫 행동"** 갱신 (다음 컴퓨터에서 무엇부터 할지)

---

## 황금률 3가지

1. **SESSION_STATE.md 는 거짓말하지 않는다** — 모든 세션이 같은 상태 인식을 공유.
2. **push 안 한 것은 존재하지 않는다** — 다른 컴퓨터에서 받을 수 없음.
3. **raw·key 는 cloud 동기화, 나머지는 git** — 한 가지로 일원화하지 말 것 (보안+편의).
