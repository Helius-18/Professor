import streamlit as st
import time
import os
import json
import numpy as np

from langchain_openai import OpenAIEmbeddings

try:
    import faiss
except Exception:
    faiss = None

enable_upload = False

uploaded_file = st.file_uploader("Choose a file")

if uploaded_file is not None:
    # Validate mime/type
    if uploaded_file.type not in ("text/plain", "text/x-python", "application/octet-stream"):
        enable_upload = False
        st.error("Only plain text files are supported.")
    else:
        enable_upload = True

# Only show the Upload button when a valid file is present
upload_clicked = st.button("Upload", type="primary", disabled=not enable_upload)

if upload_clicked and uploaded_file is not None and enable_upload:
    progress_text = "Uploading file..."
    my_bar = st.progress(0, text=progress_text)

    # prepare documents directory (inside ChatBot folder)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    docs_dir = os.path.join(base_dir, "documents")
    os.makedirs(docs_dir, exist_ok=True)

    filename = getattr(uploaded_file, "name", f"upload_{int(time.time())}.txt")
    dest_path = os.path.join(docs_dir, filename)

    # read text content
    try:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass
        raw = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()
        # decode to text for embedding
        try:
            text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else str(raw)
        except Exception:
            text = raw.decode("utf-8", errors="ignore") if isinstance(raw, (bytes, bytearray)) else str(raw)

        # chunk text into pieces (simple paragraph/window splitter)
        def chunk_text(text: str, max_chars: int = 1000):
            paras = [p.strip() for p in text.split("\n\n") if p.strip()]
            chunks = []
            for p in paras:
                if len(p) <= max_chars:
                    chunks.append(p)
                    continue
                start = 0
                while start < len(p):
                    chunk = p[start : start + max_chars]
                    chunks.append(chunk)
                    start += max_chars
            if not chunks:
                # fallback: whole text
                chunks = [text]
            return chunks

        chunks = chunk_text(text)

        # Build embeddings in batches and save a persistent vector store (embeddings + metadata)
        embeddings = OpenAIEmbeddings(api_key='api-key')

        total_chunks = len(chunks)
        batch = 8
        vectors = []
        metadata = []

        # destination paths for FAISS index and metadata (overwrite existing)
        base_name = 'context'
        faiss_path = os.path.join(docs_dir, f"{base_name}.faiss")
        meta_path = os.path.join(docs_dir, f"{base_name}.meta.jsonl")

        if faiss is None:
            my_bar.empty()
            st.error("FAISS is not installed. Please install faiss-cpu to enable persistent vector indexes.")
            raise RuntimeError("faiss not installed")

        # remove old files if present
        try:
            if os.path.exists(faiss_path):
                os.remove(faiss_path)
            if os.path.exists(meta_path):
                os.remove(meta_path)
        except Exception:
            pass

        processed = 0
        for i in range(0, total_chunks, batch):
            batch_texts = chunks[i : i + batch]
            try:
                batch_vecs = embeddings.embed_documents(batch_texts)
            except Exception as e:
                st.error(f"Embedding failed: {e}")
                my_bar.empty()
                raise

            for j, vec in enumerate(batch_vecs):
                vectors.append(np.array(vec, dtype=np.float32))
                metadata.append({"id": f"{i+j}", "text": batch_texts[j], "source": filename})

            processed += len(batch_texts)
            pct = int((processed / total_chunks) * 90)  # leave room for index build step
            my_bar.progress(min(pct, 90), text="Embedding text and building vectors...")

        # build FAISS index (cosine via normalized vectors + IndexFlatIP)
        try:
            vecs_np = np.vstack(vectors).astype(np.float32)
            # normalize for cosine similarity
            norms = np.linalg.norm(vecs_np, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            vecs_np = vecs_np / norms

            dim = vecs_np.shape[1]
            index = faiss.IndexFlatIP(dim)
            index.add(vecs_np)
            # write index to disk
            faiss.write_index(index, faiss_path)

            # save metadata
            with open(meta_path, "w", encoding="utf-8") as mf:
                for m in metadata:
                    mf.write(json.dumps(m, ensure_ascii=False) + "\n")

            my_bar.progress(100, text="FAISS index built")
            st.success(f"Uploaded and indexed the file {filename}")
        except Exception as e:
            st.error(f"Failed building FAISS index: {e}")
            my_bar.empty()
            raise
    except Exception as e:
        st.error(f"Failed to process upload: {e}")
    finally:
        time.sleep(0.2)
        my_bar.empty()