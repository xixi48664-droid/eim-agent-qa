"""将 docs/data/ 下的 .yaml 流程资料导入 tutorial + tutorial_step 表"""
import sys, os, uuid, yaml, glob

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.entities.tutorial import Tutorial, TutorialStep

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:1130@localhost:3306/eim_agent_qa")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "data")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def import_all():
    session = Session()
    files = sorted(glob.glob(os.path.join(DATA_DIR, "*.yaml")))
    created = 0
    skipped = 0

    for fp in files:
        name = os.path.basename(fp)
        with open(fp, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        tut = data.get("tutorial", {})
        process_name = tut.get("process_name", "").strip()
        if not process_name:
            print(f"[SKIP] {name}: 缺少 process_name")
            continue

        # 检查是否已存在
        existing = session.query(Tutorial).filter(
            Tutorial.process_name == process_name
        ).first()
        if existing:
            print(f"[SKIP] {name}: process_name='{process_name}' 已存在")
            skipped += 1
            continue

        tutorial = Tutorial(
            tutorial_id=uuid.uuid4().hex,
            process_name=process_name,
            total_steps=tut.get("total_steps", len(data.get("steps", []))),
            estimated_time=tut.get("estimated_time", ""),
        )
        session.add(tutorial)
        session.flush()  # 获取 tutorial_id

        steps_data = data.get("steps", [])
        step_entities = []
        for s in steps_data:
            step = TutorialStep(
                step_id=uuid.uuid4().hex,
                tutorial_id=tutorial.tutorial_id,
                step_no=s["step_no"],
                step_title=s.get("step_title", ""),
                step_content=s.get("step_content", ""),
                note=s.get("note", ""),
                faq=s.get("faq", ""),
            )
            step_entities.append(step)

        session.add_all(step_entities)
        session.commit()
        created += 1
        print(f"[OK] {name}: '{process_name}' ({len(step_entities)} 步)")

    session.close()
    print(f"\n完成: 新增 {created}, 跳过(已存在) {skipped}")

if __name__ == "__main__":
    import_all()
