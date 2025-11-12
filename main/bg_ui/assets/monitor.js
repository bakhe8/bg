const logSelector = document.getElementById('logSelector');
const logLimitInput = document.getElementById('logLimit');
const refreshBtn = document.getElementById('refreshLogsBtn');
const output = document.getElementById('logsOutput');
const statusEl = document.getElementById('monitorStatus');

async function loadLogs() {
  const file = logSelector.value;
  const limit = Number(logLimitInput.value) || 200;
  statusEl.textContent = 'جارٍ تحميل السجل...';
  output.textContent = '--';
  try {
    const response = await fetch(`/api/logs?file=${file}&limit=${limit}`, {
      headers: { 'Accept': 'application/json' }
    });
    if (response.status === 401) {
      statusEl.textContent = 'يتطلب تسجيل دخول للوصول إلى السجلات.';
      output.textContent = '--';
      return;
    }
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || 'تعذر تحميل السجل');
    }
    const entries = payload.entries || [];
    output.textContent = entries.length ? entries.join('\n') : (payload.message || 'لا توجد بيانات.');
    statusEl.textContent = `تم تحميل ${entries.length} سطر من سجل ${file}.`;
  } catch (error) {
    console.error('log load failed', error);
    statusEl.textContent = `تعذر تحميل السجل: ${error.message}`;
    output.textContent = '--';
  }
}

refreshBtn?.addEventListener('click', loadLogs);
document.addEventListener('DOMContentLoaded', loadLogs);
