const cfg = window.APP_CONFIG || {};
const api = {
  auth: (cfg.AUTH_API_URL || "http://127.0.0.1:8000/api/v1").replace(/\/$/, ""),
  finance: (cfg.FINANCE_API_URL || "http://127.0.0.1:8001/api/v1").replace(/\/$/, ""),
  reports: (cfg.REPORT_API_URL || "http://127.0.0.1:8002/api/v1").replace(/\/$/, ""),
};
const root = document.querySelector("#app");
const now = new Date();
const state = { token: sessionStorage.getItem("access_token"), report: null, categories: [], transactions: [], todayExpenses: [], debts: [], period: { year: now.getFullYear(), month: now.getMonth() + 1 } };
const money = new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });
const formatMoney = value => money.format(Number(value || 0));
const safe = value => String(value ?? "").replace(/[&<>'"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[c]));
const weakParts = value => [value.length < 8 && "8 caracteres", !/[a-z]/.test(value) && "una minúscula", !/[A-Z]/.test(value) && "una mayúscula", !/\d/.test(value) && "un número"].filter(Boolean);

async function apiCall(base, path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(`${base}${path}`, { ...options, headers });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail?.[0]?.msg || body.detail || `Error ${response.status}`);
  return body;
}

function showAuth(register = false, error = "") {
  root.innerHTML = `<main class="auth-shell"><section class="auth-copy"><p class="eyebrow">LEDGER / FINANZAS PERSONALES</p><h1>Tu dinero, con dirección.</h1><p>Una vista clara para saber cuánto entra, cuánto sale y qué sigue.</p><div class="orbit"><span>INGRESOS</span><span>GASTOS</span><span>AHORRO</span></div></section><section class="auth-card"><p class="eyebrow">${register ? "NUEVA CUENTA" : "BIENVENIDO DE NUEVO"}</p><h2>${register ? "Empieza a ordenar tu dinero" : "Entra a tu espacio"}</h2><p class="muted">${register ? "Tu sesión se abrirá automáticamente." : "Consulta tu balance y tus próximos movimientos."}</p><form id="auth-form"><label>Correo electrónico<input id="email" type="email" placeholder="tu@correo.com" required></label><label>Contraseña<div class="password-wrap"><input id="password" type="password" placeholder="Tu contraseña" required><button class="text-button" id="show-password" type="button">Ver</button></div></label>${register ? '<p class="hint">Mínimo 8 caracteres, una mayúscula, una minúscula y un número.</p>' : ""}<button class="primary-button" type="submit">${register ? "Crear cuenta" : "Iniciar sesión"}<span>→</span></button><p class="form-message error-text">${safe(error)}</p></form><button class="switch-button" id="switch-auth">${register ? "Ya tengo una cuenta" : "Crear una cuenta"}</button></section></main>`;
  document.querySelector("#switch-auth").onclick = () => showAuth(!register);
  document.querySelector("#show-password").onclick = event => { const field = document.querySelector("#password"); field.type = field.type === "password" ? "text" : "password"; event.currentTarget.textContent = field.type === "password" ? "Ver" : "Ocultar"; };
  document.querySelector("#auth-form").onsubmit = async event => { event.preventDefault(); const email = document.querySelector("#email").value.trim(); const password = document.querySelector("#password").value; try { const missing = register ? weakParts(password) : []; if (missing.length) throw new Error(`La contraseña necesita ${missing.join(", ")}.`); const result = await apiCall(api.auth, register ? "/auth/register" : "/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }); state.token = result.access_token; sessionStorage.setItem("access_token", state.token); await loadApp(); } catch (caught) { showAuth(register, caught.message); } };
}

async function loadApp(period = state.period) {
  state.period = period;
  const start = new Date(period.year, period.month - 1, 1).toISOString().slice(0, 10);
  const end = new Date(period.year, period.month, 0).toISOString().slice(0, 10);
  try {
    [state.report, state.categories, state.transactions, state.todayExpenses, state.debts] = await Promise.all([apiCall(api.reports, `/reports/dashboard?start=${start}&end=${end}&granularity=day`), apiCall(api.finance, "/finance/categories"), apiCall(api.finance, "/finance/transactions?page=1&page_size=20"), apiCall(api.finance, `/finance/transactions?start=${end}&end=${end}&page=1&page_size=100`), apiCall(api.finance, "/finance/debts")]);
    showDashboard();
  } catch (caught) { showDashboard(caught.message); }
}

function logout() { state.token = null; sessionStorage.removeItem("access_token"); document.querySelector("#action-menu")?.remove(); showAuth(); }
function nav() { document.querySelectorAll("[data-page]").forEach(button => button.onclick = () => button.dataset.page === "dashboard" ? showDashboard() : showPage(button.dataset.page)); document.querySelectorAll("#logout").forEach(button => button.onclick = logout); }

function showTransactionModal() {
  const categoryOptions = state.categories.map(category => `<option value="${category.id}" data-type="${category.type}">${safe(category.name)} · ${category.type === "income" ? "Ingreso" : "Gasto"}</option>`).join("");
  const modal = document.createElement("div");
  modal.className = "modal-backdrop";
  modal.innerHTML = `<section class="modal" role="dialog" aria-modal="true" aria-labelledby="movement-title"><button class="modal-close" id="close-movement" aria-label="Cerrar">×</button><p class="eyebrow">NUEVO MOVIMIENTO</p><h2 id="movement-title">Registrar ingreso o gasto</h2><form id="movement-form"><label>Tipo<select id="movement-type"><option value="income">Ingreso</option><option value="expense">Gasto</option></select></label><label>Categoría<select id="movement-category"><option value="">Sin categoría</option>${categoryOptions}</select></label><label>Importe en COP<input id="movement-amount" type="number" min="1" step="1" placeholder="0" required></label><label>Fecha<input id="movement-date" type="date" value="${new Date().toISOString().slice(0, 10)}" required></label><label>Descripción<input id="movement-description" maxlength="500" placeholder="Ej. Salario, mercado, transporte..."></label><p class="form-message error-text" id="movement-error"></p><button class="primary-button" type="submit">Guardar movimiento <span>→</span></button></form></section>`;
  document.body.appendChild(modal);
  const type = modal.querySelector("#movement-type");
  const category = modal.querySelector("#movement-category");
  const syncCategories = () => { [...category.options].forEach(option => { option.hidden = option.value && option.dataset.type !== type.value; }); if (category.selectedOptions[0]?.hidden) category.value = ""; };
  syncCategories();
  type.onchange = syncCategories;
  modal.querySelector("#close-movement").onclick = () => modal.remove();
  modal.onclick = event => { if (event.target === modal) modal.remove(); };
  modal.querySelector("#movement-form").onsubmit = async event => {
    event.preventDefault();
    const submit = modal.querySelector("button[type=submit]");
    const error = modal.querySelector("#movement-error");
    submit.disabled = true;
    error.textContent = "";
    try {
      await apiCall(api.finance, "/finance/transactions", { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ category_id: modal.querySelector("#movement-category").value ? Number(modal.querySelector("#movement-category").value) : null, type: type.value, amount: modal.querySelector("#movement-amount").value, currency: "COP", transaction_date: modal.querySelector("#movement-date").value, description: modal.querySelector("#movement-description").value || null }) });
      modal.remove();
      await loadApp();
    } catch (caught) { error.textContent = caught.message; submit.disabled = false; }
  };
}

function showExpenseModal() {
  const categoryOptions = state.categories.filter(category => category.type === "expense").map(category => `<option value="${category.id}">${safe(category.name)}</option>`).join("");
  const modal = document.createElement("div");
  modal.className = "modal-backdrop";
  modal.innerHTML = `<section class="modal quick-expense" role="dialog" aria-modal="true"><button class="modal-close" id="close-expense" aria-label="Cerrar">×</button><p class="eyebrow">GASTO DIARIO</p><h2>Registrar gasto</h2><p class="muted">Completa estos campos y queda guardado en segundos.</p><form id="expense-form"><label>Valor en COP<input id="expense-amount" type="number" min="1" step="1" inputmode="numeric" placeholder="0" required autofocus></label><label>Categoría<select id="expense-category" required><option value="">Selecciona una categoría</option>${categoryOptions}</select></label><label>Fecha<input id="expense-date" type="date" value="${new Date().toISOString().slice(0, 10)}" required></label><label>Nota <span class="muted">(opcional)</span><input id="expense-note" maxlength="500" placeholder="Ej. almuerzo, bus, cine..."></label><p class="form-message error-text" id="expense-error"></p><button class="primary-button" type="submit">Guardar gasto <span>→</span></button></form></section>`;
  document.body.appendChild(modal);
  modal.querySelector("#close-expense").onclick = () => modal.remove();
  modal.onclick = event => { if (event.target === modal) modal.remove(); };
  modal.querySelector("#expense-form").onsubmit = async event => {
    event.preventDefault();
    const submit = modal.querySelector("button[type=submit]");
    const error = modal.querySelector("#expense-error");
    submit.disabled = true;
    try {
      await apiCall(api.finance, "/finance/transactions", { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ type: "expense", amount: modal.querySelector("#expense-amount").value, category_id: Number(modal.querySelector("#expense-category").value), currency: "COP", transaction_date: modal.querySelector("#expense-date").value, description: modal.querySelector("#expense-note").value || null }) });
      modal.remove();
      await loadApp();
    } catch (caught) { error.textContent = caught.message; submit.disabled = false; }
  };
}

