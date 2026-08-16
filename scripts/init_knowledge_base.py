import os
import pandas as pd
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from config.settings import settings
from config.vector_db_config import VECTOR_DB_PATH

# 使用 DashScope embedding（或替换为其他）
embedding_func = OpenAIEmbeddingFunction(
    api_key=settings.DASHSCOPE_API_KEY,
    model_name="qwen3.7-text-embedding",
    api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

client = chromadb.PersistentClient(path=VECTOR_DB_PATH)

def load_all_knowledge(data_dir: str):
    all_ids = []
    all_documents = []  # 存储知识点名称
    all_metadatas = []

    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    if not csv_files:
        print(f"❌ 在 {data_dir} 下未找到任何 CSV 文件")
        return

    for filename in csv_files:
        subject = os.path.splitext(filename)[0]  # 文件名作为学科名
        df = pd.read_csv(os.path.join(data_dir, filename))
        # 确保必要列存在
        if not {'kp_id', 'name'}.issubset(df.columns):  # 判断是否是df.columns子集
            print(f"⚠️ 跳过 {filename}：缺少必要列 (kp_id, name)")
            continue

        for _, row in df.iterrows():
            kp_id = str(row['kp_id'])
            name = str(row['name'])
            if not kp_id or not name:
                continue  # 跳过无效行
            parent_id = str(row.get('parent_id', '')) if pd.notna(row.get('parent_id')) else ''
            all_ids.append(kp_id)
            all_documents.append(name)
            all_metadatas.append({
                "subject": subject,
                "name": name,
                "parent_id": parent_id,
                "kp_id": kp_id  # 元数据也存一份，方便查询
            })
        print(f"✅ 加载 {filename}: {len(df)} 条，有效 {len(all_ids)} 条")

    if all_ids:
        # 清空旧数据：删除并重建 collection
        try:
            client.delete_collection("knowledge_base")
            print("🗑️ 已删除旧 collection")
        except:
            pass
        # 重建
        collection = client.create_collection(
            name="knowledge_base",
            embedding_function=embedding_func,
        )

        # 分批添加（每批最多 20 条，阿里云 embedding 限制）
        batch_size = 20
        total = len(all_ids)
        for i in range(0, total, batch_size):
            batch_ids = all_ids[i:i + batch_size]
            batch_docs = all_documents[i:i + batch_size]
            batch_metas = all_metadatas[i:i + batch_size]
            collection.add(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_metas
            )
            print(f"📦 已导入第 {i + 1}-{min(i + batch_size, total)} 条，共 {total} 条")

        print(f"🎉 总共导入 {total} 个知识点")
    else:
        print("⚠️ 没有有效数据可导入")

if __name__ == "__main__":
    data_dir = "../data/knowledge"
    if not os.path.exists(data_dir):
        print(f"❌ 目录 {data_dir} 不存在，请先创建并放入 CSV 文件")
    else:
        load_all_knowledge(data_dir)