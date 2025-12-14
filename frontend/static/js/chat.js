/**
 * Конфигурация API
 * Указывает адрес бэкенда для отправки запросов чата.
 */
const API_URL = 'http://localhost:8000/api/chat'; 

/**
 * Инициализация библиотеки Marked.js
 * Настраивает рендеринг Markdown:
 * - breaks: true -> перенос строки интерпретируется как <br>
 * - gfm: true -> поддержка таблиц и расширенного синтаксиса GitHub
 */
if (typeof marked !== 'undefined') marked.use({ breaks: true, gfm: true });

// === DOM Элементы интерфейса ===
const chatScroll = document.getElementById('chat-scroll');       // Область прокрутки сообщений
const chatContainer = document.getElementById('chat-container'); // Контейнер для пузырей сообщений
const chatInput = document.getElementById('chat-input');         // Поле ввода
const actionBtn = document.getElementById('action-btn');         // Кнопка Отправить/Стоп

// Элементы модального окна
const deleteModal = document.getElementById('delete-modal');
const modalBg = deleteModal?.querySelector('.modal-bg');
const modalPanel = deleteModal?.querySelector('.modal-panel');

// === SVG Иконки (встроенные для производительности) ===
const ICON_SEND = `<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>`;
const ICON_STOP = `<svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor" stroke="none"><rect x="4" y="4" width="16" height="16" rx="2" /></svg>`;
const ICON_DOC = `<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>`;
const ICON_EDIT = `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/></svg>`;
const ICON_TRASH = `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>`;

// === Управление состоянием (State Management) ===
let currentSessionId = null; // ID текущего активного чата (null = новый чат)
let chatHistory = [];        // Локальная история сообщений текущей сессии
let savedSessions = {};      // Все сохраненные сессии (загружаются из LocalStorage)
let pendingDeleteId = null;  // ID чата, который ожидает подтверждения удаления

// Загрузка сохраненных данных при старте
try {
  savedSessions = JSON.parse(localStorage.getItem('fas_chat_sessions') || '{}');
} catch (e) { 
  console.error("Ошибка чтения LocalStorage:", e);
  savedSessions = {}; 
}

/**
 * Инициализация приложения при загрузке страницы.
 * Рендерит список истории и открывает пустой чат.
 */
function initSessions() {
  renderHistoryList();
  startNewChat();
}

/**
 * Сбрасывает текущее состояние интерфейса к "Новому чату".
 * Очищает контейнер сообщений и сбрасывает currentSessionId.
 */
function startNewChat() {
  currentSessionId = null; 
  chatHistory = [];
  chatContainer.innerHTML = '';
  renderHistoryList();
  
  // Адаптив: закрываем меню на мобильных устройствах
  const sidebar = document.getElementById('sidebar');
  if(window.innerWidth < 1024 && sidebar) {
      sidebar.classList.add('translate-x-full');
      document.getElementById('overlay')?.classList.add('hidden');
  }
  if(chatInput) chatInput.focus();
}

/**
 * Сохраняет текущую сессию в LocalStorage.
 * 
 * Args:
 *   titleCandidate (string): Текст для заголовка (обычно первое сообщение пользователя).
 */
function saveSession(titleCandidate) {
  if (!currentSessionId) currentSessionId = Date.now().toString();
  
  // Если сессии нет, создаем структуру
  if (!savedSessions[currentSessionId]) {
    let title = titleCandidate;
    // Обрезаем слишком длинные заголовки
    if (title.length > 30) title = title.substring(0, 30) + '...';
    
    savedSessions[currentSessionId] = { 
      id: currentSessionId, 
      title: title, 
      timestamp: Date.now(), 
      messages: [] 
    };
  }
  
  savedSessions[currentSessionId].messages = chatHistory;
  savedSessions[currentSessionId].timestamp = Date.now();
  localStorage.setItem('fas_chat_sessions', JSON.stringify(savedSessions));
  renderHistoryList();
}