function showRecurringIncomeModal(type = "income") {
  const categoryOptions = state.categories.filter(category => category.type === type).map(category => `<option value="${category.id}">${safe(category.name)}</option>`).join("");
  const modal = document.createElement("div");
  modal.className = "modal-backdrop";
  const label = type === "expense" ? "GASTO FIJO MENSUAL" : "INGRESO RECURRENTE";
  const title = type === "expense" ? "Programar gasto fijo" : "Programar ingreso";
  const placeholder = type === "expense" ? "Ej. Arriendo, energía, internet" : "Ej. Salario";
  modal.innerHTML = `<section class="modal" role="dialog" aria-modal="true"><button class="modal-close" id="close-recurring" aria-label="Cerrar">×</button><p class="eyebrow">${label}</p><h2>${title}</h2><form id="recurring-form"><label>Categoría<select id="recurring-category"><option value="">Sin categoría</option>${categoryOptions}</select></label><label>Valor estimado en COP<input id="recurring-amount" type="number" min="1" step="1" required></label><label>Frecuencia<select id="recurring-rule"><option value="monthly">Mensual</option>${type === "income" ? '<option value="biweekly">Quincenal</option>' : ""}</select></label><label>Primera fecha<input id="recurring-date" type="date" value="${new Date().toISOString().slice(0, 10)}" required></label><label>Nombre<input id="recurring-description" maxlength="500" placeholder="${placeholder}"></label><p class="form-message error-text" id="recurring-error"></p><button class="primary-button" type="submit">Guardar recurrencia <span>→</span></button></form></section>`;
  document.body.appendChild(modal);
  modal.querySelector("#close-recurring").onclick = () => modal.remove();
  modal.onclick = event => { if (event.target === modal) modal.remove(); };
  modal.querySelector("#recurring-form").onsubmit = async event => {
    event.preventDefault();
    const submit = modal.querySelector("button[type=submit]");
    const error = modal.querySelector("#recurring-error");
    submit.disabled = true;
    try {
      await apiCall(api.finance, "/finance/recurring", { method: "POST", body: JSON.stringify({ category_id: modal.querySelector("#recurring-category").value ? Number(modal.querySelector("#recurring-category").value) : null, type, amount: modal.querySelector("#recurring-amount").value, recurrence_rule: modal.querySelector("#recurring-rule").value, next_run: modal.querySelector("#recurring-date").value, description: modal.querySelector("#recurring-description").value || null }) });
      modal.remove();
      await loadApp();
    } catch (caught) { error.textContent = caught.message; submit.disabled = false; }
  };
}

