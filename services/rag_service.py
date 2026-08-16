import chromadb
from config.settings import settings
from config.vector_db_config import VECTOR_DB_PATH
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

# 初始化 embedding 函数（与初始化脚本一致）
embedding_func = OpenAIEmbeddingFunction(
    api_key=settings.DASHSCOPE_API_KEY,
    model_name="qwen3.7-text-embedding",
    api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
)


class RAGRetriever:
    def __init__(self):
        try:
            self.client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
            self.collection = self.client.get_collection("knowledge_base")
        except Exception as e:
            print(f"向量库导入出错: {e}")

    def retrieve(self, query: str, top_k: int = 5, subject: str = None):
        """
        检索知识点
        :param query: 查询文本（OCR内容）
        :param top_k: 返回数量
        :param subject: 学科名称（对应 CSV 文件名），用于过滤
        """
        where_filter = {}
        if subject:
            where_filter = {"subject": subject}
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter if where_filter else None
        )
        if not results['ids'] or not results['ids'][0]:
            return []
        kps = []
        for i, kp_id in enumerate(results['ids'][0]):
            kps.append({
                "kp_id": kp_id,
                "name": results['metadatas'][0][i]['name'],
                "subject": results['metadatas'][0][i]['subject'],
                "parent_id": results['metadatas'][0][i].get('parent_id', ''),
                "distance": results['distances'][0][i] if results.get('distances') else 1.0,
            })
        return kps


# 单例
retriever = RAGRetriever()