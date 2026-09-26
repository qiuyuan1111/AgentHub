from pathlib import Path

from build_index import split_document

file_path = Path("data/knowledge/refund_policy.txt")

text = file_path.read_text(encoding="utf-8")

chunks = split_document(
    text=text,
    source=file_path.name,
    chunk_size=80,
    overlap=20
)

for chunk in chunks:
    print("=" * 50)
    print("Source:", chunk["source"])
    print("Chunk ID:", chunk["chunk_id"])
    print("长度:", len(chunk["text"]))
    print("内容:")
    print(chunk["text"])