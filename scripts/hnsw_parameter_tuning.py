#!/usr/bin/env python3
"""
HNSW 인덱스 파라미터 튜닝 및 성능 테스트 스크립트

이 스크립트는 다양한 HNSW 파라미터 조합을 테스트하고
성능 메트릭을 측정하여 최적의 파라미터를 찾습니다.
"""

import json
import logging
import statistics
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import func, text

from app.models import PaperChunk, SessionLocal

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


@dataclass
class HNSWParams:
    """HNSW 파라미터 조합"""
    m: int
    ef_construction: int
    ef_search: int = None  # 검색시 사용

    def __str__(self):
        return f"m={self.m}, ef_construction={self.ef_construction}, ef_search={self.ef_search}"


@dataclass
class PerformanceMetrics:
    """성능 측정 결과"""
    params: HNSWParams
    index_creation_time: float
    index_size_mb: float
    search_latency_ms: float
    search_accuracy: float
    memory_usage_mb: float
    queries_per_second: float


class HNSWTuner:
    """HNSW 파라미터 튜닝 클래스"""

    def __init__(self):
        self.db = SessionLocal()
        self.test_queries = []
        self.ground_truth = []

    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()

    def prepare_test_data(self, num_queries: int = 100) -> None:
        """테스트용 쿼리와 ground truth 준비"""
        logging.info(f"테스트 데이터 준비 중... ({num_queries}개 쿼리)")

        # 랜덤 샘플 추출
        sample_chunks = (
            self.db.query(PaperChunk)
            .order_by(func.random())
            .limit(num_queries)
            .all()
        )

        for chunk in sample_chunks:
            query_embedding = chunk.embedding
            self.test_queries.append(query_embedding)

            # Ground truth: 정확한 상위 10개 결과
            exact_results = (
                self.db.query(PaperChunk.id)
                .order_by(PaperChunk.embedding.cosine_distance(query_embedding))
                .limit(10)
                .all()
            )
            self.ground_truth.append([r.id for r in exact_results])

        logging.info(f"테스트 데이터 준비 완료: {len(self.test_queries)}개 쿼리")

    def create_index_with_params(self, params: HNSWParams) -> float:
        """지정된 파라미터로 HNSW 인덱스 생성"""
        index_name = f"test_hnsw_m{params.m}_ef{params.ef_construction}"

        # 기존 테스트 인덱스 삭제
        drop_sql = text(f"DROP INDEX IF EXISTS {index_name}")
        self.db.execute(drop_sql)
        self.db.commit()

        # 새 인덱스 생성 시간 측정
        create_sql = text(f"""
            CREATE INDEX {index_name}
            ON paper_chunks
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = {params.m}, ef_construction = {params.ef_construction})
        """)

        start_time = time.time()
        try:
            self.db.execute(create_sql)
            self.db.commit()
            creation_time = time.time() - start_time
            logging.info(f"인덱스 생성 완료: {params} (시간: {creation_time:.2f}초)")
            return creation_time
        except Exception as e:
            logging.error(f"인덱스 생성 실패: {params}, 오류: {e}")
            self.db.rollback()
            return float('inf')

    def get_index_size(self, index_name: str) -> float:
        """인덱스 크기 조회 (MB)"""
        size_sql = text("""
            SELECT pg_size_pretty(pg_relation_size(indexrelid)) as size,
                   pg_relation_size(indexrelid) as size_bytes
            FROM pg_stat_user_indexes 
            WHERE indexrelname = :index_name
        """)

        result = self.db.execute(size_sql, {"index_name": index_name}).fetchone()
        if result:
            return result.size_bytes / (1024 * 1024)  # MB로 변환
        return 0.0

    def measure_search_performance(self, params: HNSWParams) -> tuple[float, float, float]:
        """검색 성능 측정"""
        if not self.test_queries:
            self.prepare_test_data()

        # ef_search 설정 (PostgreSQL의 경우 세션 레벨에서 설정)
        if params.ef_search:
            set_ef_sql = text(f"SET hnsw.ef_search = {params.ef_search}")
            self.db.execute(set_ef_sql)

        latencies = []
        accuracies = []

        for i, (query_embedding, ground_truth) in enumerate(zip(self.test_queries, self.ground_truth, strict=False)):
            # 검색 시간 측정
            start_time = time.time()

            search_results = (
                self.db.query(PaperChunk.id)
                .order_by(PaperChunk.embedding.cosine_distance(query_embedding))
                .limit(10)
                .all()
            )

            latency = (time.time() - start_time) * 1000  # ms로 변환
            latencies.append(latency)

            # 정확도 계산 (Precision@10)
            retrieved_ids = [r.id for r in search_results]
            correct_matches = len(set(retrieved_ids) & set(ground_truth[:10]))
            accuracy = correct_matches / 10.0
            accuracies.append(accuracy)

            if (i + 1) % 20 == 0:
                logging.info(f"진행률: {i+1}/{len(self.test_queries)} 쿼리 완료")

        avg_latency = statistics.mean(latencies)
        avg_accuracy = statistics.mean(accuracies)
        qps = 1000.0 / avg_latency if avg_latency > 0 else 0

        return avg_latency, avg_accuracy, qps

    def get_memory_usage(self) -> float:
        """현재 PostgreSQL 메모리 사용량 조회 (MB)"""
        memory_sql = text("""
            SELECT sum(resident) / 1024 / 1024 as memory_mb
            FROM pg_stat_activity
            WHERE state = 'active'
        """)

        try:
            result = self.db.execute(memory_sql).fetchone()
            return result.memory_mb if result and result.memory_mb else 0.0
        except:
            return 0.0

    def test_parameter_combination(self, params: HNSWParams) -> PerformanceMetrics:
        """특정 파라미터 조합 테스트"""
        logging.info(f"테스트 시작: {params}")

        # 1. 인덱스 생성
        creation_time = self.create_index_with_params(params)
        if creation_time == float('inf'):
            return None

        # 2. 인덱스 크기 측정
        index_name = f"test_hnsw_m{params.m}_ef{params.ef_construction}"
        index_size = self.get_index_size(index_name)

        # 3. 검색 성능 측정
        try:
            latency, accuracy, qps = self.measure_search_performance(params)
        except Exception as e:
            logging.error(f"검색 성능 측정 실패: {e}")
            return None

        # 4. 메모리 사용량 측정
        memory_usage = self.get_memory_usage()

        # 5. 테스트 인덱스 정리
        drop_sql = text(f"DROP INDEX IF EXISTS {index_name}")
        self.db.execute(drop_sql)
        self.db.commit()

        metrics = PerformanceMetrics(
            params=params,
            index_creation_time=creation_time,
            index_size_mb=index_size,
            search_latency_ms=latency,
            search_accuracy=accuracy,
            memory_usage_mb=memory_usage,
            queries_per_second=qps
        )

        logging.info(f"테스트 완료: {params}")
        logging.info(f"  - 생성시간: {creation_time:.2f}초")
        logging.info(f"  - 인덱스 크기: {index_size:.2f}MB")
        logging.info(f"  - 평균 지연시간: {latency:.2f}ms")
        logging.info(f"  - 정확도: {accuracy:.3f}")
        logging.info(f"  - QPS: {qps:.1f}")

        return metrics

    def run_tuning_experiment(self) -> list[PerformanceMetrics]:
        """전체 튜닝 실험 실행"""
        logging.info("HNSW 파라미터 튜닝 실험 시작")

        # 테스트할 파라미터 조합들
        param_combinations = [
            # m 값 테스트 (ef_construction 고정)
            HNSWParams(m=8, ef_construction=64, ef_search=64),
            HNSWParams(m=16, ef_construction=64, ef_search=64),  # 현재 기본값
            HNSWParams(m=32, ef_construction=64, ef_search=64),
            HNSWParams(m=64, ef_construction=64, ef_search=64),

            # ef_construction 값 테스트 (m 고정)
            HNSWParams(m=16, ef_construction=32, ef_search=64),
            HNSWParams(m=16, ef_construction=128, ef_search=64),
            HNSWParams(m=16, ef_construction=200, ef_search=64),

            # ef_search 값 테스트
            HNSWParams(m=16, ef_construction=64, ef_search=32),
            HNSWParams(m=16, ef_construction=64, ef_search=128),
            HNSWParams(m=16, ef_construction=64, ef_search=200),

            # 최적화된 조합들
            HNSWParams(m=32, ef_construction=128, ef_search=128),
            HNSWParams(m=24, ef_construction=96, ef_search=96),
        ]

        # 테스트 데이터 준비
        self.prepare_test_data(100)

        results = []
        total_combinations = len(param_combinations)

        for i, params in enumerate(param_combinations, 1):
            logging.info(f"\n진행률: {i}/{total_combinations} - {params}")

            try:
                metrics = self.test_parameter_combination(params)
                if metrics:
                    results.append(metrics)
            except Exception as e:
                logging.error(f"파라미터 테스트 실패: {params}, 오류: {e}")
                continue

        return results

    def save_results(self, results: list[PerformanceMetrics], filename: str = None) -> None:
        """결과를 JSON 파일로 저장"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hnsw_tuning_results_{timestamp}.json"

        # 결과를 직렬화 가능한 형태로 변환
        serializable_results = []
        for metrics in results:
            serializable_results.append({
                'params': {
                    'm': metrics.params.m,
                    'ef_construction': metrics.params.ef_construction,
                    'ef_search': metrics.params.ef_search
                },
                'index_creation_time': metrics.index_creation_time,
                'index_size_mb': metrics.index_size_mb,
                'search_latency_ms': metrics.search_latency_ms,
                'search_accuracy': metrics.search_accuracy,
                'memory_usage_mb': metrics.memory_usage_mb,
                'queries_per_second': metrics.queries_per_second
            })

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)

        logging.info(f"결과 저장 완료: {filename}")

    def analyze_results(self, results: list[PerformanceMetrics]) -> dict[str, Any]:
        """결과 분석 및 추천"""
        if not results:
            return {"error": "분석할 결과가 없습니다"}

        # 각 메트릭별 최고 성능
        best_latency = min(results, key=lambda x: x.search_latency_ms)
        best_accuracy = max(results, key=lambda x: x.search_accuracy)
        best_qps = max(results, key=lambda x: x.queries_per_second)
        fastest_build = min(results, key=lambda x: x.index_creation_time)
        smallest_index = min(results, key=lambda x: x.index_size_mb)

        # 균형잡힌 성능 (정규화된 점수 기반)
        def calculate_score(metrics):
            # 정규화 (min-max)
            latencies = [r.search_latency_ms for r in results]
            accuracies = [r.search_accuracy for r in results]
            build_times = [r.index_creation_time for r in results]

            norm_latency = 1 - (metrics.search_latency_ms - min(latencies)) / (max(latencies) - min(latencies))
            norm_accuracy = (metrics.search_accuracy - min(accuracies)) / (max(accuracies) - min(accuracies))
            norm_build_time = 1 - (metrics.index_creation_time - min(build_times)) / (max(build_times) - min(build_times))

            # 가중평균 (정확도 40%, 지연시간 40%, 빌드시간 20%)
            return 0.4 * norm_accuracy + 0.4 * norm_latency + 0.2 * norm_build_time

        best_balanced = max(results, key=calculate_score)

        analysis = {
            "summary": {
                "total_tests": len(results),
                "test_timestamp": datetime.now().isoformat()
            },
            "best_performance": {
                "lowest_latency": {
                    "params": str(best_latency.params),
                    "latency_ms": best_latency.search_latency_ms,
                    "accuracy": best_latency.search_accuracy
                },
                "highest_accuracy": {
                    "params": str(best_accuracy.params),
                    "accuracy": best_accuracy.search_accuracy,
                    "latency_ms": best_accuracy.search_latency_ms
                },
                "highest_qps": {
                    "params": str(best_qps.params),
                    "qps": best_qps.queries_per_second,
                    "accuracy": best_qps.search_accuracy
                },
                "fastest_build": {
                    "params": str(fastest_build.params),
                    "build_time": fastest_build.index_creation_time
                },
                "smallest_index": {
                    "params": str(smallest_index.params),
                    "size_mb": smallest_index.index_size_mb
                }
            },
            "recommended": {
                "balanced_performance": {
                    "params": str(best_balanced.params),
                    "score": calculate_score(best_balanced),
                    "latency_ms": best_balanced.search_latency_ms,
                    "accuracy": best_balanced.search_accuracy,
                    "qps": best_balanced.queries_per_second
                }
            }
        }

        return analysis

    def print_results_table(self, results: list[PerformanceMetrics]) -> None:
        """결과를 표 형태로 출력"""
        if not results:
            print("표시할 결과가 없습니다.")
            return

        print("\n" + "="*120)
        print("HNSW 파라미터 튜닝 결과")
        print("="*120)
        print(f"{'Parameters':<25} {'Build Time':<12} {'Index Size':<12} {'Latency':<10} {'Accuracy':<10} {'QPS':<8}")
        print("-"*120)

        for metrics in sorted(results, key=lambda x: x.search_latency_ms):
            params_str = f"m={metrics.params.m},ef_c={metrics.params.ef_construction},ef_s={metrics.params.ef_search}"
            print(f"{params_str:<25} {metrics.index_creation_time:>8.1f}s    {metrics.index_size_mb:>8.1f}MB   "
                  f"{metrics.search_latency_ms:>7.1f}ms  {metrics.search_accuracy:>7.3f}    {metrics.queries_per_second:>6.1f}")

        print("="*120)


def main():
    """메인 실행 함수"""
    try:
        tuner = HNSWTuner()

        # 튜닝 실험 실행
        results = tuner.run_tuning_experiment()

        if not results:
            logging.error("테스트 결과가 없습니다.")
            return

        # 결과 출력
        tuner.print_results_table(results)

        # 결과 분석
        analysis = tuner.analyze_results(results)

        print("\n" + "="*60)
        print("분석 결과 및 추천")
        print("="*60)
        print(f"총 테스트 수: {analysis['summary']['total_tests']}")
        print("\n최고 성능:")
        print(f"  • 최저 지연시간: {analysis['best_performance']['lowest_latency']['params']} "
              f"({analysis['best_performance']['lowest_latency']['latency_ms']:.1f}ms)")
        print(f"  • 최고 정확도: {analysis['best_performance']['highest_accuracy']['params']} "
              f"({analysis['best_performance']['highest_accuracy']['accuracy']:.3f})")
        print(f"  • 최고 QPS: {analysis['best_performance']['highest_qps']['params']} "
              f"({analysis['best_performance']['highest_qps']['qps']:.1f})")

        print("\n권장 설정 (균형잡힌 성능):")
        recommended = analysis['recommended']['balanced_performance']
        print(f"  • 파라미터: {recommended['params']}")
        print(f"  • 지연시간: {recommended['latency_ms']:.1f}ms")
        print(f"  • 정확도: {recommended['accuracy']:.3f}")
        print(f"  • QPS: {recommended['qps']:.1f}")

        # 결과 저장
        tuner.save_results(results)

        # 분석 결과도 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_filename = f"hnsw_analysis_{timestamp}.json"
        with open(analysis_filename, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)

        logging.info(f"분석 결과 저장: {analysis_filename}")

    except Exception as e:
        logging.error(f"실험 중 오류 발생: {e}")
        raise


if __name__ == "__main__":
    main()
