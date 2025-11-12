const API_ALIASES = '/api/aliases';
const API_UNKNOWNS = '/api/review/unknown-columns';
const API_IGNORE = '/api/review/ignore';

const statusEl = document.getElementById('reviewStatus');
const tableBody = document.getElementById('reviewTableBody');

let canonicalFields = [];
let columnsData = [];

async function initReviewBoard() {
  try {
    const [aliases, unknowns] = await Promise.all([
      fetch(API_ALIASES).then((res) => res.json()),
      fetch(API_UNKNOWNS).then((res) => res.json())
    ]);
    canonicalFields = Object.keys(aliases.aliases || {}).map((key) => ({
      key,
      label: toFieldLabel(key),
    }));
    columnsData = unknowns.columns || [];
    renderTable();
    if (!columnsData.length) {
      statusEl.textContent = 'لا توجد أعمدة مجهولة تحتاج للمراجعة.';
    } else {
      statusEl.textContent = `تم العثور على ${columnsData.length} عمودًا يحتاج للمراجعة.`;
    }
  } catch (error) {
    console.error('Review board load error', error);
    statusEl.textContent = 'تعذر تحميل البيانات. تأكد من أن الخادم يعمل.';
  }
}

function renderTable() {
  if (!columnsData.length) {
    tableBody.innerHTML = '<tr><td colspan="5" class="muted">لا توجد بيانات حالياً.</td></tr>';
    return;
  }
  tableBody.innerHTML = columnsData.map((column, index) => `
    <tr>
      <td data-label="اسم العمود">
        <strong>${column.label}</strong>
        <div class="muted">آخر ظهور: ${formatDate(column.last_seen)}</div>
      </td>
      <td data-label="عدد التكرارات">${column.count}</td>
      <td data-label="الأوراق">
        <div class="tags">${renderTags(column.sheets)}</div>
      </td>
      <td data-label="الملفات">
        <div class="tags">${renderTags(column.files)}</div>
      </td>
      <td data-label="الإجراء">
        <div class="actions">
          ${renderSelect(index)}
          <button class="btn-primary" data-action="add" data-index="${index}">إضافة للمراجع</button>
          <button class="btn-secondary" data-action="ignore" data-index="${index}">تجاهل</button>
        </div>
      </td>
    </tr>
  `).join('');
  tableBody.querySelectorAll('button').forEach((btn) => {
    btn.addEventListener('click', handleActionClick);
  });
}

function renderTags(items = []) {
  if (!items.length) {
    return '<span class="tag">—</span>';
  }
  return items.map((item) => `<span class="tag">${item}</span>`).join('');
}

function renderSelect(index) {
  const options = [
    '<option value="">اختر الحقل القياسي</option>',
    ...canonicalFields.map((field) => `<option value="${field.key}">${field.label}</option>`)
  ].join('');
  return `<select data-select="${index}">${options}</select>`;
}

function toFieldLabel(key) {
  const labels = {
    bank_name: 'اسم البنك',
    guarantee_number: 'رقم الضمان',
    contract_number: 'رقم العقد',
    amount: 'مبلغ الضمان',
    validity_date: 'تاريخ الانتهاء',
    company_name: 'اسم الشركة',
  };
  return labels[key] || key;
}

function formatDate(value) {
  if (!value) {
    return '—';
  }
  try {
    return new Intl.DateTimeFormat('ar-SA', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(value));
  } catch (error) {
    return value;
  }
}

async function handleActionClick(event) {
  const button = event.currentTarget;
  const index = Number(button.dataset.index);
  const column = columnsData[index];
  if (!column) {
    return;
  }
  if (button.dataset.action === 'add') {
    await addAliasFromReview(column, index);
  } else if (button.dataset.action === 'ignore') {
    await ignoreColumnFromReview(column, index);
  }
}

async function addAliasFromReview(column, index) {
  const select = tableBody.querySelector(`select[data-select="${index}"]`);
  const canonical = select?.value;
  if (!canonical) {
    alert('الرجاء اختيار الحقل القياسي لهذا العمود.');
    return;
  }
  try {
    setRowBusy(index, true);
    const response = await fetch(API_ALIASES, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ canonical, alias: column.label }),
    });
    const payload = await response.json();
    if (!response.ok || payload.error) {
      throw new Error(payload.error || 'تعذر إضافة العمود للمراجع.');
    }
    statusEl.textContent = `تمت إضافة "${column.label}" إلى ${toFieldLabel(canonical)}.`;
    columnsData.splice(index, 1);
    renderTable();
  } catch (error) {
    console.error('Review alias add failed', error);
    alert(error.message);
  } finally {
    setRowBusy(index, false);
  }
}

async function ignoreColumnFromReview(column, index) {
  if (!confirm(`هل تريد تجاهل العمود "${column.label}"؟`)) {
    return;
  }
  try {
    setRowBusy(index, true);
    const response = await fetch(API_IGNORE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ label: column.label }),
    });
    const payload = await response.json();
    if (!response.ok || payload.error) {
      throw new Error(payload.error || 'تعذر تجاهل العمود.');
    }
    statusEl.textContent = `تم تجاهل العمود "${column.label}".`;
    columnsData.splice(index, 1);
    renderTable();
  } catch (error) {
    console.error('Review ignore failed', error);
    alert(error.message);
  } finally {
    setRowBusy(index, false);
  }
}

function setRowBusy(index, isBusy) {
  const row = tableBody.querySelector(`tr:nth-child(${index + 1})`);
  if (!row) {
    return;
  }
  row.style.opacity = isBusy ? 0.5 : 1;
  const buttons = row.querySelectorAll('button');
  buttons.forEach((button) => { button.disabled = isBusy; });
}

document.addEventListener('DOMContentLoaded', initReviewBoard);
