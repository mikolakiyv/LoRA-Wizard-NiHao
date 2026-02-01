# 🧙 HuggingFace LoRA Wizard

**Designed and produced by NiHao OFM**

[![Telegram](https://img.shields.io/badge/Telegram-NiHaoOFM-blue?logo=telegram)](https://t.me/NiHaoOFM)

CLI-утилита для **загрузки (upload)** и **скачивания (download)** LoRA-моделей в/из репозитория Hugging Face с интерактивным мастером. Поддерживает **русский** и **английский** языки.

---

## ✨ Возможности

### 📤 Upload Mode
- Автоматический поиск папок с результатами обучения (`epoch*/*.safetensors`)
- Выбор диапазона эпох для загрузки
- Создание нового репозитория или использование существующего
- **Сбор данных о тренировке** из `.toml` файлов конфигурации
- Поддержка приватных репозиториев
- Автоматическая настройка Git LFS для больших файлов

### 📥 Download Mode
- Просмотр списка ваших репозиториев на HuggingFace
- Скачивание одного файла или диапазона эпох
- Умный поиск папки `loras` для сохранения
- Фильтрация файлов по имени

### 🔧 Дополнительно
- Автоматическое исправление CRLF → LF
- Автоустановка зависимостей (в Linux с root)
- Безопасная работа с токеном (не отображается, не логируется)
- Подробные логи в `nihao_wizard_logs/`

---

## 📦 Файлы

| Файл | Описание |
|------|----------|
| `lora_wizard.py` | Основной Python-скрипт мастера |
| `run.sh` | Скрипт запуска с подготовкой окружения |
| `README.md` | Этот файл |
| `HOWTO_RUN.md` | Подробное руководство по запуску |

---

## 🚀 Быстрый старт

```bash
# 1. Скачайте файлы
wget https://raw.githubusercontent.com/mikolakiyv/LoRA-Wizard-NiHao/main/run.sh
wget https://raw.githubusercontent.com/mikolakiyv/LoRA-Wizard-NiHao/main/lora_wizard.py

# 2. Исправьте окончания строк (если скачивали на Windows)
sed -i 's/\r$//' run.sh lora_wizard.py

# 3. Запустите
bash run.sh
```

---

## 📋 Требования

- **Python 3.8+**
- **Git** и **Git LFS**
- **huggingface_hub** (`pip install huggingface_hub`)
- **Токен HuggingFace** с правами записи ([получить здесь](https://huggingface.co/settings/tokens))

---

## 🔐 Авторизация

Скрипт поддерживает несколько способов авторизации:

1. **Переменная окружения**: `HF_TOKEN` или `HUGGING_FACE_HUB_TOKEN`
2. **Кэш HuggingFace**: после `huggingface-cli login`
3. **Ручной ввод**: при первом запуске

```bash
# Вариант 1: через переменную окружения
export HF_TOKEN="hf_xxxxxxxxxxxxxxxxxxxxxxxx"
bash run.sh

# Вариант 2: предварительный логин
huggingface-cli login
bash run.sh
```

---

## 📤 Пример: Upload LoRA

```
🧙 HuggingFace LoRA Wizard by NiHao OFM (RU)

🟦 Что сделать?
  [1] Upload
  [2] Download
👉 Выбор: 1

🟦 Шаг 2/6: Репозиторий
  [1] Создать новый
  [2] Использовать существующий
👉 Выбор: 1
📦 Имя нового репозитория: MyLoRA_v1
🔒 Приватный? [Y/n]: Y

🟦 Шаг 5/6: Автопоиск run
✅ Найдены run-папки:
  [1] /workspace/output_folder/my_training   (эпох: 50)
👉 Номер run: 1

✅ Доступные эпохи: 1 .. 50
🔢 Эпоха ОТ: 10
🔢 Эпоха ДО: 30

✅ Загружено файлов: 21 (в репозиторий user/MyLoRA_v1)
✅ training_info.txt создан
```

---

## 📥 Пример: Download LoRA

```
🧙 HuggingFace LoRA Wizard by NiHao OFM (EN)

🟦 What do you want to do?
  [1] Upload
  [2] Download
👉 Select: 2

🟦 Step 2/4: Repository
  [1] user/my-loras
  [2] user/flux-lora
  [3] user/test-model
👉 Select: 2

🟦 Step 3/4: Choose files to download
  [1] Single file
  [2] Range of epoch files
👉 Select: 2

✅ Epochs available: 10 .. 80
🔢 Epoch FROM: 40
🔢 Epoch TO: 60

✅ Downloaded 21 file(s) to /workspace/loras
```

---

## 📊 Training Info

При загрузке скрипт автоматически ищет `.toml` файлы конфигурации и создаёт `training_info.txt` с параметрами:

```
==================================================
  LoRA Training Information
  Collected by NiHao OFM LoRA Wizard
==================================================

[Network Settings]
  network_dim = 32
  network_alpha = 16

[Training Settings]
  learning_rate = 0.0001
  max_train_epochs = 50
  train_batch_size = 2

[Resolution]
  resolution = 1024

[Model]
  pretrained_model_name_or_path = black-forest-labs/FLUX.1-dev

[Source]
  Parsed from: config.toml, training.toml
  Date: 2024-01-15 14:30:00
```

---

## 🛠 Troubleshooting

### Ошибка "Token not found"
```bash
# Установите токен через переменную окружения
export HF_TOKEN="hf_xxxxxxxxxxxxxxxxxxxxxxxx"
```

### Ошибка "git-lfs not found"
```bash
# Ubuntu/Debian
sudo apt install git-lfs
git lfs install

# Другие системы: https://git-lfs.com
```

### Ошибка "Permission denied"
```bash
chmod +x run.sh lora_wizard.py
```

### Проблемы с CRLF (Windows)
```bash
sed -i 's/\r$//' run.sh lora_wizard.py
```

---

## 📞 Контакты

- **Telegram**: [@NiHaoOFM](https://t.me/NiHaoOFM)
- **Issues**: [GitHub Issues](https://github.com/mikolakiyv/LoRA-Wizard-NiHao/issues)

---

## 📄 Лицензия

MIT License - свободное использование с указанием автора.

---

**Made with ❤️ by NiHao OFM**
