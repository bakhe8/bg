document.getElementById('convertBtn').addEventListener('click', () => {
  const file = document.getElementById('excelFile').files[0];
  const output = document.getElementById('jsonOutput');
  if (!file) {
    alert('📂 يرجى اختيار ملف Excel أولاً');
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    const data = new Uint8Array(e.target.result);
    const workbook = XLSX.read(data, { type: 'array' });
    const firstSheet = workbook.SheetNames[0];
    const sheet = workbook.Sheets[firstSheet];
    const rows = XLSX.utils.sheet_to_json(sheet, { defval: "" });

    const banks = {};
    rows.forEach(row => {
      const name = row["Name"] || row["Bank Name"] || row["البنك"];
      if (!name) return;
      banks[name] = {
        address: row["Address"] || row["العنوان"] || "",
        email: row["Email"] || row["البريد الإلكتروني"] || "",
        swift: row["SwiftCode"] || row["رمز السويفت"] || ""
      };
    });

    const jsonStr = JSON.stringify(banks, null, 4);
    output.textContent = jsonStr;

    // إنشاء ملف JSON قابل للتحميل
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = "bank-data.json";
    link.textContent = "⬇️ تحميل bank-data.json";
    output.appendChild(document.createElement('br'));
    output.appendChild(link);
  };

  reader.readAsArrayBuffer(file);
});
