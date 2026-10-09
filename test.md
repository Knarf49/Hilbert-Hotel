# แผนการทดสอบระบบอัตโนมัติ (Automated CI/CD Test Specification)

**โครงงาน:** Distributed Hilbert's Hotel (Consistent Hashing)  
**วิชา:** Object Oriented Data Structure (OODS) ภาคการศึกษา 1/2569  
**วัตถุประสงค์:** กำหนดหัวข้อและกรณีทดสอบ (Test Cases) สำหรับการรันผ่าน **GitHub Actions CI/CD** ทุกครั้งที่มีการ `Push` หรือเปิด `Pull Request (PR)` เพื่อการันตีความถูกต้องของระบบและใช้เป็นหลักฐานส่งงานตามเกณฑ์การให้คะแนน

---

## 🎯 ภาพรวมโครงสร้างการทดสอบใน CI/CD

เมื่อมีการ Push โค้ดหรือเปิด Pull Request เข้าสู่ Branch `main` หรือ `task-*/**`:
1. **GitHub Actions Workflow** จะตั้งค่าสภาพแวดล้อม Python
2. รันชุดทดสอบด้วย `pytest` (หรือ `python -m unittest discover tests`)
3. ตรวจสอบกฎความปลอดภัย กฎเหล็กคณิตศาสตร์ และกรณีขอบ (Edge Cases)
4. สรุปผล Pass/Fail ชัดเจน หากมีข้อผิดพลาด PR จะถูกบล็อกไม่ให้ Merge

---

## 📋 รายละเอียดกรณีทดสอบแยกตาม Task (Test Suites)

---

### 🧪 Suite 1: Core Ring & Mod N Baseline (`tests/test_task1_ring.py`)
**เป้าหมาย:** ทดสอบความเสถียรของฟังก์ชันแฮช 64-บิต การทำงานของวงแหวน และระบบเปรียบเทียบ Hash Mod N

| รหัสทดสอบ | ชื่อกรณีทดสอบ | เงื่อนไขและสิ่งที่ต้องตรวจสอบ | เกณฑ์การผ่าน (Assertion) |
| :--- | :--- | :--- | :--- |
| **T1.1** | Deterministic SHA-256 Range | คำนวณแฮชของคีย์เดียวกัน 100 ครั้ง และตรวจสอบขนาดบิต | ค่าต้องตรงกันทุกครั้ง (ไม่สุ่มเหมือน `hash()`), อยู่ในช่วง $[0, 2^{64}-1]$ |
| **T1.2** | Salt Parameter Effect | ส่ง `salt="0"` เทียบกับ `salt="1"` สำหรับคีย์เดียวกัน | ได้ตำแหน่งบนวงแหวนต่างกันอย่างแน่นอน |
| **T1.3** | Virtual Node Placement | เพิ่มตึกด้วย $V = 32$ | ต้องมี Virtual Node ปรากฏบนวงแหวน 32 จุดในรูปแบบ `node:{id}:{j}` |
| **T1.4** | Mock Ring Logic (โจทย์ข้อ 9.1) | วงแหวนจำลองขนาด 100, $V=1$, ตึก A=20, B=50, C=80: <br>- แขก pos 10 $\to$ ตึก A (ตามเข็ม)<br>- แขก pos 20 $\to$ ตึก A (ตรงจุดพอดี)<br>- แขก pos 25 $\to$ ตึก B (ระหว่าง A กับ B)<br>- แขก pos 70 $\to$ ตึก C (ระหว่าง B กับ C)<br>- แขก pos 90 $\to$ ตึก A (วนกลับจุดเริ่มต้น Wrap-around) | ทุกจุดต้องคืนค่า Node ID ตรงตามโจทย์ระบุ 100% |
| **T1.5** | Hash Collision Tie-Breaker | จำลอง Virtual Nodes 2 จุดที่มีค่าแฮชชนกันพอดี | ต้องจัดเรียงตาม Tuple `(position, node_id, j)` ได้อย่างเสถียร ไม่แครช |
| **T1.6** | Mod N Array Preservation | ทดสอบระบบเปรียบเทียบ Naive Mod N: เพิ่มตึก (ต่อท้าย) และลบตึก (คงลำดับเดิม) | ลำดับ Array ของตึกที่เหลือต้องไม่สลับที่ และสูตร $H(k) \pmod N$ ทำงานถูกต้อง |

---

### 🧪 Suite 2: Guest Entity, Room Number & Indexing (`tests/test_task2_guest.py`)
**เป้าหมาย:** ทดสอบการแปลงเลขห้อง การรักษากฎความคงที่ (Invariants) และระบบค้นหา 2 ทาง

