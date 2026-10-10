# Distributed Hilbert's Hotel (Consistent Hashing)

โครงงานวิชา Object Oriented Data Structure (OODS) ภาคการศึกษา 1/2569  
การจำลองโรงแรมอนันต์ของฮิลเบิร์ตแบบกระจายศูนย์ (Distributed Hilbert's Hotel) ด้วยเทคนิค Consistent Hashing บนภาษา Python

---

## 📌 โครงสร้าง Branch ประจำแต่ละ Task

โปรเจกต์นี้แบ่งงานแบบ **1 คนต่อ 1 Task** โดยมี Branch แยกอิสระสำหรับแต่ละคน ดังนี้:

| Task | Branch Name | โมดูลที่รับผิดชอบ | ผู้รับผิดชอบ |
| :---: | :--- | :--- | :--- |
| **Task 1** | `task-1/core-ring` | `src/hash_ring.py`, `src/mod_n_system.py` | คนที่ 1 |
| **Task 2** | `task-2/guest-index` | `src/guest.py`, `src/indexing.py` | คนที่ 2 |
| **Task 3** | `task-3/migration-engine` | `src/hotel_node.py`, `src/hotel_system.py` | คนที่ 3 |
| **Task 4** | `task-4/experiments-cli` | `src/experiments.py`, `src/export.py`, `src/cli.py` | คนที่ 4 |

> ⚠️ **กฎสำคัญ:** ห้าม push โค้ดลง branch `main` โดยตรงเด็ดขาด! ระบบจะปฏิเสธการ push ทันที ทุกคนต้องพัฒนาโค้ดบน branch ของตนเอง แล้วส่งเข้ามาทาง **Pull Request (PR)** เท่านั้น

---

## ⚙️ การตั้งค่าสภาพแวดล้อมด้วย `uv` (Recommended)

โปรเจกต์นี้แนะนำให้จัดการสภาพแวดล้อมด้วย [**`uv`**](https://docs.astral.sh/uv/) ซึ่งเป็น Python package & project manager ที่ทำงานเร็วมาก และสามารถดึง Python เวอร์ชันตรงตาม [`.python-version`](.python-version) ให้อัตโนมัติ:

### ขั้นที่ 1: ติดตั้ง `uv` (หากยังไม่มีในเครื่อง)
```bash
# สำหรับ Windows (PowerShell):
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# สำหรับ macOS / Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### ขั้นที่ 2: สร้าง Environment และติดตั้ง Dependencies
```bash
# 1. สร้าง Virtual Environment (uv จะอ่าน .python-version ให้อัตโนมัติ)
uv venv

# 2. ติดตั้งแพ็กเกจให้ตรงกันทุกคน
uv pip install -r requirements.txt
```

> 🚀 **ความสะดวกของ `uv`:** ไม่จำเป็นต้องสั่ง activate environment ก็ได้! สามารถสั่ง `uv run` นำหน้าคำสั่งใดๆ ได้ทันที เช่น `uv run pytest`
> 
> 💡 **สำหรับผู้ใช้ VS Code:** เมื่อสั่ง `uv venv` แล้วเปิด VS Code ตัวโปรแกรมจะตรวจพบ `.venv` และตั้งค่า Pytest Test Explorer ให้อัตโนมัติจาก `.vscode/settings.json`

<details>
<summary>👉 คลิกที่นี่หากต้องการใช้วิธี python venv ปกติ (แบบดั้งเดิม)</summary>

```bash
# 1. สร้าง virtual environment
python -m venv .venv

# 2. เปิดใช้งาน (Activate)
# Windows (PowerShell): .venv\Scripts\Activate.ps1
# macOS / Linux: source .venv/bin/activate

# 3. ติดตั้งแพ็กเกจ
pip install -r requirements.txt
```
</details>

---

## 🧪 1. กลไกการทดสอบโค้ดในเครื่อง (Local Testing)

ก่อนจะส่งโค้ดขึ้น GitHub ทุกครั้ง ให้รันชุดทดสอบในเครื่องตัวเองเพื่อความมั่นใจและประหยัดเวลา:

### คำสั่งรันเทสต์เฉพาะ Task ของตนเอง:
```bash
# สำหรับคนทำ Task 1
uv run pytest tests/test_task1_ring.py -v

# สำหรับคนทำ Task 2
uv run pytest tests/test_task2_guest.py -v

# สำหรับคนทำ Task 3
uv run pytest tests/test_task3_migration.py -v

# สำหรับคนทำ Task 4
uv run pytest tests/test_task4_integration.py -v
```
*(หมายเหตุ: หากใช้ venv แบบปกติและ activate แล้ว สามารถใช้คำสั่ง `pytest tests/...` แทน `uv run pytest` ได้เช่นกัน)*

### คำสั่งรันเทสต์ทั้งหมดในโปรเจกต์:
```bash
pytest tests/ -v
```
*(ระบบถูกออกแบบให้ Skip โมดูลของเพื่อนที่ยังไม่ถูกรวมเข้ามาโดยอัตโนมัติ ทำให้เทสต์เฉพาะส่วนของคุณได้อย่างราบรื่น)*

---

## 🚀 2. ขั้นตอนการเปิด Pull Request (Create PR)

เมื่อเขียนโค้ดและรันเทสต์ในเครื่องผ่านเรียบร้อยแล้ว ให้ทำตามขั้นตอนดังนี้:

### ขั้นที่ 1: Commit และ Push ไปยัง Branch ของตนเอง
```bash
# ตัวอย่างสำหรับ Task 1
git checkout task-1/core-ring
git add .
git commit -m "feat: implement HashRing with 64-bit SHA-256 and bisect lookup"
git push origin task-1/core-ring
```

### ขั้นที่ 2: สร้าง Pull Request บน GitHub
1. เข้าไปที่หน้าคลังโค้ด: [Knarf49/Hilbert-Hotel](https://github.com/Knarf49/Hilbert-Hotel)
2. คลิกปุ่ม **"Compare & pull request"** หรือแท็บ **"Pull requests"** $\to$ **"New pull request"**
3. ตั้งค่า Base และ Compare:
   * **base:** `main`
   * **compare:** `task-X/...` (เลือก branch ของตนเอง)
4. ตั้งชื่อหัวข้อ PR และอธิบายสั้นๆ ว่าได้พัฒนาหรือแก้ไขส่วนใดบ้าง แล้วคลิก **"Create pull request"**

---

## 🤖 3. กลไกการทดสอบอัตโนมัติ (Automated CI/CD)

ทันทีที่มีการเปิด PR ระบบ **GitHub Actions** จะตื่นขึ้นมาทำงานอัตโนมัติทันที:

1. **Matrix Testing:** รันเทสต์ซ้ำบน Python เวอร์ชัน **3.11**, **3.12**, และ **3.13** บนสภาพแวดล้อม Ubuntu Clean Image
2. **การตรวจจับความผิดพลาด:**
   * ❌ **Failed:** หากมีบั๊กหรือทำผิดกฎเหล็ก (เช่น เลขห้องเปลี่ยน, แขกย้ายผิดตึก, หรือแครชจากกรณีขอบ) CI จะขึ้นกากบาทสีแดง **ปุ่ม Merge จะถูกล็อคทันที** ผู้ส่ง PR ต้องแก้โค้ดและ push ขึ้นมาใหม่
   * ✅ **Passed:** หากผ่านทุกการทดสอบ จะขึ้นเครื่องหมายถูกสีเขียว (`All checks have passed`)

---

## 🔀 4. การ Merge เข้าสู่ Branch `main`

เงื่อนไขในการ Merge เข้าสู่ `main`:
1. ✅ **CI Status Checks ต้องผ่าน 100%:** ต้องขึ้นสีเขียวครบทั้ง 3 เวอร์ชันของ Python
2. 🔒 **ผ่านเกณฑ์ Branch Protection:** หาก CI ไม่ผ่าน ปุ่ม **"Merge pull request"** จะไม่สามารถกดได้
3. เมื่อผ่านครบถ้วน ให้คลิก **"Merge pull request"** $\to$ **"Confirm merge"**

---

## 🔄 5. การดึงโค้ดล่าสุดจาก `main` กลับเข้า Branch ตัวเอง (Sync with Main)

เมื่อเพื่อนคนอื่น Merge โค้ดเข้า `main` ไปแล้ว ให้ดึงโค้ดล่าสุดมาอัปเดตที่ Branch ของตนเองก่อนทำงานต่อ:

```bash
# สลับมาที่ branch ของตัวเอง
git checkout task-X/...

# ดึงโค้ดล่าสุดจาก main มารวม
git pull origin main
```
