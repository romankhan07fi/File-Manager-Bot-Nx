# ============================================================
# COUNTRY NUMBER SPLITTER BOT — SINGLE FILE
# ============================================================
# Required packages:
#   python-telegram-bot
#   pandas
#   openpyxl
#   xlrd
#   phonenumbers
#   pycountry
#
# Install once:
#   pip install python-telegram-bot pandas openpyxl xlrd phonenumbers pycountry
#
# Then put your Telegram Bot Token in BOT_TOKEN below.
# ============================================================

import os
import re
import asyncio
import tempfile
import zipfile
from collections import defaultdict

import pandas as pd
import phonenumbers
from phonenumbers import geocoder
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ============================================================
# CONFIG
# ============================================================
BOT_TOKEN = "8888974597:AAFiSW_Ht7XEYhoaCNdZ70PYalgtI30c68I"

MAX_NUMBERS_PER_FILE = 0  # 0 = no split. Example: 1000 to split large country files.

# Output customization
OUTPUT_EXTENSION = ".txt"
INCLUDE_HEADER = False
HEADER_TEMPLATE = "Country: {flag} {country} ({code})\nTotal Numbers: {count}\n\n"
DEDUPLICATE_NUMBERS = True

# ============================================================
# COUNTRY HELPERS
# ============================================================
def country_name(region_code: str) -> str:
    """Return the full country/region name automatically."""
    if not region_code or region_code == "ZZ":
        return "Unknown"

    # phonenumbers supplies country/region display names for supported regions.
    try:
        from phonenumbers import geocoder
        name = geocoder.country_name_for_number(
            phonenumbers.parse("+999999999999", None), "en"
        )
    except Exception:
        name = ""

    # A reliable complete mapping from the library's region metadata.
    try:
        item = pycountry.countries.get(alpha_2=region_code)
        if item:
            return item.name
    except Exception:
        pass

    # Fallback to the region code if a special territory is not in pycountry.
    return region_code

def country_flag(region_code: str) -> str:
    if not region_code or len(region_code) != 2:
        return "🌐"
    return "".join(chr(127397 + ord(c)) for c in region_code.upper())

def clean_phone(value) -> str | None:
    if value is None:
        return None

    # Excel may turn a numeric phone into 880171234567.0
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return None

    text = re.sub(r"\.0$", "", text)
    text = text.replace("\u00a0", " ")

    # Keep + and digits; this also handles spaces, -, (, ), etc.
    if text.startswith("+"):
        cleaned = re.sub(r"\D", "", text[1:])
    else:
        cleaned = re.sub(r"\D", "", text)

    if len(cleaned.lstrip("+")) < 7:
        return None

    return cleaned

def detect_country(number: str):
    """
    Parse an international number.
    If the input has no + prefix, we cannot reliably know the country,
    so it is placed in Unknown instead of guessing.
    """
    try:
        if not number.startswith("+"):
            return None, None

        parsed = phonenumbers.parse(number, None)
        if not phonenumbers.is_possible_number(parsed):
            return None, None

        region = phonenumbers.region_code_for_number(parsed)
        if not region:
            return None, None

        return region, country_name(region)
    except Exception:
        return None, None

# ============================================================
# FILE EXTRACTION
# ============================================================
def extract_from_txt(path: str):
    text = Path(path).read_text(encoding="utf-8", errors="ignore")
    # First prefer +international numbers; fallback to long digit strings.
    matches = re.findall(r"\+\d[\d\s().-]{6,}\d", text)
    numbers = [clean_phone(x) for x in matches]

    if not numbers:
        matches = re.findall(r"(?<!\d)\d{7,15}(?!\d)", text)
        numbers = [clean_phone(x) for x in matches]

    return [n for n in numbers if n]

def extract_from_csv(path: str):
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    numbers = []
    for col in df.columns:
        for value in df[col].tolist():
            n = clean_phone(value)
            if n:
                numbers.append(n)
    return numbers

