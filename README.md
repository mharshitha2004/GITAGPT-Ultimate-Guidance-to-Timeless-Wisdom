# 🕉️ GitaGPT: Your Ultimate Guide to Timeless Wisdom

An AI chatbot that answers questions about the **Bhagavad Gita**. It runs on **Microsoft Phi-4**, fine-tuned with LoRA on 1,244 Gita question-and-answer pairs, and includes a **Sanskrit Phrases** assistant that explains and translates Sanskrit terms and slokas.

[![Published in IJRAR](https://img.shields.io/badge/Published-IJRAR%20Vol.12%20Issue%202-orange)](http://www.ijrar.org/viewfull.php?&p_id=IJRAR25B2301)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Flask](https://img.shields.io/badge/Backend-Flask-black)
![Model](https://img.shields.io/badge/LLM-Phi--4%20%2B%20LoRA-purple)
![Unsloth](https://img.shields.io/badge/Fine--tuning-Unsloth-green)
![RunPod](https://img.shields.io/badge/Inference-RunPod%20Serverless-673ab7)

> 📄 **Research paper:** *GitaGPT – Ultimate Guide To Timeless Wisdom*, International Journal of Research and Analytical Reviews (IJRAR), Vol. 12, Issue 2, May 2025, pp. 971–976. Paper ID **IJRAR25B2301**. [Read the paper](http://www.ijrar.org/viewfull.php?&p_id=IJRAR25B2301)

---

## 📌 Overview

General-purpose chatbots often give vague or wrong answers about scripture, and they mix in content from unrelated sources. GitaGPT stays inside one domain. The model is fine-tuned **only** on Bhagavad Gita content, and the app's system prompts make it turn down questions that have nothing to do with the Gita. The result is a focused, conversational guide to the Gita's teachings.

After logging in, users choose between two assistants on the dashboard:

| Assistant | What it does |
|---|---|
| **Gita GPT** | Answers questions about verses, chapters, characters, and teachings (karma, dharma, devotion, the Self) |
| **Sanskrit Phrases** | Explains and translates Sanskrit words, phrases, and slokas |

## 🎥 Demo

<!-- Option 1 (an inline player): edit this README on GitHub and drag the .mp4 here.
     GitHub uploads it and replaces this comment with a playable video link.
     Option 2 (a file in the repo): commit the video to demo/ and keep the link below. -->

▶️ [Watch the demo video](demo/GITAGPT-Execution_Demo.mp4)

## ✨ Features

- 💬 **Gita-focused chatbot**: verse explanations ("Explain verse 2.47"), thematic questions ("What does Krishna say about karma?"), chapter summaries
- 📖 **Sanskrit Phrases assistant**: meanings, translations, and context for Sanskrit terms
- 🚫 **Domain restriction**: separate system prompts keep each assistant on topic. Off-topic questions ("Who won the cricket match?") get a polite message explaining the bot's scope. In testing, more than **95%** of unrelated queries were turned down.
- 🧠 **Conversational memory**: the last 10 messages of a chat are sent with each request, so follow-up questions keep their context
- 🔐 **User accounts**: registration and login with hashed passwords (Werkzeug), plus session handling
- 🗂️ **Chat management**: create, rename, delete, and resume chats. A new chat's title is set automatically from its first question.
- 🛟 **Graceful fallbacks**: if RunPod credentials are missing, a mock client lets you run the app without a GPU. If the model fails, the user sees a friendly error message instead of a crash.
- 🎨 **Themed UI**: saffron theme for Gita GPT and green theme for Sanskrit Phrases, built with Bootstrap 5

## 🏗️ Architecture

```
 Bhagavad Gita text
        │  extract Q&A pairs
        ▼
 data/dataset gita.json  (ShareGPT format, 1,244 conversations)
        │  notebooks/PushtoHub.ipynb
        ▼
 Hugging Face Datasets ── harshitha672/dataset_Gita
        │  notebooks/GITAGPT.ipynb  (Unsloth + LoRA, Google Colab T4)
        ▼
 Hugging Face Hub ── harshitha672/Phi_4_model_Finetuned_GitaGPT  (merged 16-bit)
        │
        ▼
 RunPod Serverless vLLM endpoint  (NVIDIA A100 80 GB, OpenAI-compatible API)
        ▲
        │  openai client + RUNPOD_API_KEY / RUNPOD_ENDPOINT_ID
 app.py (Flask) ──► SQLite via SQLAlchemy  (users, chats, messages)
        ▲
        │  HTTP + session cookie
 templates/  (Jinja2 + Bootstrap 5 + JavaScript)
   index → register / login → dashboard → chat (gita | sanskrit)
```

**Request flow:** the user sends a message → `/send_message` checks the session and that the chat belongs to the user → it builds the prompt from the system prompt for that chat type plus the last 10 messages → it calls the RunPod endpoint → it saves both messages to SQLite → it returns the answer as JSON to the chat page.

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Base model | Microsoft **Phi-4** (`unsloth/Phi-4`, 14B) |
| Fine-tuning | **Unsloth**, LoRA / PEFT, TRL `SFTTrainer`, 4-bit loading, merged 16-bit export |
| Dataset & model hosting | **Hugging Face** Datasets and Hub |
| Inference | **RunPod** Serverless (vLLM on A100 80 GB), OpenAI-compatible API |
| Backend | **Flask**, Flask-SQLAlchemy, Werkzeug, python-dotenv, `openai` |
| Database | **SQLite** (`instance/chatapp.db`, created automatically) |
| Frontend | HTML, CSS, **Bootstrap 5**, JavaScript, Jinja2, Font Awesome |

## 📚 Dataset

[`data/dataset gita.json`](data/dataset%20gita.json) contains **1,244** question-and-answer conversations about the Bhagavad Gita, in **ShareGPT** format. They cover characters, events, verses, and philosophical teachings. The dataset is also published on Hugging Face as [`harshitha672/dataset_Gita`](https://huggingface.co/datasets/harshitha672/dataset_Gita).

```json
{
  "conversations": [
    [
      { "from": "human", "value": "Who were Dhritarashtra and Pandu?" },
      { "from": "gpt",   "value": "Dhritarashtra and Pandu were brothers." }
    ],
    [
      { "from": "human", "value": "Whom did Dhritarashtra and Pandu marry?" },
      { "from": "gpt",   "value": "Dhritarashtra married Gandhari, while Pandu was married to Kunti and Madri." }
    ]
  ]
}
```

## 🧠 Model Fine-Tuning

[`notebooks/GITAGPT.ipynb`](notebooks/GITAGPT.ipynb) fine-tunes Phi-4 with Unsloth on a free Google Colab **Tesla T4** GPU (peak memory about 14.7 GB).

| Setting | Value |
|---|---|
| Base model | `unsloth/Phi-4`, loaded in 4-bit |
| Max sequence length | 2048 |
| LoRA rank / alpha / dropout | 16 / 16 / 0 |
| Target modules | `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj` |
| Trainable parameters | **65.5M** (LoRA adapters only, under 0.5% of the 14B base model) |
| Chat template | `phi-4` (ShareGPT standardized) |
| Effective batch size | 8 (2 per device × 4 gradient accumulation steps) |
| Learning rate / scheduler | 2e-4 / linear, 5 warmup steps |
| Optimizer | `adamw_8bit`, weight decay 0.01 |
| Training | 250 steps (about 2 epochs) |
| Loss masking | `train_on_responses_only` (loss is computed on assistant replies only) |
| Training loss | **2.95 → 0.98** |
| Export | merged 16-bit weights pushed to the Hugging Face Hub |

The fine-tuned model is on the Hub as [`harshitha672/Phi_4_model_Finetuned_GitaGPT`](https://huggingface.co/harshitha672/Phi_4_model_Finetuned_GitaGPT).

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- *(Optional)* A [RunPod](https://www.runpod.io/) serverless endpoint serving the fine-tuned model. Without one, the app runs with a mock AI client.

### 1. Clone and install
```bash
git clone https://github.com/mharshitha2004/GitaGPT.git
cd GitaGPT
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables
```bash
cp .env.example .env            # Windows: copy .env.example .env
```
Then fill in `.env`:
```env
SECRET_KEY=any-long-random-string
RUNPOD_API_KEY=your-runpod-api-key
RUNPOD_ENDPOINT_ID=your-endpoint-id
```

### 3. Run
```bash
python app.py
```
Open http://127.0.0.1:5000, register an account, and pick an assistant from the dashboard. The SQLite database is created automatically the first time the app runs.

### Reproducing the model (optional)
1. Open [`notebooks/PushtoHub.ipynb`](notebooks/PushtoHub.ipynb) in Colab to upload the dataset to Hugging Face.
2. Open [`notebooks/GITAGPT.ipynb`](notebooks/GITAGPT.ipynb) in Colab (T4 GPU) to fine-tune Phi-4 and push the merged model.
   Both notebooks read your Hugging Face token from the `HF_TOKEN` environment variable.
3. In RunPod, go to **Serverless** → **New Endpoint** → **vLLM**, enter the Hugging Face model ID, choose an A100 80 GB GPU, and deploy. Copy the endpoint ID and your API key into `.env`.

## 📁 Project Structure

```
GitaGPT/
├── app.py                   # Flask app: models, routes, RunPod client, system prompts
├── requirements.txt
├── .env.example             # Template for environment variables
├── data/
│   └── dataset gita.json    # ShareGPT-format training data (1,244 conversations)
├── notebooks/
│   ├── PushtoHub.ipynb      # Uploads the dataset to Hugging Face
│   └── GITAGPT.ipynb        # Unsloth LoRA fine-tuning of Phi-4
├── templates/
│   ├── index.html           # Landing page
│   ├── register.html
│   ├── login.html
│   ├── dashboard.html       # Choose Gita GPT or Sanskrit Phrases
│   ├── chat.html            # Chat UI with sidebar history (shared by both assistants)
│   └── error.html           # 404 / 500 page
└── demo/
    └── GITAGPT-Execution_Demo.mp4
```

### API Routes

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Landing page (redirects to the dashboard if logged in) |
| `/register`, `/login` | GET, POST | Account creation and sign-in |
| `/logout` | GET | Ends the session |
| `/dashboard` | GET | Choose an assistant |
| `/chat/<chat_type>` | GET | Chat page for `gita` or `sanskrit` |
| `/create_chat` | POST | Start a new chat |
| `/send_message` | POST | Send a message and get the model's reply |
| `/rename_chat/<id>` | POST | Rename a chat |
| `/delete_chat/<id>` | POST | Delete a chat and its messages |

## 📊 Results

- **Response time:** 4–8 s for typical questions and 10–15 s for long verse explanations (A100 80 GB)
- **Domain filtering:** more than 95% of off-topic queries were correctly turned down
- **Accuracy:** answers to verse and theme questions matched the scripture closely. Early problems with verse references were fixed by further fine-tuning.
- **Stability:** no crashes or slowdowns during stress tests with many users sending queries in quick succession

## ⚠️ Limitations

- Very detailed or obscure verse questions can produce weaker answers because the dataset is small
- A few off-topic queries can still get through the filter
- Needs internet access to reach the hosted model
- No voice input or output yet

## 🔮 Future Enhancements

- Exact verse lookup by reference (e.g. `BG 2.47`)
- Voice questions and audio answers
- Android and iOS apps
- Hindi, Sanskrit, Tamil, and other regional languages
- Admin dashboard for usage and monitoring
- Answer ratings from users to guide further training
- Lightweight on-device model for offline use

## 👥 Team

Major Project, B.Tech CSE, **Geethanjali College of Engineering and Technology** (2024–2025)

- **Mandadi Harshitha Reddy**
- Banala Prabhakar
- Nadimpally Vaishnavi Devi

**Guide:** P. Krishna Rao, Assistant Professor, Dept. of CSE

## 📖 Citation

```bibtex
@article{rao2025gitagpt,
  title   = {GitaGPT -- Ultimate Guide To Timeless Wisdom},
  author  = {Rao, P. Krishna and Reddy, Mandadi Harshitha and Devi, Nadimpally Vaishnavi and Prabhakar, Banala},
  journal = {International Journal of Research and Analytical Reviews (IJRAR)},
  volume  = {12},
  number  = {2},
  pages   = {971--976},
  year    = {2025},
  issn    = {2348-1269},
  url     = {http://www.ijrar.org/viewfull.php?&p_id=IJRAR25B2301}
}
```

## 🙏 Acknowledgements

- [Unsloth](https://github.com/unslothai/unsloth) for efficient fine-tuning
- [Hugging Face](https://huggingface.co/) and [RunPod](https://www.runpod.io/) for hosting and inference
