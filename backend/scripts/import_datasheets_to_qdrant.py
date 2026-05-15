"""
电子元器件 Datasheet 导入 Qdrant 脚本。

流程: 读取 component → 下载 PDF → 解析文本 → 切片 → 向量化 → 写入 Qdrant

用法:
    python scripts/import_datasheets_to_qdrant.py --limit 100
    python scripts/import_datasheets_to_qdrant.py --limit 100 --dry-run
    python scripts/import_datasheets_to_qdrant.py --category MCU/MPU --limit 50
    python scripts/import_datasheets_to_qdrant.py --limit 100 --force
    python scripts/import_datasheets_to_qdrant.py --limit 500 --resume
"""

import argparse
import hashlib
import os
import sys
import time
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from app.db.mysql import SessionLocal
from app.entities.component_info import Component
from app.entities.datasheet import DatasheetRecord
from app.external.model_client import ModelClient

# ── 常量 ──
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "datasheets")
QDRANT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "qdrant")
COLLECTION_NAME = "component_datasheets"
EMBEDDING_DIM = 1024
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
DOWNLOAD_TIMEOUT = 120
MAX_PDF_SIZE_MB = 30  # 超过此大小的视为目录/手册，跳过


def _hash_file(filepath: str) -> str:
    """计算文件 SHA256"""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _hash_url(url: str) -> str:
    """对 URL 取 hash 用作文件名"""
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def _cleanup_pdf(record, keep_pdf: bool):
    """嵌入成功后删除本地 PDF，除非 --keep-pdf"""
    if keep_pdf:
        return
    if record.local_path and os.path.exists(record.local_path):
        try:
            os.remove(record.local_path)
        except OSError:
            pass
    record.local_path = None


def _chunk_text(text: str, page: int, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """将文本按 chunk_size 切片，返回 [{page, chunk_index, text}, ...]"""
    chunks = []
    start = 0
    idx = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append({"page": page, "chunk_index": idx, "text": chunk_text})
            idx += 1
        start += size - overlap
    return chunks


def _parse_pdf(filepath: str) -> list[dict]:
    """解析 PDF，返回 [{page, text}, ...]。解析失败抛异常。"""
    try:
        import pdfplumber
        pages = []
        with pdfplumber.open(filepath) as pdf:
            for i, p in enumerate(pdf.pages):
                text = p.extract_text()
                if text and text.strip():
                    pages.append({"page": i + 1, "text": text.strip()})
        if pages:
            return pages
    except Exception:
        pass

    # fallback: pypdf
    try:
        from pypdf import PdfReader
        reader = PdfReader(filepath)
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                pages.append({"page": i + 1, "text": text.strip()})
        if pages:
            return pages
    except Exception:
        pass

    raise RuntimeError("无法解析 PDF (pdfplumber/pypdf 均失败，可能是扫描版)")


def _ensure_collection(client: QdrantClient):
    """确保 Qdrant collection 存在"""
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )


def _prepare_record(db, component: Component, source_url: str, status: str = "pending") -> DatasheetRecord:
    """查找或创建 DatasheetRecord"""
    record = db.query(DatasheetRecord).filter(
        DatasheetRecord.component_id == component.component_id,
        DatasheetRecord.source_url == source_url,
    ).first()
    if not record:
        record = DatasheetRecord(
            component_id=component.component_id,
            source_url=source_url,
            status=status,
        )
        db.add(record)
        db.flush()
    return record


