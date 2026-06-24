"""景区知识库 - 基于 ChromaDB 向量存储"""
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import Chroma

class KnowledgeBase:
    def __init__(self, data_dir="../data/raw", vector_db_path="../data/chroma_storage"):
        self.data_dir = data_dir
        self.vector_db_path = vector_db_path
        
        # 直接填入 KEY，彻底解决报错
        self.embeddings = DashScopeEmbeddings(
            model="text-embedding-v2",
            dashscope_api_key="sk-7d9eb5d3d31d4eddaed244c54742f2b7"
        )
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
        )
        
        self.collection_name = "lingshan_knowledge"
    
    def load_documents(self):
        docs = []
        if not os.path.exists(self.data_dir):
            print(f"⚠️ 目录不存在：{self.data_dir}")
            return docs

        for filename in sorted(os.listdir(self.data_dir)):
            if filename.endswith('.txt'):
                filepath = os.path.join(self.data_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        docs.append({
                            'content': content,
                            'source': filename,
                        })
                        print(f"  📄 {filename}: {len(content)} 字")
                except:
                    pass
        print(f"✅ 共加载 {len(docs)} 个文档")
        return docs
    
    def build_vector_store(self):
        docs = self.load_documents()
        
        all_texts = []
        all_metadatas = []
        for doc in docs:
            chunks = self.splitter.split_text(doc['content'])
            for i, chunk in enumerate(chunks):
                all_texts.append(chunk)
                all_metadatas.append({'source': doc['source'], 'chunk_id': i})
        
        print(f"✂️  切分为 {len(all_texts)} 个文本块")
        
        vector_store = Chroma.from_texts(
            texts=all_texts,
            embedding=self.embeddings,
            metadatas=all_metadatas,
            collection_name=self.collection_name,
            persist_directory=self.vector_db_path
        )
        
        print(f"✅ 向量库构建完成：{len(all_texts)} 条记录")
        return vector_store
    
    def search(self, query: str, k: int = 5):
        vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.vector_db_path
        )
        docs = vector_store.similarity_search(query, k=k)
        results = []
        for doc in docs:
            results.append({
                'content': doc.page_content,
                'source': doc.metadata.get('source', ''),
            })
        return results

if __name__ == "__main__":
    print("=" * 50)
    print("🏗️  灵山胜境知识库构建 (ChromaDB)")
    print("=" * 50)
    
    kb = KnowledgeBase()
    kb.build_vector_store()
    
    print("\n" + "=" * 50)
    print("🔍 检索测试")
    print("=" * 50)
    
    queries = ["灵山大佛有多高", "灵山胜境在哪里", "门票多少钱"]
    for q in queries:
        print(f"\n❓ {q}")
        results = kb.search(q, k=2)
        if results:
            r = results[0]
            print(f"  📖 来源: {r['source']}")
            print(f"  📝 {r['content'][:150]}...")
        else:
            print("  ⚠️  未找到相关结果")