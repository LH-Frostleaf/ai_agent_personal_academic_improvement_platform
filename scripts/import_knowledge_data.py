import os
import pandas as pd
from sqlalchemy.orm import Session
from config.database_config import SessionLocal
from models.db_models import Subject, KnowledgePoint

def import_knowledge_data(data_dir: str):
    db = SessionLocal()
    try:
        # 清空旧数据（开发阶段）
        db.query(KnowledgePoint).delete()
        db.query(Subject).delete()
        db.commit()

        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        if not csv_files:
            print("❌ 未找到 CSV 文件")
            return

        subject_cache = {}

        for filename in csv_files:
            subject_name = os.path.splitext(filename)[0]
            df = pd.read_csv(os.path.join(data_dir, filename))

            if not {'kp_id', 'name'}.issubset(df.columns):
                print(f"⚠️ 跳过 {filename}：缺少必要列")
                continue

            # 获取或创建学科
            subject = db.query(Subject).filter(Subject.name == subject_name).first()
            if not subject:
                subject = Subject(name=subject_name, sort_order=len(subject_cache))
                db.add(subject)
                db.flush()
                subject_cache[subject_name] = subject
                print(f"📚 创建学科: {subject_name}")
            else:
                subject_cache[subject_name] = subject

            # 导入知识点
            for _, row in df.iterrows():
                kp_id = str(row['kp_id'])
                name = str(row['name'])
                if not kp_id or not name:
                    continue

                existing = db.query(KnowledgePoint).filter(
                    KnowledgePoint.kp_id == kp_id
                ).first()
                if existing:
                    continue

                kp = KnowledgePoint(
                    kp_id=kp_id,
                    subject_id=subject.id,
                    name=name,
                    description=row.get('description', '') if pd.notna(row.get('description')) else None,
                    parent_kp_id=str(row.get('parent_id', '')) if pd.notna(row.get('parent_id')) else None
                )
                db.add(kp)

            print(f"✅ 导入 {filename}: {len(df)} 条知识点")

        db.commit()
        print(f"🎉 导入完成！学科数: {db.query(Subject).count()}, 知识点数: {db.query(KnowledgePoint).count()}")

    except Exception as e:
        db.rollback()
        print(f"❌ 导入失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    data_dir = "../data/knowledge"
    if not os.path.exists(data_dir):
        print(f"❌ 目录 {data_dir} 不存在")
    else:
        import_knowledge_data(data_dir)