def process_one(component: Component, db, model_client: ModelClient, qdrant: QdrantClient,
                force: bool = False, dry_run: bool = False, keep_pdf: bool = False) -> dict:
    """处理单个元器件的 datasheet。

    返回 {"status": "...", "chunks": N, "error": "..."}
    """
    url = (component.datasheet_url or "").strip()
    if not url:
        return {"status": "skipped", "chunks": 0, "error": "无 datasheet_url"}
    if url.startswith("//"):
        url = "https:" + url

    record = _prepare_record(db, component, url)

    # 断点续跑: 已成功的不重复处理
    if record.status == "embedded" and not force:
        return {"status": "skipped", "chunks": record.chunk_count, "error": "已嵌入"}

    # 1. 下载 PDF
    if record.status in ("pending", "failed") or force:
        if dry_run:
            record.status = "downloaded"
            return {"status": "dry_run", "chunks": 0, "error": ""}

        url_hash = _hash_url(url)
        local_path = os.path.join(DATA_DIR, f"{url_hash}.pdf")
        os.makedirs(DATA_DIR, exist_ok=True)

        try:
            print(f"    下载: {url[:80]}...")
            browser_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Accept": "text/html,application/pdf,application/xhtml+xml,*/*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "identity",
                "Referer": "https://www.google.com/",
            }
            with httpx.Client(timeout=DOWNLOAD_TIMEOUT, follow_redirects=True) as client:
                # 先检查文件大小，跳过超大 PDF
                head = client.head(url, headers=browser_headers)
                cl = int(head.headers.get("content-length", 0))
                if cl > MAX_PDF_SIZE_MB * 1024 * 1024:
                    size_mb = cl / 1024 / 1024
                    raise RuntimeError(f"PDF 过大 ({size_mb:.0f}MB > {MAX_PDF_SIZE_MB}MB 上限)，可能是产品目录")
                resp = client.get(url, headers=browser_headers)
            if resp.status_code != 200:
                raise RuntimeError(f"HTTP {resp.status_code}")
            content_type = resp.headers.get("content-type", "")
            if "application/pdf" not in content_type:
                # 有些站点返回 HTML 而不是 PDF（如 Molex part-detail 页依赖 JS 触发下载）
                body_preview = resp.text[:200] if resp.text else ""
                raise RuntimeError(f"非 PDF 响应 (Content-Type: {content_type})")
            with open(local_path, "wb") as f:
                f.write(resp.content)
        except Exception as e:
            record.status = "failed"
            record.error_message = f"下载失败: {str(e)[:500]}"
            db.commit()
            print(f"    [失败] 下载: {str(e)[:80]}")
            return {"status": "failed", "chunks": 0, "error": record.error_message}

        record.local_path = local_path
        record.file_hash = _hash_file(local_path)
        record.status = "downloaded"
        db.commit()
        print(f"    已下载: {os.path.basename(local_path)} ({os.path.getsize(local_path)/1024:.0f}KB)")
    else:
        local_path = record.local_path
        if not local_path or not os.path.exists(local_path):
            record.status = "failed"
            record.error_message = f"本地文件丢失: {local_path}"
            db.commit()
            return {"status": "failed", "chunks": 0, "error": record.error_message}

    # 2. 按文件 hash 查重 — 同一份 PDF 可能被多个 component 引用
    file_hash = record.file_hash or _hash_file(local_path)
    record.file_hash = file_hash

    existing = db.query(DatasheetRecord).filter(
        DatasheetRecord.file_hash == file_hash,
        DatasheetRecord.status == "embedded",
        DatasheetRecord.record_id != record.record_id,
    ).first()
    if existing:
        record.status = "embedded"
        record.chunk_count = existing.chunk_count
        _cleanup_pdf(record, keep_pdf)
        db.commit()
        print(f"    [跳过] 重复 PDF (已由 {existing.record_id[:8]} 处理), {existing.chunk_count} chunks")
        return {"status": "embedded", "chunks": existing.chunk_count, "error": ""}

    # 3. 解析 PDF
    if record.status == "downloaded" or force:
        if dry_run:
            record.status = "parsed"
            return {"status": "dry_run", "chunks": 0, "error": ""}

        try:
            pages = _parse_pdf(local_path)
        except Exception as e:
            record.status = "failed"
            record.error_message = f"解析失败: {str(e)[:500]}"
            _cleanup_pdf(record, keep_pdf)
            db.commit()
            print(f"    [失败] 解析: {str(e)[:80]}")
            return {"status": "failed", "chunks": 0, "error": record.error_message}

        if not pages:
            record.status = "failed"
            record.error_message = "PDF 无可提取文本（可能是扫描版）"
            _cleanup_pdf(record, keep_pdf)
            db.commit()
            print(f"    [失败] PDF 无可提取文本")
            return {"status": "failed", "chunks": 0, "error": record.error_message}

        print(f"    解析出 {len(pages)} 页文本, 共 {sum(len(p['text']) for p in pages)} 字符")
    else:
        # 已经 parsed 过，重新解析
        try:
            pages = _parse_pdf(local_path)
        except Exception as e:
            record.status = "failed"
            record.error_message = f"重新解析失败: {str(e)[:500]}"
            _cleanup_pdf(record, keep_pdf)
            db.commit()
            return {"status": "failed", "chunks": 0, "error": record.error_message}

    # 4. 切分 chunk
    all_chunks = []
    for page_info in pages:
        chunks = _chunk_text(page_info["text"], page_info["page"])
        all_chunks.extend(chunks)

    if not all_chunks:
        record.status = "failed"
        record.error_message = "切分后无有效文本块"
        db.commit()
        return {"status": "failed", "chunks": 0, "error": record.error_message}

    print(f"    切分为 {len(all_chunks)} 个 chunk")

    if dry_run:
        record.status = "embedded"
        record.chunk_count = len(all_chunks)
        db.commit()
        return {"status": "dry_run", "chunks": len(all_chunks), "error": ""}

    # 5. 向量化 + 写入 Qdrant（分批，带重试）
    component_id = component.component_id
    model_name = component.model or ""
    manufacturer = component.manufacturer or ""
    category = component.type or ""

    BATCH_SIZE = 10
    all_points = []
    for batch_start in range(0, len(all_chunks), BATCH_SIZE):
        batch = all_chunks[batch_start:batch_start + BATCH_SIZE]
        texts = [c["text"] for c in batch]
        if batch_start == 0:
            print(f"    向量化 {len(all_chunks)} 个 chunk (每批 {BATCH_SIZE}) ...")

        last_error = None
        for attempt in range(3):
            try:
                embeddings = model_client.embedTexts(texts)
                if not embeddings or len(embeddings) != len(texts):
                    raise RuntimeError(f"Embedding 返回数量不匹配: {len(embeddings)} vs {len(texts)}")

                for chunk, emb in zip(batch, embeddings):
                    point_id = uuid4().hex
                    all_points.append(PointStruct(
                        id=point_id,
                        vector=emb,
                        payload={
                            "component_id": component_id,
                            "model": model_name,
                            "manufacturer": manufacturer,
                            "category": category,
                            "datasheet_url": url,
                            "local_path": record.local_path,
                            "file_hash": record.file_hash,
                            "page": chunk["page"],
                            "chunk_index": chunk["chunk_index"],
                            "text": chunk["text"],
                        },
                    ))
                break
            except Exception as e:
                last_error = e
                if attempt < 2:
                    wait = (attempt + 1) * 2
                    print(f"    [重试 {attempt+1}/3] 批次 {batch_start//BATCH_SIZE+1} 失败: {str(e)[:80]}, {wait}s 后重试...")
                    time.sleep(wait)
                else:
                    record.status = "failed"
                    record.error_message = f"向量化失败 (批次{batch_start//BATCH_SIZE+1}): {str(last_error)[:500]}"
                    db.commit()
                    print(f"    [失败] 向量化: {str(last_error)[:80]}")
                    return {"status": "failed", "chunks": 0, "error": record.error_message}

    try:
        qdrant.upsert(collection_name=COLLECTION_NAME, points=all_points)
    except Exception as e:
        record.status = "failed"
        record.error_message = f"Qdrant 写入失败: {str(e)[:500]}"
        db.commit()
        print(f"    [失败] Qdrant 写入: {str(e)[:80]}")
        return {"status": "failed", "chunks": 0, "error": record.error_message}

    # 6. 更新状态，清理 PDF
    record.status = "embedded"
    record.chunk_count = len(all_chunks)
    _cleanup_pdf(record, keep_pdf)
    db.commit()
    print(f"    写入 Qdrant 成功: {len(all_chunks)} chunks" + (" (PDF已删除)" if not keep_pdf else ""))
    return {"status": "embedded", "chunks": len(all_chunks), "error": ""}


def main():
    parser = argparse.ArgumentParser(description="电子元器件 Datasheet 导入 Qdrant")
    parser.add_argument("--limit", type=int, default=100, help="最多处理多少条 (默认 100)")
    parser.add_argument("--category", type=str, help="只处理指定分类")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不下载/不写 Qdrant")
    parser.add_argument("--force", action="store_true", help="强制重新处理所有记录")
    parser.add_argument("--resume", action="store_true", help="断点续跑：跳过已嵌入的")
    parser.add_argument("--offset", type=int, default=0, help="跳过前 N 条")
    parser.add_argument("--keep-pdf", action="store_true", help="保留本地 PDF 文件（默认嵌入后删除）")
    args = parser.parse_args()

    db = SessionLocal()
    model_client = ModelClient()
    qdrant = QdrantClient(host="localhost", port=6333, timeout=60)
    _ensure_collection(qdrant)

    query = db.query(Component).filter(Component.datasheet_url != "", Component.datasheet_url.isnot(None))
    if args.category:
        query = query.filter(Component.type == args.category)

    total_available = query.count()
    components = query.order_by(Component.model).offset(args.offset).limit(args.limit).all()

    print(f"Datasheet 导入 Qdrant")
    print(f"  符合条件的元器件: {total_available}")
    print(f"  本次处理: {len(components)} 条")
    print(f"  模式: {'预览' if args.dry_run else ('强制' if args.force else ('续跑' if args.resume else '正常'))}")
    print()

    stats = {"embedded": 0, "skipped": 0, "failed": 0, "dry_run": 0, "total_chunks": 0}
    stop_file = os.path.join(os.path.dirname(__file__), "..", ".stop_import")
    last_processed = 0
    try:
        for i, comp in enumerate(components):
            last_processed = i
            if os.path.exists(stop_file):
                print(f"检测到停止信号，已处理 {i} 条，安全退出")
                os.remove(stop_file)
                break
            print(f"[{i+1}/{len(components)}] {comp.model} ({comp.type or 'N/A'})")
            try:
                result = process_one(comp, db, model_client, qdrant,
                                     force=args.force or not args.resume,
                                     dry_run=args.dry_run,
                                     keep_pdf=args.keep_pdf)
            except Exception as e:
                result = {"status": "failed", "chunks": 0, "error": str(e)[:200]}
                print(f"    [异常] {str(e)[:100]}")
            stats[result["status"]] = stats.get(result["status"], 0) + 1
            stats["total_chunks"] += result.get("chunks", 0)
            print("", flush=True)
            if i < len(components) - 1:
                time.sleep(0.5)
    except Exception as e:
        print(f"\n[致命错误] 第 {last_processed+1} 条后崩溃: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n{'='*50}")
    print(f"处理完成:")
    for k, v in stats.items():
        if k != "total_chunks":
            print(f"  {k}: {v}")
    print(f"  total_chunks: {stats['total_chunks']}")

    # Qdrant collection 统计
    info = qdrant.get_collection(COLLECTION_NAME)
    print(f"\nQdrant collection '{COLLECTION_NAME}': {info.points_count} points")

    db.close()


if __name__ == "__main__":
    main()
