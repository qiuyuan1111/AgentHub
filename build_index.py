import json
from pathlib import Path
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader

import re


CHUNK_SIZE = 80
CHUNK_OVERLAP_SENTENCE = 0
LONG_SENTENCE_OVERLAP_CHARS = 10

BASE_DIR = Path(__file__).resolve().parent

KNOWLEDGE_DIR = BASE_DIR / "data" / "knowledge"

STORAGE_DIR = BASE_DIR / "storage"

INDEX_PATH = STORAGE_DIR / "knowledge.index"

CHUNKS_PATH = STORAGE_DIR / "chunks.json"

embedding_model = SentenceTransformer(
    "BAAI/bge-small-zh-v1.5"
)

def split_long_sentences(
    sentence: str,
    chunk_size: int = 80,
    overlap_chars: int = 10
) -> list[str]:

    if len(sentence) <= chunk_size:
        return [sentence]

    parts = []

    start = 0

    while start < len(sentence):

        end = min(len(sentence), start + chunk_size)

        part = sentence[start:end].strip()

        if part:
            parts.append(part)

        if end >= len(sentence):
            break

        start = end - overlap_chars

    return parts


def split_into_sentences(text: str) -> list[str]:
    # 清理空行
    text = "\n".join(
        line.strip()
        for line in text.splitlines()
        if line.strip()
    )

    # 在中文句号、问号、感叹号、分号后切分
    sentences = re.split(
        r'(?<=[。！？；!?;])',
        text
    )

    results = []
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            results.append(sentence)

    return results

def load_documents() -> list[dict]:
    document = []

    # 把 build_index.py 从单文件读取升级成多文件读取
    for file_path in KNOWLEDGE_DIR.iterdir():

        # TXT / Markdown
        if file_path.suffix.lower()  in [".txt", ".md"]:

            text = file_path.read_text(encoding="utf-8")

            document.append(
                {
                    "text": text,
                    "source": file_path.name,
                    "page": None
                }
            )

        # PDF
        elif file_path.suffix.lower() == ".pdf":
            reader = PdfReader(str(file_path))

            for page_number, page in enumerate(
                reader.pages,
                start=1
            ):
                # 把 PDF 变成 python 字符串
                text = page.extract_text()

                if not text:
                    continue

                text = text.strip()

                if not text:
                    continue

                document.append(
                    {
                        "text": text,
                        "source": file_path.name,
                        "page": page_number
                    }
                )

    return document

def split_document(
    text: str,
    source: str,
    page: int | None = None,
    chunk_size: int = 80,
    overlap_sentences: int = 1,
    overlap_chars: int = 10
) -> list[dict]:

    sentences = split_into_sentences(text)

    chunks = []

    current_sentences = []
    current_length = 0

    chunk_id = 0

    for sentence in sentences:

        sentence_length = len(sentence)

        # 情况1：当前句子本身就超过 chunk_size
        if sentence_length > chunk_size:

            # 先保存前面已经积累的普通句子
            if current_sentences:
                chunk_text = "".join(current_sentences)

                chunks.append(
                    {
                        "text": chunk_text,
                        "source": source,
                        "page": page,
                        "chunk_id": chunk_id
                    }
                )

                chunk_id += 1

                current_sentences = []
                current_length = 0

            # 超长句单独按字符切分
            long_sentence_parts = split_long_sentences(
                sentence=sentence,
                chunk_size=chunk_size,
                overlap_chars=overlap_chars
            )

            # 每个 part 直接作为一个 Chunk
            for part in long_sentence_parts:

                chunks.append(
                    {
                        "text": part,
                        "source": source,
                        "page": page,
                        "chunk_id": chunk_id
                    }
                )

                chunk_id += 1

            # 超长句处理完成，不再进入下面普通句子的逻辑
            continue

        # 情况2：普通句子，可以直接加入当前 Chunk
        # 如果当前 Chunk 加上新句子后没有超过限制
        if current_length + sentence_length <= chunk_size:

            current_sentences.append(sentence)
            current_length += sentence_length

        else:
            # 先保存当前 Chunk
            if current_sentences:

                chunk_text = "".join(current_sentences)
                chunks.append(
                    {
                        "text": chunk_text,
                        "source": source,
                        "page": page,
                        "chunk_id": chunk_id
                    }
                )

                chunk_id += 1

            # 保留上一 Chunk 最后的若干完整句子作为 overlap
            if overlap_sentences > 0:

                overlap = current_sentences[-overlap_sentences:]

            else:
                overlap = []

            overlap_length = sum(len(item) for item in overlap)

            # 如果 overlap + 新句子仍然不超过 chunk_size
            # 才保留 overlap
            if overlap_length + sentence_length <= chunk_size:
                current_sentences = overlap
                current_length = overlap_length
            else:
                current_sentences = []
                current_length = 0

            current_sentences.append(sentence)
            current_length += sentence_length

    # 最后剩下的内容别忘了保存
    if current_sentences:
        chunk_text = "".join(current_sentences)
        chunks.append(
            {
                "text": chunk_text,
                "source": source,
                "page": page,
                "chunk_id": chunk_id
            }
        )
    # 已经是最后一个,chunk_id不用+1
    return chunks



def build_index():

    STORAGE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    documents = load_documents()

    chunks = []

    # 把所有文档 Chunk 合并
    for document in documents:

        document_chunks = split_document(
            text=document["text"],
            source=document["source"],
            page=document["page"],
            chunk_size=CHUNK_SIZE,
            overlap_sentences=CHUNK_OVERLAP_SENTENCE,
            overlap_chars=LONG_SENTENCE_OVERLAP_CHARS
        )

        chunks.extend(document_chunks)

    chunk_texts = []

    for chunk in chunks:
        chunk_texts.append(chunk["text"])

    embeddings = embedding_model.encode(
        chunk_texts,
        normalize_embeddings=True
    )

    embeddings = np.asarray(
        embeddings,
        dtype="float32"
    )

    # 取得向量维度
    dimension = embeddings.shape[1]

    # 创建 FAISS 索引仓库
    index = faiss.IndexFlatIP(dimension)

    # 放入向量
    index.add(embeddings)

    # print("索引中的向量数量:", index.ntotal)

    # 把 FAISS 保存到硬盘
    faiss.write_index(
        index,
        str(INDEX_PATH)  # 因为 INDEX_PATH 原本是Path对象
    )

    # 保存 Chunk
    with CHUNKS_PATH.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            chunks,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("知识库索引构建完成")
    print("Chunk数量:", len(chunks))
    print("Embedding维度:", dimension)
    print("FAISS向量数量:", index.ntotal)
    print("索引保存位置:", INDEX_PATH)

if __name__ == "__main__":
    build_index()