/**
 * Логика модального окна удаления.
 * 
 * openDeleteModal - Открывает окно с анимацией
 * closeDeleteModal - Закрывает окно
 * confirmDelete - Выполняет фактическое удаление из хранилища
 */
function openDeleteModal(e, id) {
  e.stopPropagation();
  pendingDeleteId = id;
  if(deleteModal) {
      deleteModal.classList.remove('hidden');
      // Небольшой таймаут для запуска CSS transition
      setTimeout(() => {
          modalBg.classList.remove('opacity-0');
          modalPanel.classList.remove('scale-95', 'opacity-0');
          modalPanel.classList.add('scale-100', 'opacity-100');
      }, 10);
  }
}

function closeDeleteModal() {
  if(deleteModal) {
      modalBg.classList.add('opacity-0');
      modalPanel.classList.remove('scale-100', 'opacity-100');
      modalPanel.classList.add('scale-95', 'opacity-0');
      setTimeout(() => {
          deleteModal.classList.add('hidden');
          pendingDeleteId = null;
      }, 200);
  }
}

function confirmDelete() {
  if (!pendingDeleteId || !savedSessions[pendingDeleteId]) {
      closeDeleteModal();
      return;
  }
  delete savedSessions[pendingDeleteId];
  localStorage.setItem('fas_chat_sessions', JSON.stringify(savedSessions));

  // Если удалили активный чат — переходим к новому
  if (currentSessionId === pendingDeleteId) {
      startNewChat();
  } else {
      renderHistoryList();
  }
  closeDeleteModal();
}

// Экспорт функций в глобальную область видимости для доступа из HTML (onclick)
window.closeDeleteModal = closeDeleteModal;
window.confirmDelete = confirmDelete;

/**
 * Запускает режим редактирования названия чата.
 * Заменяет текстовый span на input поле.
 * 
 * Args:
 *   e (Event): Событие клика (нужно для stopPropagation)
 *   id (string): ID сессии
 */
function startRenaming(e, id) {
  e.stopPropagation();
  const itemDiv = e.target.closest('.history-item');
  const titleSpan = itemDiv.querySelector('.history-title-span');
  const actionsDiv = itemDiv.querySelector('.history-actions');
  
  const currentTitle = savedSessions[id].title;
  
  // Скрываем UI элементы
  titleSpan.style.display = 'none';
  actionsDiv.style.display = 'none';

  // Создаем поле ввода
  const input = document.createElement('input');
  input.type = 'text';
  input.value = currentTitle;
  input.className = 'history-edit-input';
  
  const save = () => {
      const newTitle = input.value.trim();
      if (newTitle) {
          savedSessions[id].title = newTitle;
          localStorage.setItem('fas_chat_sessions', JSON.stringify(savedSessions));
      }
      renderHistoryList();
  };

  // Сохраняем по Enter или потере фокуса
  input.addEventListener('blur', save);
  input.addEventListener('keydown', (ev) => {
      if (ev.key === 'Enter') save();
      if (ev.key === 'Escape') renderHistoryList();
  });

  itemDiv.insertBefore(input, actionsDiv);
  input.focus();
  input.onclick = (ev) => ev.stopPropagation();
}

/**
 * Загружает выбранную сессию из памяти и отрисовывает её.
 * 
 * Args:
 *   id (string): ID сессии для загрузки
 */
function loadSession(id) {
  if (!savedSessions[id]) return;
  currentSessionId = id;
  chatHistory = savedSessions[id].messages || [];
  
  chatContainer.innerHTML = '';
  // Статический рендеринг всей истории
  chatHistory.forEach(msg => {
    if (msg.role === 'user') renderUserMessageStatic(msg.content);
    else renderBotMessageStatic(msg.content, msg.sources);
  });
  scrollToBottom();
  renderHistoryList();
  
  // Закрываем меню на мобильных
  const sidebar = document.getElementById('sidebar');
  if(window.innerWidth < 1024 && sidebar) {
      sidebar.classList.add('translate-x-full');
      document.getElementById('overlay')?.classList.add('hidden');
  }
}

