import argparse

from crawlers.gb_crawler import crawl_gb_standards
from crawlers.ipc_crawler import crawl_ipc_catalog
from crawlers.iso_crawler import crawl_iso_from_csv
from crawlers.jedec_crawler import crawl_jedec_standards
from crawlers.official_catalog import crawl_official_catalog
from crawlers.sjt_crawler import crawl_sjt_standards
from output.yaml_generator import generate_yaml
from processors.enrich_existing_yaml import enrich_file
from utils.standard_metadata import RECOMMENDED_STANDARDS
from config import OUTPUT_DIR


def generate_recommended_templates():
    """按行业规范录入格式.md 的推荐清单生成待补全文档。"""
    for code, metadata in RECOMMENDED_STANDARDS.items():
        generate_yaml(
            {
                "standard_code": code,
                "standard_name": metadata["standard_name"],
                "section": "",
                "summary": "",
                "tags": metadata["tags"],
                "related_process": metadata["related_process"],
            },
            OUTPUT_DIR,
        )


def parse_args():
    parser = argparse.ArgumentParser(description="行业规范 YAML 采集与模板生成")
    parser.add_argument(
        "--source",
        choices=("recommended", "official", "gb", "sjt", "jedec", "ipc", "iso", "all"),
        default="all",
        help="采集来源；默认生成官方目录条目并从可访问官网采集元数据",
    )
    parser.add_argument("--max-pages", type=int, default=10, help="GB/SJ/T 最大抓取页数或关键词批次数")
    parser.add_argument("--limit", type=int, default=0, help="官方目录条目上限，0 表示不限制")
    parser.add_argument("--skip-enrich", action="store_true", help="跳过非真实 section 清理和 summary 二次补全")
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"输出目录: {OUTPUT_DIR}")

    if args.source in ("recommended", "all"):
        print("生成推荐规范 YAML 模板...")
        generate_recommended_templates()
    if args.source in ("official", "all"):
        print("生成文档指定来源的官方目录 YAML...")
        crawl_official_catalog(limit=args.limit or None)
    if args.source in ("gb", "all"):
        print("开始爬取 GB/T 标准...")
        crawl_gb_standards(max_pages=args.max_pages)
    if args.source in ("sjt", "all"):
        print("开始爬取 SJ/T 标准...")
        crawl_sjt_standards(max_pages=args.max_pages)
    if args.source in ("jedec", "all"):
        print("开始爬取 JEDEC 标准...")
        crawl_jedec_standards()
    if args.source in ("ipc", "all"):
        print("开始爬取 IPC 目录...")
        crawl_ipc_catalog()
    if args.source in ("iso", "all"):
        print("开始处理 ISO CSV 元数据...")
        crawl_iso_from_csv()

    if not args.skip_enrich:
        count = 0
        for path in sorted(OUTPUT_DIR.glob("*.yaml")):
            if enrich_file(path):
                count += 1
        print(f"已清理非真实 section 并重写电子制造业重点 summary: {count} 个 YAML")

    print("全部完成")


if __name__ == "__main__":
    main()
