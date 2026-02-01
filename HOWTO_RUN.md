# 📖 Руководство по запуску / HOWTO RUN

**Designed and produced by NiHao OFM** | [Telegram](https://t.me/NiHaoOFM)

---

## 🇷🇺 Русский

### Предварительные требования

| Компонент | Описание | Установка |
|-----------|----------|-----------|
| **Python 3.8+** | С доступным `pip` | `apt install python3 python3-pip` |
| **Git** | Система контроля версий | `apt install git` |
| **Git LFS** | Для больших файлов | `apt install git-lfs && git lfs install` |
| **huggingface_hub** | Python библиотека | `pip install huggingface_hub` |
| **HF Token** | С правами write | [Получить токен](https://huggingface.co/settings/tokens) |

### Установка

#### Вариант 1: Быстрая установка (wget)

```bash
# Перейдите в рабочую директорию
cd /workspace

# Скачайте файлы
wget https://raw.githubusercontent.com/mikolakiyv/LoRA-Wizard-NiHao/main/run.sh
wget https://raw.githubusercontent.com/mikolakiyv/LoRA-Wizard-NiHao/main/lora_wizard.py

# Исправьте окончания строк (важно!)
sed -i 's/\r$//' run.sh lora_wizard.py

# Сделайте исполняемыми
chmod +x run.sh lora_wizard.py
```

#### Вариант 2: Клонирование репозитория

```bash
git clone https://github.com/mikolakiyv/LoRA-Wizard-NiHao.git
cd LoRA-Wizard-NiHao
sed -i 's/\r$//' run.sh lora_wizard.py
chmod +x run.sh lora_wizard.py
```

### Запуск

```bash
# Основной способ (рекомендуется)
bash run.sh

# Или напрямую через Python
python3 lora_wizard.py

# С отключённым quiet mode (для отладки)
QUIET_BOOT=0 bash run.sh
```

### Настройка токена HuggingFace

#### Способ 1: Переменная окружения (рекомендуется для серверов)

```bash
# Добавьте в ~/.bashrc или ~/.profile
export HF_TOKEN="hf_xxxxxxxxxxxxxxxxxxxxxxxx"

# Или временно для текущей сессии
HF_TOKEN="hf_xxx" bash run.sh
```

#### Способ 2: Через huggingface-cli

```bash
pip install huggingface_hub
huggingface-cli login
# Введите токен когда попросит
```

#### Способ 3: Ввод при запуске

Просто запустите скрипт — он попросит ввести токен, если не найдёт его.

### Структура папок для Upload

Скрипт ищет папки с такой структурой:

```
/workspace/
├── output_folder/           # ← скрипт ищет здесь
│   └── my_training/
│       ├── epoch1/
│       │   └── adapter_model.safetensors
│       ├── epoch2/
│       │   └── adapter_model.safetensors
│       ├── ...
│       ├── epoch50/
│       │   └── adapter_model.safetensors
│       └── final.safetensors  # опционально
├── config.toml              # ← скрипт соберёт данные отсюда
└── training.toml
```

### Куда сохраняются скачанные файлы

При Download скрипт автоматически:
1. Ищет папку с именем `loras` в `/workspace`
2. Если не находит — создаёт `/workspace/loras`
3. Если `/workspace` недоступен — создаёт `./loras`

### Логи

При возникновении ошибок проверьте логи:

```bash
ls -la nihao_wizard_logs/
cat nihao_wizard_logs/2024-01-15_1430.log
```

---

## 🇬🇧 English

### Prerequisites

| Component | Description | Installation |
|-----------|-------------|--------------|
| **Python 3.8+** | With `pip` available | `apt install python3 python3-pip` |
| **Git** | Version control | `apt install git` |
| **Git LFS** | For large files | `apt install git-lfs && git lfs install` |
| **huggingface_hub** | Python library | `pip install huggingface_hub` |
| **HF Token** | With write access | [Get token](https://huggingface.co/settings/tokens) |

### Installation

#### Option 1: Quick install (wget)

```bash
# Go to your working directory
cd /workspace

# Download files
wget https://raw.githubusercontent.com/mikolakiyv/LoRA-Wizard-NiHao/main/run.sh
wget https://raw.githubusercontent.com/mikolakiyv/LoRA-Wizard-NiHao/main/lora_wizard.py

# Fix line endings (important!)
sed -i 's/\r$//' run.sh lora_wizard.py

# Make executable
chmod +x run.sh lora_wizard.py
```

#### Option 2: Clone repository

```bash
git clone https://github.com/mikolakiyv/LoRA-Wizard-NiHao.git
cd LoRA-Wizard-NiHao
sed -i 's/\r$//' run.sh lora_wizard.py
chmod +x run.sh lora_wizard.py
```

### Running

```bash
# Main method (recommended)
bash run.sh

# Or directly with Python
python3 lora_wizard.py

# With quiet mode disabled (for debugging)
QUIET_BOOT=0 bash run.sh
```

### Setting up HuggingFace Token

#### Method 1: Environment variable (recommended for servers)

```bash
# Add to ~/.bashrc or ~/.profile
export HF_TOKEN="hf_xxxxxxxxxxxxxxxxxxxxxxxx"

# Or temporarily for current session
HF_TOKEN="hf_xxx" bash run.sh
```

#### Method 2: Via huggingface-cli

```bash
pip install huggingface_hub
huggingface-cli login
# Enter token when prompted
```

#### Method 3: Enter at runtime

Just run the script — it will ask for token if not found.

### Folder Structure for Upload

The script looks for folders with this structure:

```
/workspace/
├── output_folder/           # ← script searches here
│   └── my_training/
│       ├── epoch1/
│       │   └── adapter_model.safetensors
│       ├── epoch2/
│       │   └── adapter_model.safetensors
│       ├── ...
│       ├── epoch50/
│       │   └── adapter_model.safetensors
│       └── final.safetensors  # optional
├── config.toml              # ← script will collect data from here
└── training.toml
```

### Where Downloaded Files are Saved

During Download, the script automatically:
1. Searches for a folder named `loras` in `/workspace`
2. If not found — creates `/workspace/loras`
3. If `/workspace` is unavailable — creates `./loras`

### Logs

If errors occur, check logs:

```bash
ls -la nihao_wizard_logs/
cat nihao_wizard_logs/2024-01-15_1430.log
```

---

## 🐛 Troubleshooting / Решение проблем

### "Token not found" / "Токен не найден"

```bash
# Set token via environment variable
export HF_TOKEN="hf_xxxxxxxxxxxxxxxxxxxxxxxx"

# Or login via CLI
huggingface-cli login
```

### "git-lfs not found"

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install git-lfs
git lfs install

# macOS
brew install git-lfs
git lfs install

# Other: https://git-lfs.com
```

### "Permission denied"

```bash
chmod +x run.sh lora_wizard.py
```

### CRLF issues (downloaded on Windows)

```bash
sed -i 's/\r$//' run.sh lora_wizard.py *.toml
```

### "Repository not found" during clone

1. Check that the repository was actually created on HuggingFace
2. Verify your token has write permissions
3. Check the repository name is correct (case-sensitive)

### "No epoch folders found"

Make sure your training output has the expected structure:
```
run_dir/
├── epoch1/
│   └── *.safetensors
├── epoch2/
│   └── *.safetensors
└── ...
```

### Script hangs / doesn't respond

Try running with debug output:
```bash
QUIET_BOOT=0 python3 lora_wizard.py
```

---

## 📞 Support / Поддержка

- **Telegram**: [@NiHaoOFM](https://t.me/NiHaoOFM)
- **GitHub Issues**: [Report a bug](https://github.com/mikolakiyv/LoRA-Wizard-NiHao/issues)

---

**Made with ❤️ by NiHao OFM**