def extract_from_excel(path: str):
    engine = "xlrd" if path.lower().endswith(".xls") else "openpyxl"
    sheets = pd.read_excel(path, sheet_name=None, dtype=str, engine=engine)
    numbers = []

    for _, df in sheets.items():
        for col in df.columns:
            for value in df[col].tolist():
                n = clean_phone(value)
                if n:
                    numbers.append(n)

    return numbers


def extract_from_zip(path: str, workdir: str):
    numbers = []
    extract_dir = os.path.join(workdir, "zip_input")
    os.makedirs(extract_dir, exist_ok=True)

    with zipfile.ZipFile(path, "r") as z:
        z.extractall(extract_dir)

    for root, _, files in os.walk(extract_dir):
        for filename in files:
            full = os.path.join(root, filename)
            ext = Path(filename).suffix.lower()
            try:
                if ext == ".txt":
                    numbers.extend(extract_from_txt(full))
                elif ext == ".csv":
                    numbers.extend(extract_from_csv(full))
                elif ext in {".xlsx", ".xls"}:
                    numbers.extend(extract_from_excel(full))
            except Exception:
                # One bad file inside a ZIP should not stop the whole batch.
                continue

    return numbers

def extract_numbers(path: str, workdir: str | None = None):
    ext = Path(path).suffix.lower()

    if ext == ".txt":
        return extract_from_txt(path)
    if ext == ".csv":
        return extract_from_csv(path)
    if ext in {".xlsx", ".xls"}:
        return extract_from_excel(path)
    if ext == ".zip":
        if not workdir:
            raise ValueError("ZIP processing requires a working directory.")
        return extract_from_zip(path, workdir)

    raise ValueError("Unsupported file format. Use TXT, CSV, XLSX, XLS or ZIP.")

# ============================================================
# OUTPUT
# ============================================================
def split_list(items, size):
    if not size or size <= 0:
        return [items]
    return [items[i:i + size] for i in range(0, len(items), size)]

def build_country_files(numbers_by_country, workdir):
    files = []

    for region in sorted(numbers_by_country):
        numbers = numbers_by_country[region]
        name = country_name(region)
        safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_") or "Unknown"

        chunks = split_list(numbers, MAX_NUMBERS_PER_FILE)

        for idx, chunk in enumerate(chunks, start=1):
            if len(chunks) == 1:
                filename = f"{safe_name}.txt"
            else:
                filename = f"{safe_name}_{idx}.txt"

            path = os.path.join(workdir, filename)
            # Output numbers without the leading + sign.
            chunk = [n.lstrip("+") for n in chunk]

            with open(path, "w", encoding="utf-8") as f:
                if INCLUDE_HEADER:
                    display_flag = "🌐" if region == "ZZ" else country_flag(region)
                    display_country = "Unknown" if region == "ZZ" else name
                    f.write(
                        HEADER_TEMPLATE.format(
                            flag=display_flag,
                            country=display_country,
                            code=region,
                            count=len(chunk),
                        )
                    )
                f.write("\n".join(chunk))
                f.write("\n")

            files.append((path, region, name, len(chunk)))

    return files

