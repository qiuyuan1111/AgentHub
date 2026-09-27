from pathlib import Path

from build_index import split_document

file_path = Path("data/knowledge/refund_policy.txt")

# text = file_path.read_text(encoding="utf-8")

text = (
    "这是第一条正常规则。"
    "这是一条非常非常长的测试规则，"
    "为了测试当单个句子的长度超过chunk_size以后程序是否能够继续正确切分，"
    "我们故意把这一句话写得特别长特别长特别长特别长特别长特别长。"
    "这是最后一条正常规则。"
)
chunks = split_document(
    text=text,
    source="text.txt",
    chunk_size=40,
    overlap_sentences=1
)

for chunk in chunks:
    print("=" * 50)
    print("Source:", chunk["source"])
    print("Chunk ID:", chunk["chunk_id"])
    print("长度:", len(chunk["text"]))
    print("内容:")
    print(chunk["text"])