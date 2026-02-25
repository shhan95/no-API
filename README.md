# NFPC/NFTC 주간 자동검토 (No API)

- 법제처(국가법령정보센터) 및 소방청 공개 웹페이지를 주 1회(금 14:00 KST) 파싱하여
  NFPC/NFTC 관련 항목의 변동(추가/제외)을 기록합니다.
- GitHub Pages로 배포하면 대시보드에서 배너/로그/프린트/리포트 링크를 확인할 수 있습니다.

## 설치/배포(가장 쉬운 방식)
1) 이 ZIP 압축을 풀어서 새 GitHub 저장소에 업로드
2) **Settings → Pages → Deploy from a branch → main / (root)** 저장
3) **Actions**에서 “NFPC NFTC Weekly Check (No API)” → Run workflow 1회 실행
4) Pages URL 접속

## 주의
- 공개 웹페이지 구조가 바뀌면 파싱이 깨질 수 있습니다.
- 이 버전은 “조문 신구대비”까지 자동화하지 않고, 변동 감지(추가/제외) + 원문 링크 제공에 집중합니다.