# ============================================================
# TELEGRAM HANDLERS
# ============================================================\n\ndef get_display_name(update):\n    user = update.effective_user\n    first_name = (user.first_name or "").strip()\n    last_name = (user.last_name or "").strip()\n    return " ".join(part for part in (first_name, last_name) if part) or "User"\n
WELCOME = (
    "👋 <b>Welcome, {display_name}!</b>\n\n"
    "I can extract phone numbers from your files, detect their country, "
    "and separate them into individual TXT files.\n\n"
    "📁 <b>Supported formats:</b>\n"
    "📄 TXT\n"
    "📊 CSV\n"
    "📗 XLSX / XLS\n\n"
    "Just send me a file and I'll process it automatically. ⚡"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    first_name = update.effective_user.first_name or "User"
    await update.message.reply_text(
        WELCOME.format(display_name=get_display_name(update)),
        parse_mode=ParseMode.HTML
    )

async def process_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    filename = document.file_name or "uploaded_file"

    allowed = {".txt", ".csv", ".xlsx", ".xls", ".zip"}
    ext = Path(filename).suffix.lower()

    if ext not in allowed:
        await update.message.reply_text(
            "❌ Unsupported file format.\n\n"
            "Please send TXT, CSV, XLSX, XLS or ZIP."
        )
        return

    status = await update.message.reply_text("🔄 Processing your file, please wait...")

    with tempfile.TemporaryDirectory() as workdir:
        input_path = os.path.join(workdir, filename)

        try:
            tg_file = await document.get_file()
            await tg_file.download_to_drive(input_path)

            numbers = await asyncio.to_thread(extract_numbers, input_path, workdir)

            if not numbers:
                await status.edit_text(
                    "❌ No phone numbers were found in this file."
                )
                return

            # Classify by country.
            by_country = defaultdict(list)
            unknown = []

            for number in numbers:
                region, _ = detect_country(number)
                if region:
                    by_country[region].append(number)
                else:
                    unknown.append(number)

            # Keep original order and remove exact duplicates within each country.
            if DEDUPLICATE_NUMBERS:
                for region in list(by_country):
                    seen = set()
                    unique = []
                    for n in by_country[region]:
                        if n not in seen:
                            seen.add(n)
                            unique.append(n)
                    by_country[region] = unique

            if unknown:
                by_country["ZZ"] = []
                seen = set()
                for n in unknown:
                    if n not in seen:
                        seen.add(n)
                        by_country["ZZ"].append(n)

            total = sum(len(v) for v in by_country.values())

            await status.edit_text(
                f"⏳ <b>Processing complete.</b>\n"
                f"📞 Numbers found: <b>{total}</b>\n"
                f"🌍 Countries: <b>{len(by_country)}</b>\n\n"
                f"📤 Sending country files...",
                parse_mode=ParseMode.HTML,
            )

            output_files = build_country_files(by_country, workdir)

            for path, region, name, count in output_files:
                if region == "ZZ":
                    flag = "🌐"
                    display_name = "Unknown"
                else:
                    flag = country_flag(region)
                    display_name = name

                caption = (
                    f"🌍 Country: {flag} {display_name}\n"
                    f"📞 Total Number: {count}"
                )

                with open(path, "rb") as f:
                    await update.message.reply_document(
                        document=f,
                        filename=os.path.basename(path),
                        caption=caption,
                    )

            summary_lines = [
                "✅ <b>Done!</b>",
                "",
                f"📞 Total numbers: <b>{total}</b>",
                f"🌍 Total countries: <b>{len(by_country)}</b>",
                "",
            ]

            for region in sorted(by_country):
                name = "Unknown" if region == "ZZ" else country_name(region)
                flag = "🌐" if region == "ZZ" else country_flag(region)
                summary_lines.append(
                    f"{flag} {name}: <b>{len(by_country[region])}</b>"
                )

            await status.edit_text(
                "\n".join(summary_lines),
                parse_mode=ParseMode.HTML,
            )

        except Exception as e:
            await status.edit_text(
                "❌ <b>Something went wrong.</b>\n\n"
                f"<code>{str(e)[:1000]}</code>",
                parse_mode=ParseMode.HTML,
            )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 <b>How to use</b>\n\n"
        "1. Send /start\n"
        "2. Upload TXT, CSV, XLSX or XLS\n"
        "3. The bot detects countries automatically\n"
        "4. You receive one TXT file per country\n\n"
        "Example:\n"
        "🇧🇩 Bangladesh.txt\n"
        "🇿🇼 Zimbabwe.txt\n"
        "🇮🇱 Israel.txt",
        parse_mode=ParseMode.HTML,
    )

def main():
    if BOT_TOKEN == "PUT_YOUR_BOT_TOKEN_HERE":
        raise RuntimeError(
            "Set BOT_TOKEN in the environment or replace PUT_YOUR_BOT_TOKEN_HERE."
        )

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(
        MessageHandler(filters.Document.ALL, process_document)
    )

    print("Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