function showDashboard(error = "") {
  const report = state.report || { overview: {}, cash_flow: [], expenses_by_category: [], recent_transactions: [], insights: [] };
  const overview = report.overview;
  root.innerHTML = `<div class="app-shell"><aside class="sidebar"><div class="brand"><span class="brand-mark">L</span><span>ledger</span></div><nav><button class="nav-item active" data-page="dashboard">◈ <span>Resumen</span></button><button class="nav-item" data-page="transactions">↗ <span>Movimientos</span></button></nav><div class="side-bottom"><span class="cop-badge">COP</span><button class="logout" id="logout">Salir</button></div></aside><main class="content"><header class="topbar"><div><p class="eyebrow">RESUMEN MENSUAL</p><h1>Hola, vuelve a tomar el control.</h1></div><button class="avatar" id="logout">↗</button></header>${error ? `<div class="alert error-text">${safe(error)}</div>` : ""}<section class="hero-grid"><article class="balance-card"><div><p class="card-label">BALANCE NETO</p><strong>${formatMoney(overview.net)}</strong><p class="balance-note">${overview.savings_rate || 0}% de ahorro</p></div><span class="balance-glyph">₱</span></article><article class="metric-card"><p class="card-label">INGRESOS</p><strong>${formatMoney(overview.income)}</strong><span class="positive">${overview.income_count || 0} movimientos</span></article><article class="metric-card warm"><p class="card-label">GASTOS</p><strong>${formatMoney(overview.expenses)}</strong><span class="negative">${overview.expense_count || 0} movimientos</span></article></section><section class="dashboard-grid"><article class="surface"><div class="section-heading"><div><p class="eyebrow">RITMO DEL DINERO</p><h2>Flujo de caja</h2></div><span class="pill">COP</span></div><div class="bars">${renderBars(report.cash_flow)}</div></article><article class="surface"><div class="section-heading"><div><p class="eyebrow">DISTRIBUCIÓN</p><h2>Gastos por categoría</h2></div></div>${renderCategories(report.expenses_by_category)}</article></section><section class="dashboard-grid lower-grid"><article class="surface"><div class="section-heading"><div><p class="eyebrow">ACTIVIDAD</p><h2>Últimos movimientos</h2></div><button class="link-button" data-page="transactions">Ver todos →</button></div>${renderRecent(report.recent_transactions)}</article><article class="surface"><div class="section-heading"><div><p class="eyebrow">SEÑALES</p><h2>Lecturas del mes</h2></div></div>${renderInsights(report.insights)}</article></section></main></div>`;
  nav();
  renderDailyExpenses();
  renderDebts();
  renderPeriodSelector();
  movementButton.className = "primary-button floating-action";
  movementButton.id = "action-menu";
  movementButton.textContent = "+ Nueva acción";
  movementButton.onclick = () => document.querySelector("#action-options").classList.toggle("open");
  const actions = document.createElement("div");
  actions.id = "action-options";
  actions.className = "action-options";
  actions.innerHTML = '<button type="button" data-action="expense">Registrar gasto</button><button type="button" data-action="income">Registrar ingreso</button><button type="button" data-action="fixed-expense">Programar gasto fijo mensual</button><button type="button" data-action="recurring">Programar ingreso recurrente</button>';
  document.body.appendChild(actions);
  actions.querySelector('[data-action="expense"]').onclick = () => { actions.classList.remove("open"); showExpenseModal(); };
  actions.querySelector('[data-action="income"]').onclick = () => { actions.classList.remove("open"); showTransactionModal(); };
  actions.querySelector('[data-action="recurring"]').onclick = () => { actions.classList.remove("open"); showRecurringIncomeModal(); };
  actions.querySelector('[data-action="fixed-expense"]').onclick = () => { actions.classList.remove("open"); showRecurringIncomeModal("expense"); };
}

