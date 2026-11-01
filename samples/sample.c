/* sample.c — AI_docs reader 코드 보기 확인용 (읽기 전용 · 줄 번호) */
#include <stdio.h>
#include <stdlib.h>

#define PERCENT_BASE 100

/* 합계 — 7번 줄부터 함수 본문 */
int sum_values(const int *values, int count)
{
    int total = 0;
    for (int i = 0; i < count; i++) {
        total += values[i];
    }
    return total;
}

int average(const int *values, int count)
{
	/* 탭 들여쓰기 줄 */
	if (count <= 0) {
		return 0;
	}
	return sum_values(values, count) / count;
}

/* 아주 긴 줄: 창 폭에서 줄바꿈돼도 다음 줄 번호가 밀리지 않아야 한다 — 이 문장은 일부러 길게 써서 화면 폭을 넘기도록 만든 주석이며 줄 번호 정렬을 눈으로 확인하는 데 쓴다. */
int percent(int part, int whole)
{
    if (whole == 0) {
        return 0;
    }
    return (part * PERCENT_BASE) / whole;
}

int main(void)
{
    int values[] = {10, 20, 30, 40};
    int n = (int)(sizeof(values) / sizeof(values[0]));
    printf("sum=%d avg=%d pct=%d\n", sum_values(values, n), average(values, n), percent(1, 4));
    return 0;
}
