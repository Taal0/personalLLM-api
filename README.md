# Personal LLM API

Mac'te çalışan FastAPI sunucusu. PC'deki Ollama'ya (Qwen3 8B) HTTP ile bağlanır; ileride RAG ve kişilik katmanı buraya eklenecek.

## Kurulum

```bash
cd personalLLM-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env içinde OLLAMA_HOST'u PC IP'sine ayarla
```

## Çalıştırma

```bash
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Sağlık kontrolü: `curl http://localhost:8000/health`

Sohbet testi:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Merhaba, kısaca kendini tanıt"}'
```

## Ortam değişkenleri

| Değişken | Varsayılan | Açıklama |
|----------|------------|----------|
| `OLLAMA_HOST` | `http://localhost:11434` | PC Ollama adresi |
| `OLLAMA_MODEL` | `qwen3:8b-q4_K_M` | Kullanılacak model |
| `PERSONA_PATH` | `./persona.txt` | System prompt dosyası |
| `API_HOST` | `0.0.0.0` | API bind adresi |
| `API_PORT` | `8000` | API portu |

## Yol haritası (Faz 1)

- [x] Aşama 2a-1: Python projesi (venv, requirements)
- [x] Aşama 2a-2: `/chat` endpoint → Ollama forward
- [x] Aşama 2a-3: System prompt (`persona.txt`)
- [ ] Aşama 2a-4: Kişilik anketi → system prompt
- [ ] Aşama 2b: RAG (ChromaDB + Obsidian vault)