| รหัสทดสอบ | ชื่อกรณีทดสอบ | เงื่อนไขและสิ่งที่ต้องตรวจสอบ | เกณฑ์การผ่าน (Assertion) |
| :--- | :--- | :--- | :--- |
| **T2.1** | Cantor Pairing Standard Table | ตรวจสอบรหัสแขกตามตารางตัวอย่างของโจทย์ (หน้า 4 & 12):<br>- $(1, 1) \to 1$<br>- $(2, 1) \to 2$<br>- $(1, 2) \to 3$<br>- $(3, 1) \to 4$<br>- $(2, 2) \to 5$ | ได้เลขห้องตรงตามตารางเป๊ะทุกค่า และผลลัพธ์เป็น `int` (ห้ามมี float) |
| **T2.2** | No "Last Room + 1" Rule | เพิ่มแขกใหม่ในช่องทางเดิมและช่องทางใหม่ | แขกเดิมทุกคนต้องมี `room_no` เหมือนเดิม 100% ไม่ถูกเลื่อนเลขห้อง |
| **T2.3** | Bidirectional Index Consistency | เพิ่มแขก $K$ คน แล้วทดสอบค้นหาไขว้กัน:<br>- ค้นด้วย $(c, s) \to (\text{node\_id}, \text{room\_no})$<br>- ค้นด้วย $(\text{node\_id}, \text{room\_no}) \to (c, s)$ | ผลลัพธ์ทั้ง 2 ฝั่งต้องตรงกัน และใช้เวลาเฉลี่ย $\mathcal{O}(1)$ |
| **T2.4** | Atomic Batch Validation | เพิ่มแขกเป็นกลุ่ม เช่น 5 คน โดยให้คนที่ 3 มีรหัส $(c, s)$ ซ้ำกับที่มีอยู่แล้วในระบบ | **ต้องปฏิเสธทั้งกลุ่ม (Reject entire batch)**, แขก 4 คนที่ไม่ซ้ำต้องไม่ถูกบันทึกแอบแฝง (Zero side-effects) |
| **T2.5** | Polite Rejection on Not Found | ค้นหาแขกที่ไม่มีอยู่จริง หรือค้นหาตึก/เลขห้องที่ว่าง | คืนค่า `None` หรือแจ้ง "Not Found" สุภาพ ห้ามเกิด Uncaught Exception |
| **T2.6** | Remove Guest Cleanliness | ลบแขกรายคนออกจากระบบ | ข้อมูลถูกถอนออกจากดัชนีทั้ง 2 ฝั่ง แขกคนอื่นไม่ได้รับผลกระทบ และไม่มีช่องว่างห้องตกค้าง |

---

### 🧪 Suite 3: Migration Engine & Load Balance (`tests/test_task3_migration.py`)
**เป้าหมาย:** ทดสอบกฎเหล็กการย้ายแขก ความถูกต้องของสถิติโหลด และ Edge Cases ของอาคาร

| รหัสทดสอบ | ชื่อกรณีทดสอบ | เงื่อนไขและสิ่งที่ต้องตรวจสอบ | เกณฑ์การผ่าน (Assertion) |
| :--- | :--- | :--- | :--- |
| **T3.1** | Add Building Invariant (กฎเหล็ก 1) | เพิ่มอาคารใหม่เข้าสู่ระบบที่มีแขกอยู่แล้ว | **แขกที่ย้าย ต้องย้ายมาจากอาคารอื่นเข้าสู่อาคารใหม่นี้เท่านั้น!** แขกในอาคารเดิมห้ามสลับตึกกันเองเด็ดขาด |
| **T3.2** | Remove Building Invariant (กฎเหล็ก 2) | ลบอาคารใดอาคารหนึ่งออกจากระบบ | **มีเฉพาะแขกในอาคารที่ถูกลบเท่านั้นที่ย้าย** แขกในอาคารอื่นที่ไม่ถูกลบต้องไม่ย้ายตึกเด็ดขาด |
| **T3.3** | Room Number Invariant on Migration | ตรวจสอบแขกทุกคนที่อยู่ใน Migration Log | ค่า `room_no` ของแขกที่ย้าย ต้องเท่าเดิมทุกประการ เปลี่ยนเฉพาะ `node_id` |
| **T3.4** | Guest Conservation Rule | เปรียบเทียบจำนวนแขกก่อนและหลัง Add/Remove ตึก | จำนวนแขกรวมในระบบต้องเท่าเดิมเป๊ะ ไม่หาย ไม่เกิน และเท่ากับยอดใน Migration Log |
| **T3.5** | Migration Rate Calculation | คำนวณอัตราการย้าย: $\text{Rate} = \text{moved} / K$ | ถ้า $K > 0$ ได้อัตราถูกต้อง, ถ้า $K = 0$ รายงานคนย้าย 0 คน และไม่เกิด `ZeroDivisionError` |
| **T3.6** | Load Balance Stats Integrity | คำนวณ Max, Min, Mean, Std Dev, $CV = \sigma / \mu$ | คำนวณถูกต้องตามสูตรคณิตศาสตร์ รวมอาคารที่มีแขก 0 คน และกรณี $K=0$ ต้องแสดง $CV = \text{N/A}$ ไม่แครช |
| **T3.7** | Occupied Rooms Sorting | เรียกฟังก์ชันแสดงห้องที่ไม่ว่าง | เรียงลำดับตาม `node_id` น้อยไปมาก และภายในตึกเรียงตาม `room_no` ตัวเลขน้อยไปมาก |
| **T3.8** | Edge Case: Reject $N=1$ Removal | สั่งลบอาคารเมื่อเหลืออาคารเดียวในระบบ ($N=1$) | **ต้องปฏิเสธอย่างสุภาพทันที** ระบบต้องรักษากฎ $N \ge 1$ เสมอ |
| **T3.9** | Edge Case: Duplicate / Missing Node | - เพิ่มอาคารที่มีชื่อซ้ำ<br>- ลบอาคารที่ไม่มีอยู่จริง | ปฏิเสธสุภาพ รายงานย้าย 0 คน ไม่ทำให้ระบบพัง |

