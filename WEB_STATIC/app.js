async function fetchState() {
  try {
    const res = await fetch('/api/state');
    const data = await res.json();
    updateDistance(data.distance);
    updateApiLog(data.api_log);
    updateSchedule(data.schedule);
    updateServerLog(data.logs);
  } catch (e) {
    console.error('State fetch error', e);
  }
}

function updateDistance(d) {
  if (!d) return;
  const el = document.getElementById('distance-value');
  el.textContent = d.current_distance.toFixed(2) + 'px';
}

function updateApiLog(list) {
  const ul = document.getElementById('api-log');
  ul.innerHTML = '';
  list.slice().reverse().forEach(item => {
    const li = document.createElement('li');
    li.textContent = `/api/${item.endpoint} - ${item.status}`;
    ul.appendChild(li);
  });
}

function updateSchedule(list) {
  const ul = document.getElementById('schedule-list');
  ul.innerHTML = '';
  list.forEach(item => {
    const li = document.createElement('li');
    if (typeof item === 'string') {
      li.textContent = item;
    } else {
      li.textContent = `${item.이름 || item.name} - ${item.시간 || ''}`;
    }
    ul.appendChild(li);
  });
}

function updateServerLog(list) {
  const ul = document.getElementById('log-list');
  ul.innerHTML = '';
  list.slice().reverse().forEach(msg => {
    const li = document.createElement('li');
    li.textContent = msg;
    ul.appendChild(li);
  });
}

fetchState();
setInterval(fetchState, 2000);