function renderPeriodSelector() {
  document.querySelector("#period-selector")?.remove();
  const selector = document.createElement("div");
  selector.id = "period-selector";
  selector.className = "period-selector";
  const months = Array.from({ length: 12 }, (_, index) => `<option value="${index + 1}" ${state.period.month === index + 1 ? "selected" : ""}>${new Date(2020, index, 1).toLocaleDateString("es-CO", { month: "long" })}</option>`).join("");
  selector.innerHTML = `<label>Periodo<select id="period-month">${months}</select><select id="period-year"><option ${state.period.year === now.getFullYear() - 1 ? "selected" : ""}>${now.getFullYear() - 1}</option><option ${state.period.year === now.getFullYear() ? "selected" : ""}>${now.getFullYear()}</option><option ${state.period.year === now.getFullYear() + 1 ? "selected" : ""}>${now.getFullYear() + 1}</option></select></label>`;
  document.querySelector(".topbar")?.appendChild(selector);
  const reloadPeriod = () => loadApp({ year: Number(selector.querySelector("#period-year").value), month: Number(selector.querySelector("#period-month").value) });
  selector.querySelector("#period-month").onchange = reloadPeriod;
  selector.querySelector("#period-year").onchange = reloadPeriod;
}

function renderDebts() {
  document.querySelector("#debts-progress")?.remove();
  const section = document.createElement("section");
  section.className = "surface debts-progress";
  section.innerHTML = `<div class="section-heading"><div><p class="eyebrow">COMPROMISOS FINANCIEROS</p><h2>Progreso de deudas</h2></div></div>${state.debts?.map(debt => `<div class="debt-row"><div class="debt-heading"><strong>${safe(debt.name)}</strong><span>${formatMoney(debt.paid_amount)} de ${formatMoney(debt.total_amount)}</span></div><div class="debt-progress"><i style="width:${Math.min(100, debt.progress_percentage)}%"></i></div><div class="debt-meta"><small>${debt.progress_percentage}% pagado · saldo ${formatMoney(debt.remaining_amount)}</small><small>${debt.estimated_end_date ? `Final estimado: ${debt.estimated_end_date}` : "Sin fecha estimada"}</small></div></div>`).join("") || '<p class="empty">No tienes deudas registradas.</p>'}`;
  document.querySelector(".content")?.appendChild(section);
}