/**
 * Рендерит список истории чатов в боковой панели.
 * Сортирует чаты по времени (новые сверху).
 */
function renderHistoryList() {
    // Всегда ищем элемент заново, так как DOM может обновляться
    const listEl = document.getElementById('history-list');
    if (!listEl) return;
    
    listEl.innerHTML = '';
    const sortedIds = Object.keys(savedSessions).sort((a,b) => savedSessions[b].timestamp - savedSessions[a].timestamp);
  
    if (sortedIds.length === 0) {
      listEl.innerHTML = '<div class="text-center opacity-40 text-sm mt-10">Нет истории чатов</div>';
      return;
    }
  
    sortedIds.forEach(id => {
      const session = savedSessions[id];
      const div = document.createElement('div');
      div.className = `history-item ${id === currentSessionId ? 'active' : ''}`;
      
      div.innerHTML = `
        <span class="history-title-span">${session.title || 'Без названия'}</span>
        <div class="history-actions">
           <button class="history-btn edit" title="Переименовать">${ICON_EDIT}</button>
           <button class="history-btn delete" title="Удалить">${ICON_TRASH}</button>
        </div>
      `;
      
      div.onclick = () => loadSession(id);
      
      const editBtn = div.querySelector('.edit');
      const deleteBtn = div.querySelector('.delete');
      
      editBtn.onclick = (e) => startRenaming(e, id);
      deleteBtn.onclick = (e) => openDeleteModal(e, id);
  
      listEl.appendChild(div);
    });
  }

// --- Функции отрисовки (Rendering) ---

function renderUserMessageStatic(text) {
  const row = document.createElement('div'); row.className = 'msg-row msg-user';
  const bubble = document.createElement('div'); bubble.className = 'bubble bubble-user';
  bubble.textContent = text;
  row.appendChild(bubble); chatContainer.appendChild(row);
}

function renderBotMessageStatic(rawMarkdown, sources) {
  const row = document.createElement('div'); row.className = 'msg-row msg-bot';
  const bubble = document.createElement('div'); bubble.className = 'bubble bubble-bot';
  
  // Если есть источники, рендерим блок документов
  if (sources && sources.length) {
     const docsBlock = document.createElement('div'); docsBlock.className = 'docs-block';
     docsBlock.innerHTML = `<div class="docs-title">${ICON_DOC} Источники</div><div class="docs-grid"></div>`;
     const grid = docsBlock.querySelector('.docs-grid');
     sources.forEach(doc => {
       const score = doc.score != null ? Number(doc.score).toFixed(2) : '--';
       const url = doc.url || doc.link || '#';
       grid.innerHTML += `
          <div class="doc-item">
             <div class="doc-icon-box">${ICON_DOC}</div>
             <div class="doc-content">
                <a href="${url}" target="_blank" class="doc-link" title="${url}">${url}</a>
                <div class="doc-meta-row"><span class="doc-badge">score: ${score}</span></div>
             </div>
          </div>`;
     });
     bubble.appendChild(docsBlock);
  }

  // Рендеринг основного текста (Markdown -> HTML)
  const answerDiv = document.createElement('div'); answerDiv.className = 'answer-markdown';
  // DOMPurify защищает от XSS атак
  answerDiv.innerHTML = DOMPurify.sanitize(marked.parse(rawMarkdown || ''));
  bubble.appendChild(answerDiv);
  row.appendChild(bubble); chatContainer.appendChild(row);
}

// --- Основная логика чата (Chat Logic) ---

let isLoading = false;
let abortController = null; // Позволяет прервать fetch запрос

function isAtBottom() { 
    // Считаем, что мы внизу, если до конца меньше 50px
    return chatScroll.scrollHeight - chatScroll.scrollTop - chatScroll.clientHeight <= 50; 
}

function scrollToBottom(smooth = false) {
  if (smooth) chatScroll.scrollTo({ top: chatScroll.scrollHeight, behavior: 'smooth' });
  else chatScroll.scrollTop = chatScroll.scrollHeight;
}

