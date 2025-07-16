document.addEventListener("DOMContentLoaded", function () {
    // 回填搜索关键词
    const searchInput = document.getElementById("search");
    if (searchInput) {
        const urlParams = new URLSearchParams(window.location.search);
        const keyword = urlParams.get("search") || urlParams.get("keyword");
        if (keyword) {
            searchInput.value = keyword;
        }
    }

    // 保存原始的li元素
    const todoList = document.getElementById("todoList-search");
    const originalItems = todoList ? Array.from(todoList.children) : [];

    // 1. 编辑按钮逻辑：打开模态框并回填表单字段
    document.querySelectorAll('.edit-project-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const todoId = this.dataset.projectId;
            fetch(`/Spirit/api/get_todo_info/${todoId}`)
                .then(res => res.json())
                .then(data => {
                    document.getElementById("project-id").value = data.id || "";
                    document.getElementById("edit-title").value = data.title || "";
                    document.getElementById("edit-brief").value = data.brief || "";
                    document.getElementById("edit-content").value = data.content || "";
                    document.getElementById("edit-deadline").value = data.deadline || "";
                    document.getElementById("edit-start-time").value = data.start_time || "";
                    document.getElementById("edit-completion-time").value = data.completed_time || "";
                    document.getElementById("edit-mail-notify").checked = !!data.mail_notify;
                    document.getElementById("edit-important").checked = !!data.important;
                });
        });
    });

    // 2. 编辑表单提交逻辑
    const editForm = document.getElementById("editTodoForm");
    if (editForm) {
        editForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const todoId = document.getElementById("editTodoId").value;
            const payload = {
                title: document.getElementById("editTodoTitle").value,
                content: document.getElementById("editTodoContent").value,
                deadline: document.getElementById("editTodoDeadline").value,
                priority: document.getElementById("editTodoPriority").value,
            };

            fetch(`/Spirit/edit/${todoId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(res => {
                if (res.ok) {
                    location.reload();
                } else {
                    alert("Failed to update todo.");
                }
            });
        });
    }

    // 3. 删除按钮逻辑
    document.querySelectorAll('.delete-project-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const todoId = this.dataset.projectId;
            if (!confirm("确定要删除这个任务吗？删除后可在回收站恢复。")) return;
            fetch(`/Spirit/delete/${todoId}`, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            }).then(res => res.json())
            .then(data => {
                if (data.success) {
                    // 可选：移除该项，或刷新页面
                    location.reload();
                } else {
                    alert(data.error || "删除失败");
                }
            });
        });
    });

    function applyFilters() {
        if (!todoList) return;
        // 获取当前选中的筛选和排序
        const filter = document.querySelector('.filter-option.active')?.dataset.filter;
        const sortKey = document.querySelector('.sort-option.active')?.dataset.sort;

        let items = [...originalItems];

        if (filter && filter !== "all") {
            items = items.filter(li => {
                const status = li.querySelector(".badge")?.textContent.toLowerCase();
                if (filter === "completed") return status === "completed";
                if (filter === "pending") return status === "not started" || status === "in progress";
                return true;
            });
        }

        if (sortKey) {
            items.sort((a, b) => {
                // 可扩展：li中需有[data-sort-key]的元素
                const getText = (el, key) => el.querySelector(`[data-sort-key="${key}"]`)?.textContent || "";
                const aText = getText(a, sortKey).toLowerCase();
                const bText = getText(b, sortKey).toLowerCase();
                return aText.localeCompare(bText);
            });
        }

        todoList.innerHTML = "";
        items.forEach(item => todoList.appendChild(item));
    }

    // 绑定筛选点击事件
    document.querySelectorAll('.filter-option').forEach(btn => {
        btn.addEventListener("click", function () {
            document.querySelectorAll('.filter-option').forEach(b => b.classList.remove("active"));
            this.classList.add("active");
            applyFilters();
        });
    });

    // 绑定排序点击事件
    document.querySelectorAll('.sort-option').forEach(btn => {
        btn.addEventListener("click", function () {
            document.querySelectorAll('.sort-option').forEach(b => b.classList.remove("active"));
            this.classList.add("active");
            applyFilters();
        });
    });
    // 初始化倒计时显示
    function updateCountdowns() {
        const countdownElements = document.querySelectorAll('[data-deadline]');
        countdownElements.forEach(el => {
            el.classList.remove("text-danger");
            const deadlineStr = el.dataset.deadline;
            const deadline = new Date(deadlineStr);
            const now = new Date();
            const diffMs = deadline - now;

            if (isNaN(deadline.getTime())) {
                el.textContent = 'Invalid deadline';
                return;
            }

            if (diffMs <= 0) {
                el.textContent = 'Time Out';
                el.classList.add("text-danger");
                el.style.color = 'red';
                return;
            }

            const totalSeconds = Math.floor(diffMs / 1000);
            const days = Math.floor(totalSeconds / (3600 * 24));
            const hours = Math.floor((totalSeconds % (3600 * 24)) / 3600);
            const minutes = Math.floor((totalSeconds % 3600) / 60);

            if (days > 0) {
                el.textContent = `${days}d ${hours}h ${minutes}m left`;
            } else if (hours > 0) {
                el.textContent = `${hours}h ${minutes}m left`;
            } else {
                el.textContent = `${minutes}m left`;
            }
        });
    }

    // 初始调用 + 定时刷新
    updateCountdowns();
    setInterval(updateCountdowns, 60000); // 每分钟刷新一次
});