function renderDailyExpenses() {
  document.querySelector("#daily-expenses")?.remove();
  const section = document.createElement("section");
  section.id = "daily-expenses";
  section.className = "surface daily-expenses";
  const items = state.todayExpenses?.items || [];
  section.innerHTML = `<div class="section-heading"><div><p class="eyebrow">HOY · ${new Date().toLocaleDateString("es-CO", { day: "2-digit", month: "long" })}</p><h2>Gastos del día</h2></div><strong>${formatMoney(items.filter(item => item.type === "expense").reduce((total, item) => total + Number(item.amount), 0))}</strong></div>${items.filter(item => item.type === "expense").map(item => `<div class="daily-expense-row"><span class="recent-icon expense">↗</span><div><strong>${safe(item.description || "Gasto")}</strong><small>${safe(state.categories.find(category => category.id === item.category_id)?.name || "Sin categoría")}</small></div><b>${formatMoney(item.amount)}</b></div>`).join("") || '<p class="empty">Aún no registras gastos hoy.</p>'}`;
  document.querySelector(".content")?.appendChild(section);
}
function renderBars(items = []) { if (!items.length) return '<p class="empty">Aún no hay movimientos en este periodo.</p>'; const max = Math.max(...items.map(item => Number(item.income) + Number(item.expenses)), 1); return items.slice(-12).map(item => `<div class="bar-column"><div class="bar-stack"><i class="bar income" style="height:${Math.max(4, Number(item.income) / max * 150)}px"></i><i class="bar expense" style="height:${Math.max(4, Number(item.expenses) / max * 150)}px"></i></div><small>${safe(item.period.slice(-5))}</small></div>`).join(""); }
function renderCategories(items = []) { if (!items.length) return '<p class="empty">No hay categorías con gastos todavía.</p>'; return items.slice(0, 5).map(item => `<div class="category-row"><span class="category-icon">${safe(item.category_name[0])}</span><div class="category-main"><div><strong>${safe(item.category_name)}</strong><span>${formatMoney(item.amount)}</span></div><div class="progress"><i style="width:${Math.min(100, item.percentage)}%"></i></div><small>${item.percentage}% del total</small></div></div>`).join(""); }
function renderRecent(items = []) { if (!items.length) return '<p class="empty">Aún no hay movimientos registrados.</p>'; return items.slice(0, 6).map(item => `<div class="recent-row"><span class="recent-icon ${item.type}">${item.type === "income" ? "↙" : "↗"}</span><div><strong>${safe(item.description || (item.type === "income" ? "Ingreso" : "Gasto"))}</strong><small>${safe(item.category_name || "Sin categoría")} · ${safe(item.date || item.transaction_date || "")}</small></div><b class="amount ${item.type}">${item.type === "income" ? "+" : "−"}${formatMoney(item.amount)}</b></div>`).join(""); }
function renderInsights(items = []) { if (!items.length) return '<p class="empty">Tus señales aparecerán aquí.</p>'; return items.slice(0, 4).map(item => `<div class="insight"><span class="insight-mark ${item.severity}">${item.severity === "warning" ? "!" : "✓"}</span><div><strong>${safe(item.title)}</strong><p>${safe(item.message)}</p></div></div>`).join(""); }
function showPage(name) { const titles = { transactions: "Movimientos" }; const content = transactionPage(); document.querySelector(".content").innerHTML = `<header class="topbar"><div><p class="eyebrow">LEDGER / ${titles[name].toUpperCase()}</p><h1>${titles[name]}</h1></div><button class="avatar" id="logout">↗</button></header><section class="surface section-page">${content}</section>`; nav(); }
function transactionPage() { const items = state.transactions.items || []; return `<div class="section-heading"><div><p class="eyebrow">REGISTRO FINANCIERO</p><h2>${state.transactions.total || 0} movimientos</h2></div></div><div class="table-wrap"><table><thead><tr><th>Fecha</th><th>Descripción</th><th>Tipo</th><th>Importe</th></tr></thead><tbody>${items.map(item => `<tr><td>${item.transaction_date}</td><td>${safe(item.description || "Sin descripción")}</td><td><span class="type ${item.type}">${item.type}</span></td><td class="amount ${item.type}">${item.type === "income" ? "+" : "−"}${formatMoney(item.amount)}</td></tr>`).join("")}</tbody></table></div>`; }
if (state.token) loadApp(); else showAuth();