/**
 * Переключает состояние UI между "Ожидание" и "Генерация".
 * Блокирует ввод, меняет иконку кнопки.
 */
function updateUIState(loading) {
  isLoading = loading;
  chatInput.disabled = loading; 
  actionBtn.innerHTML = loading ? ICON_STOP : ICON_SEND;
  if(!loading) { chatInput.focus(); abortController = null; }
}

/**
 * Создает пустой пузырь сообщения бота с индикатором печати.
 * Возвращает объект с ссылками на DOM элементы для последующего обновления.
 */
function createBotMessage() {
  const row = document.createElement('div'); row.className = 'msg-row msg-bot';
  const bubble = document.createElement('div'); bubble.className = 'bubble bubble-bot';
  
  const docsBlock = document.createElement('div'); docsBlock.className = 'docs-block'; docsBlock.style.display = 'none';
  docsBlock.innerHTML = `<div class="docs-title">${ICON_DOC} Источники</div><div class="docs-grid"></div>`;
  
  const answerText = document.createElement('div'); answerText.className = 'answer-markdown';
  
  const typing = document.createElement('div'); typing.className = 'typing-indicator';
  typing.innerHTML = `<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>`;

  bubble.appendChild(docsBlock); bubble.appendChild(answerText); bubble.appendChild(typing);
  row.appendChild(bubble); chatContainer.appendChild(row);
  setTimeout(() => scrollToBottom(true), 10);
  
  return { 
      row, 
      bubble, 
      docsBlock, 
      docsGrid: docsBlock.querySelector('.docs-grid'), 
      answerText, 
      typing, 
      rawText: '', 
      typingRemoved: false, 
      sources: [] 
  };
}

/**
 * Обновляет список документов в пузыре бота.
 * Вызывается при получении события типа 'sources' от сервера.
 */
function updateDocs(botMsg, items) {
  if (!items || !items.length) return;
  botMsg.sources = items;
  botMsg.docsBlock.style.display = 'block'; 
  botMsg.docsGrid.innerHTML = '';
  items.forEach(doc => {
    const score = doc.score != null ? Number(doc.score).toFixed(2) : '--';
    const url = doc.url || doc.link || '#';
    botMsg.docsGrid.innerHTML += `
      <div class="doc-item">
         <div class="doc-icon-box">${ICON_DOC}</div>
         <div class="doc-content">
            <a href="${url}" target="_blank" class="doc-link" title="${url}">${url}</a>
            <div class="doc-meta-row">
              <span class="doc-badge">score: ${score}</span>
              <button onclick="navigator.clipboard.writeText('${url}')" class="doc-copy-btn">copy link</button>
            </div>
         </div>
      </div>`;
  });
  if (isAtBottom()) scrollToBottom(true);
}

// Дебаунс для рендеринга Markdown (оптимизация производительности)
let mdRenderTimer = null;
function scheduleMarkdownRender(botMsg) { 
  if (mdRenderTimer) clearTimeout(mdRenderTimer); 
  const userWasAtBottom = isAtBottom();
  mdRenderTimer = setTimeout(() => { 
    botMsg.answerText.innerHTML = DOMPurify.sanitize(marked.parse(botMsg.rawText));
    if (userWasAtBottom) scrollToBottom(false); 
  }, 40); 
}

/**
 * Основная функция отправки запроса.
 * Реализует паттерн Streaming Response.
 * 
 * Args:
 *   query (string): Текст запроса пользователя
 */