---

### 🧪 Suite 4: End-to-End & CSV Export Integration (`tests/test_task4_integration.py`)
**เป้าหมาย:** ทดสอบความสมบูรณ์ของระบบส่งออกไฟล์ การจำลองข้อมูล และการทำงานร่วมกันทุกโมดูล

| รหัสทดสอบ | ชื่อกรณีทดสอบ | เงื่อนไขและสิ่งที่ต้องตรวจสอบ | เกณฑ์การผ่าน (Assertion) |
| :--- | :--- | :--- | :--- |
| **T4.1** | CSV Row Count Match (โจทย์ข้อ 12) | เพิ่มแขก $K$ คน แล้วสั่ง Export CSV แขก | ไฟล์เข้ารหัส UTF-8 และจำนวนบรรทัดของ CSV (ไม่รวม Header) ต้องเท่ากับ $K$ ในระบบเป๊ะ |
| **T4.2** | CSV Headers & Columns | ตรวจสอบหัวตารางของไฟล์ CSV | มีคอลัมน์ครบถ้วน: `channel_id`, `sequence_id`, `node_id`, `room_no` |
| **T4.3** | Migration Log CSV Export | สั่งย้ายตึกแล้ว Export รายการย้ายเป็น CSV | คอลัมน์ครบ: `channel_id`, `sequence_id`, `old_node`, `new_node`, `room_no` และจำนวนตรงกับเหตุการณ์จริง |
| **T4.4** | Experiment Data Distribution | สั่งสร้างชุดแขกจำลอง $K = 1,000$ | แขกต้องถูกสร้างกระจายสม่ำเสมอใน 10 ช่องทาง ($c \in [1, 10]$) และลำดับ $s$ เริ่มต้นที่ 1 |
| **T4.5** | 10 Core Functions Smoke Test | จำลองเรียกใช้ครบ 10 ฟังก์ชันหลักของระบบต่อเนื่องกัน | ทุกฟังก์ชันทำงานประสานกันได้สมบูรณ์ ไม่มีการเกิด Exception หลุดออกมา |

---

## ⚙️ โครงสร้างไฟล์ GitHub Actions Workflow (`.github/workflows/tests.yml`)

```yaml
name: Automated CI Test Suite

on:
  push:
    branches: [ "main", "task-*/**" ]
  pull_request:
    branches: [ "main" ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    steps:
    - name: Checkout Repository
      uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install Dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest pytest-cov

    - name: Run All Test Suites
      run: |
        pytest tests/ -v --tb=short
```

---

## 📊 ประโยชน์ของการทำ CI/CD สำหรับส่งงาน OODS
1. **หลักฐานความถูกต้อง 100% (ตรงตามเกณฑ์ 9 คะแนน):** ในรายงานสามารถแนบ Badge `CI Passing` และภาพการรันเทสต์อัตโนมัติบน GitHub
2. **ป้องกันเพื่อนทำโค้ดพังก่อน Merge:** หากสมาชิกคนใดแก้โค้ดแล้วทำผิดกฎเหล็ก (เช่น เลขห้องเปลี่ยน หรือแขกหาย) PR จะขึ้นสีแดง ❌ ทันที
3. **การันตีความสอดคล้องข้ามระบบปฏิบัติการ:** โค้ดจะถูกเทสต์บน Clean Environment ของ GitHub ทำให้มั่นใจได้ว่าอาจารย์นำไปรันบนเครื่องใดก็ผ่านแน่นอน
