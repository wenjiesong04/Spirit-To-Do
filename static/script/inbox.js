document.addEventListener("DOMContentLoaded", function () {
    const inboxListContainer = document.querySelector("#inbox-list");
    const inboxClearBtn = document.querySelector("#inbox-clear-btn");

    if (!inboxListContainer || !inboxClearBtn) return;

    function fetchNotifications() {
        fetch("/Spirit/In-Box/api/notifications")
            .then(response => response.json())
            .then(data => {
                inboxListContainer.innerHTML = "";
                if (!data.notifications || data.notifications.length === 0) {
                    inboxListContainer.innerHTML = `<div class="text-muted py-4 text-center">No notifications.</div>`;
                    return;
                }
                data.notifications.forEach(item => {
                    const div = document.createElement("div");
                    div.className = "inbox-item border-bottom py-2 px-3";
                    div.innerHTML = `
                        <div class="fw-semibold text-light">${item.content}</div>
                        <div class="text-secondary small">${item.created_time}</div>
                    `;
                    inboxListContainer.appendChild(div);
                });
            });
    }

    inboxClearBtn.addEventListener("click", () => {
        fetch("/Spirit/In-Box/api/notifications/clear", { method: "POST" })
            .then(response => response.json())
            .then(() => fetchNotifications());
    });

    fetchNotifications();
});