async function sendQuery(query) { 
  if (!query) return;
  abortController = new AbortController();
  
  // Если это первое сообщение — инициализируем сессию
  if (!currentSessionId) {
      currentSessionId = Date.now().toString();
      chatHistory = [];
      saveSession(query);
  }

  updateUIState(true); 
  renderUserMessageStatic(query); 
  chatHistory.push({ role: "user", content: query });
  saveSession(savedSessions[currentSessionId].title); 

  const botMsg = createBotMessage();

  try {
    // Подготовка истории (очистка от лишних полей)
    const cleanHistory = chatHistory.map(msg => ({ role: msg.role, content: msg.content }));

    const response = await fetch(API_URL, {
      method: 'POST', 
      headers: { 'Content-Type': 'application/json' }, 
      body: JSON.stringify({ query: query, history: cleanHistory }),
      signal: abortController.signal
    });

    if (!response.ok) throw new Error(`Server Error: ${response.status} ${response.statusText}`);

    // Чтение потока (Stream Reader)
    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) { 
      const { value, done } = await reader.read(); 
      if (done) break; 
      buffer += decoder.decode(value, { stream: true });
      buffer = buffer.replace(/\r/g, ''); // Фикс для Windows
      
      // Парсинг JSON-строк (Server-Sent Events стиль)
      let boundary = buffer.indexOf('\n');
      while (boundary !== -1) {
          const part = buffer.slice(0, boundary).trim();
          buffer = buffer.slice(boundary + 1);
          if (part) {
              try { 
                const data = JSON.parse(part); 
                
                // Обработка разных типов событий
                if (data.type === 'sources') updateDocs(botMsg, data.data?.items);
                else if (data.type === 'token') {
                   // Убираем индикатор при первом токене
                   if (data.data && !botMsg.typingRemoved) { 
                       botMsg.typing.remove(); 
                       botMsg.typingRemoved = true; 
                   }
                   botMsg.rawText += data.data || '';
                   scheduleMarkdownRender(botMsg);
                }
                else if (data.type === 'error') {
                   botMsg.rawText += `\n**Backend Error:** ${data.data}`;
                   scheduleMarkdownRender(botMsg);
                }
              } catch (e) { console.warn('JSON Parse Error', e); }
          }
          boundary = buffer.indexOf('\n');
      }
    }

    // Завершение ответа
    if (botMsg.typing && !botMsg.typingRemoved) botMsg.typing.remove();
    botMsg.answerText.innerHTML = DOMPurify.sanitize(marked.parse(botMsg.rawText));
    
    // Сохранение ответа в историю
    chatHistory.push({ role: "assistant", content: botMsg.rawText, sources: botMsg.sources });
    saveSession(savedSessions[currentSessionId].title);

  } catch (err) { 
    if (err.name === 'AbortError') {
       // Обработка ручной остановки
       if (botMsg.typing && !botMsg.typingRemoved) botMsg.typing.remove();
       botMsg.answerText.innerHTML += `<div style="opacity:0.6; margin-top:10px; font-size:0.85rem; border-top:1px solid var(--card-border); padding-top:6px;">⏹ Остановлено</div>`;
       chatHistory.push({ role: "assistant", content: botMsg.rawText, sources: botMsg.sources });
       saveSession(savedSessions[currentSessionId].title);
    } else {
       console.error(err);
       if (botMsg.typing && !botMsg.typingRemoved) botMsg.typing.remove();
       botMsg.answerText.innerHTML += `<div style="color: #ef4444; margin-top: 10px;">Ошибка: ${err.message}</div>`;
       chatHistory.pop(); // Откат истории при ошибке
    }
  } finally { 
    updateUIState(false); 
    scrollToBottom(true);
  }
}

// --- Bind Events (Привязка событий) ---

// Делегирование событий для кнопки "Новый чат"
document.addEventListener('click', function(e) {
    if(e.target && (e.target.id === 'new-chat-btn' || e.target.closest('#new-chat-btn'))) startNewChat();
});

if(actionBtn) actionBtn.addEventListener('click', () => {
  if (isLoading) { if(abortController) abortController.abort(); return; }
  const q = chatInput.value.trim(); chatInput.value = ''; sendQuery(q);
});

if(chatInput) chatInput.addEventListener('keydown', (e) => { 
  if (e.key === 'Enter') { 
    e.preventDefault(); 
    if (isLoading) return; 
    const q = chatInput.value.trim(); chatInput.value = ''; sendQuery(q); 
  } 
});


document.addEventListener('DOMContentLoaded', initSessions);
// Запуск приложения
initSessions();