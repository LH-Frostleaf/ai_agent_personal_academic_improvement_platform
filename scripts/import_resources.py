import csv
from sqlalchemy.orm import Session
from config.database_config import SessionLocal
from models.db_models import KnowledgePoint, Recommendation

def import_resources(csv_path: str):
    db = SessionLocal()
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                kp_id = row.get('kp_id')
                title = row.get('title')
                if not kp_id or not title:
                    continue

                # 查找知识点
                kp = db.query(KnowledgePoint).filter(KnowledgePoint.kp_id == kp_id).first()
                if not kp:
                    print(f"⚠️ 知识点不存在: {kp_id}")
                    continue

                resource = Recommendation(
                    knowledge_point_id=kp.id,
                    title=title,
                    type=row.get('type', 'article'),
                    url=row.get('url', ''),
                    description=row.get('description', ''),
                    difficulty=int(row.get('difficulty', 2)),
                    source=row.get('source', '')
                )
                db.add(resource)
                count += 1

            db.commit()
            print(f"✅ 成功导入 {count} 条资源")

    except Exception as e:
        db.rollback()
        print(f"❌ 导入失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import_resources("../data/resources.csv")