"""
Qdrant 本地 → Docker 迁移脚本

将本地 Qdrant 所有 collection 数据迁移到 Docker Qdrant。
本地 scroll() 返回 Record 对象，需转换为 PointStruct 后 upsert 到远程。

用法:
    python scripts/migrate_qdrant_to_docker.py
    python scripts/migrate_qdrant_to_docker.py --dry-run
    python scripts/migrate_qdrant_to_docker.py --batch-size 200
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

QDRANT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "qdrant")
DOCKER_HOST = "localhost"
DOCKER_PORT = 6333


def main():
    parser = argparse.ArgumentParser(description="Qdrant 本地 → Docker 迁移")
    parser.add_argument("--dry-run", action="store_true", help="预览模式")
    parser.add_argument("--batch-size", type=int, default=200, help="每批写入点数 (默认 200)")
    parser.add_argument("--collection", type=str, help="只迁移指定 collection")
    args = parser.parse_args()

    local = QdrantClient(path=QDRANT_DIR)
    remote = QdrantClient(host=DOCKER_HOST, port=DOCKER_PORT, timeout=120)

    print("=" * 60)
    print("Qdrant 本地 → Docker 迁移")
    print(f"  本地: {QDRANT_DIR}")
    print(f"  远程: {DOCKER_HOST}:{DOCKER_PORT}")
    print(f"  批次大小: {args.batch_size}")
    if args.dry_run:
        print(f"  模式: 预览 (不实际写入)")
    print()

    # 1. 列出所有 collection
    local_collections = local.get_collections().collections
    print(f"本地 collections: {len(local_collections)}")
    for c in local_collections:
        info = local.get_collection(c.name)
        print(f"  {c.name}: {info.points_count} points")
    print()

    if args.collection:
        local_collections = [c for c in local_collections if c.name == args.collection]
        if not local_collections:
            print(f"未找到 collection: {args.collection}")
            return

    # 2. 逐个迁移
    for coll in local_collections:
        name = coll.name
        print(f"\n{'─' * 60}")
        print(f"迁移 collection: {name}")

        local_info = local.get_collection(name)
        total_points = local_info.points_count
        print(f"  总点数: {total_points}")

        if total_points == 0:
            print(f"  跳过 (空)")
            continue

        # 确保远程 collection 存在
        if not remote.collection_exists(name):
            # 从本地获取 vector 配置
            config = local_info.config
            vector_size = config.params.vectors.size
            distance = config.params.vectors.distance
            remote.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=vector_size, distance=distance),
            )
            print(f"  远程 collection 已创建 (dim={vector_size})")

        if args.dry_run:
            print(f"  [预览] 将迁移 {total_points} 个点")
            continue

        # 3. 滚动读取 + 批量写入
        migrated = 0
        offset = None
        batch_num = 0
        t_start = time.time()

        while True:
            records, offset = local.scroll(
                collection_name=name,
                limit=args.batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=True,
            )

            if not records:
                break

            # Record → PointStruct
            points = []
            for r in records:
                points.append(PointStruct(
                    id=r.id,
                    vector=r.vector,
                    payload=r.payload,
                ))

            remote.upsert(collection_name=name, points=points)
            migrated += len(points)
            batch_num += 1

            elapsed = time.time() - t_start
            rate = migrated / elapsed if elapsed > 0 else 0
            pct = migrated / total_points * 100
            print(f"  [{migrated}/{total_points} ({pct:.1f}%)] "
                  f"批次 {batch_num}, {rate:.0f} pts/s", end="\r")

            if offset is None:
                break

        elapsed = time.time() - t_start
        print(f"\n  完成: {migrated} 个点, 耗时 {elapsed:.1f}s, "
              f"速率 {migrated/elapsed:.0f} pts/s")

    # 4. 验证
    print(f"\n{'=' * 60}")
    print("验证远程 collections:")
    for c in local_collections:
        name = c.name
        remote_info = remote.get_collection(name)
        print(f"  {name}: {remote_info.points_count} points")

    local.close()
    remote.close()
    print("\n迁移完成!")


if __name__ == "__main__":
    main()
