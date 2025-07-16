document.addEventListener("DOMContentLoaded", function () {
    // 检查是否是从恢复操作跳转过来的
    const urlParams = new URLSearchParams(window.location.search);
    const restoredTodoId = urlParams.get('restored');
    
    if (restoredTodoId) {
        console.log(`Detected restored todo_id: ${restoredTodoId}`);
        // 自动切换到 Todo List 标签页
        const todoListTab = document.querySelector('button[data-tab="todo-list"]');
        if (todoListTab) {
            todoListTab.click();
        }
        
        // 清除URL参数
        const newUrl = window.location.pathname;
        window.history.replaceState({}, document.title, newUrl);
    }

    // ===========================
    // Dashboard 数字面板赋值逻辑
    // ===========================
    function getCurrentMonth() {
        const now = new Date();
        return ('0' + (now.getMonth() + 1)).slice(-2);
    }
    function updateDashboardData(month = null) {
        let url = '/Spirit/TodoPage/api/dashboard_data';
        if (month) {
            url += `?month=${month}`;
        }
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data && !data.error) {
                    document.getElementById("sent_todo").textContent = data.sent_todo;
                    // Update the label for the first metric
                    const sentLabelDiv = document.querySelector('#sent_todo')?.parentElement?.querySelector('div');
                    if (sentLabelDiv && sentLabelDiv.textContent.trim() === "已发出的 Todo") {
                        sentLabelDiv.textContent = "已完成的 Todo";
                    }
                    document.getElementById("unfinished_todo").textContent = data.unfinished_todo;
                    document.getElementById("overdue_todo").textContent = data.overdue_todo;
                    document.getElementById("total_todo").textContent = data.total_todo;
                }
            })
            .catch(error => console.error("Failed to fetch dashboard data", error));
    }

    updateDashboardData(getCurrentMonth());

    // Dashboard 筛选按钮逻辑
    document.querySelectorAll('.dashboard-filter-option').forEach(function (item) {
        item.addEventListener('click', function () {
            const filterMonth = this.getAttribute('data-filter');
            console.log('Dashboard filter selected month:', filterMonth);
            updateDashboardCharts(filterMonth);
        });
    });

    function updateDashboardCharts(filterMonth) {
        console.log('Updating dashboard charts with filter month:', filterMonth);
        const barFrame = document.querySelector('iframe[src*="bar_chart.html"]');
        const pieFrame = document.querySelector('iframe[src*="pie_radius.html"]');
        const lineFrame = document.querySelector('iframe[src*="line_chart.html"]');
        if (barFrame) barFrame.src = `/static/echarts/bar_chart.html?month=${filterMonth}`;
        if (pieFrame) pieFrame.src = `/static/echarts/pie_radius.html?month=${filterMonth}`;
        if (lineFrame) lineFrame.src = `/static/echarts/line_chart.html?month=${filterMonth}`;
        // 更新数字面板
        fetch(`/Spirit/TodoPage/api/dashboard_data?month=${filterMonth}`)
            .then(response => response.json())
            .then(data => {
                if (data && !data.error) {
                    document.getElementById("sent_todo").textContent = data.sent_todo;
                    const sentLabelDiv = document.querySelector('#sent_todo')?.parentElement?.querySelector('div');
                    if (sentLabelDiv && sentLabelDiv.textContent.trim() === "已发出的 Todo") {
                        sentLabelDiv.textContent = "已完成的 Todo";
                    }
                    document.getElementById("unfinished_todo").textContent = data.unfinished_todo;
                    document.getElementById("overdue_todo").textContent = data.overdue_todo;
                    document.getElementById("total_todo").textContent = data.total_todo;
                }
            })
            .catch(error => console.error("Failed to fetch dashboard data with month filter", error));
    }

    const groupFilters = {};
    // Tab 切换
    const tabBtns = document.querySelectorAll(".todo_content_button");
    const tabContents = document.querySelectorAll(".tab-contents");
    tabBtns.forEach(btn => {
        btn.addEventListener("click", function () {
            tabBtns.forEach(b => b.classList.remove("active"));
            this.classList.add("active");
            const tab = this.getAttribute("data-tab");
            tabContents.forEach(tc => {
                tc.style.display = (tc.id === "tab-" + tab) ? "" : "none";
            });
            if (tab === "dashboard") {
                updateDashboardData(getCurrentMonth());
            }
            const activeTabGroupIndex = tab.match(/\d+/) ? tab.match(/\d+/)[0] : null;
            if (activeTabGroupIndex && groupFilters[activeTabGroupIndex]) {
                const groupDiv = document.getElementById(`group-${activeTabGroupIndex}`);
                const ul = groupDiv ? groupDiv.querySelector('.todo_list_length') : null;
                if (ul) {
                    ul.querySelectorAll(".list_item").forEach(li => {
                        const status = li.getAttribute("data-status");
                        const show = (groupFilters[activeTabGroupIndex] === "all" || status === groupFilters[activeTabGroupIndex]);
                        li.classList.toggle("d-none", !show);
                    });
                }
            }
        });
    });



    // 筛选与排序
    document.querySelectorAll(".filter-option").forEach(item => {
        item.addEventListener("click", function (e) {
            e.preventDefault();
            const filterType = this.getAttribute("data-filter-type");
            const filterVal = this.getAttribute("data-filter");
            const groupIndex = this.getAttribute("data-group-index");
            groupFilters[groupIndex] = filterVal;
            console.log(`筛选 group-${groupIndex}, type=${filterType}, val=${filterVal}`);
            // 高亮当前分组下的筛选项
            document.querySelectorAll(`.filter-option[data-group-index="${groupIndex}"]`).forEach(btn => btn.classList.remove("active"));
            this.classList.add("active");

            // 修正：先定位 group，再找 ul
            const groupDiv = document.getElementById(`group-${groupIndex}`);
            const ul = groupDiv ? groupDiv.querySelector('.todo_list_length') : null;
            if (!ul) return;
            ul.querySelectorAll(".list_item").forEach(li => {
                // 没有 data-status 的 li（如"no task"），永远显示
                if (!li.hasAttribute('data-status')) {
                    li.classList.remove("d-none");
                    return;
                }
                if (filterType === "status") {
                    const status = li.getAttribute("data-status");
                    const show = (filterVal === "all" || status === filterVal);
                    if (show) {
                        li.classList.remove("d-none");
                    } else {
                        li.classList.add("d-none");
                    }
                    console.log(`li id=${li.getAttribute("data-todo-id")}, status=${status}, show=${show}`);
                } else if (filterType === "priority") {
                    const priority = li.getAttribute("data-priority");
                    const show = (filterVal === "all" || priority === filterVal);
                    if (show) {
                        li.classList.remove("d-none");
                    } else {
                        li.classList.add("d-none");
                    }
                    console.log(`li id=${li.getAttribute("data-todo-id")}, priority=${priority}, show=${show}`);
                }
            });
        });
    });

    document.querySelectorAll(".sort-option").forEach(item => {
        item.addEventListener("click", function (e) {
            e.preventDefault();
            const sortBy = this.getAttribute("data-sort");
            const groupIndex = this.getAttribute("data-group-index");
            const ul = document.querySelector(`#group-${groupIndex} .todo_list_length`);
            if (!ul) return;
            let lis = Array.from(ul.querySelectorAll(".list_item"));
            lis.sort((a, b) => {
                let aVal = a.getAttribute("data-" + sortBy) || "";
                let bVal = b.getAttribute("data-" + sortBy) || "";
                if (sortBy === "deadline" || sortBy === "start_time") {
                    let aDate = new Date(aVal);
                    let bDate = new Date(bVal);
                    return bDate - aDate;
                }
                return bVal.localeCompare(aVal);
            });
            ul.innerHTML = "";
            lis.forEach(li => ul.appendChild(li));
            if (typeof updateCountdowns === "function") updateCountdowns();
        });
    });


    // ===============================
    // Edit按钮 & 弹窗交互逻辑 (事件委托，彻底防止重复弹窗和多次请求)
    // ===============================
    let isEditModalOpen = false;
    const todoPageBase = document.getElementById("todo_page_content_base");
    if (todoPageBase) {
        todoPageBase.addEventListener("click", function (e) {
            const target = e.target.closest('.edit-todo-btn');
            if (!target) return;
            if (isEditModalOpen) return;
            isEditModalOpen = true;
            const todoId = target.getAttribute('data-todo-id');
            // 通过 API 获取 todo 详情
            fetch(`/Spirit/TodoPage/api/get_todo_info/${todoId}`)
                .then(res => {
                    if (!res.ok) {
                        throw new Error(`获取 Todo 信息失败: ${res.statusText}`);
                    }
                    return res.json();
                })
                .then(data => {
                    if (data.error) {
                        alert(`获取 Todo 信息时发生错误: ${data.error}`);
                        isEditModalOpen = false;
                        return;
                    }
                    try {
                        // 填充 home.html 中定义的模态框字段
                        document.getElementById('edit-project-id').value = data.id || '';
                        document.getElementById('edit-title').value = data.title || '';
                        document.getElementById('edit-brief').value = data.brief || '';
                        document.getElementById('edit-content').value = data.content || '';
                        document.getElementById('edit-start-time').value = data.start_time || '';
                        document.getElementById('edit-deadline').value = data.deadline || '';
                        document.getElementById('edit-completed-time').value = data.completed_time || '';
                        document.getElementById('edit-mail-notify').checked = data.mail_notify || false;

                        // 显示 home.html 中定义的模态框
                        const modal = new bootstrap.Modal(document.getElementById('editProjectModal'));
                        modal.show();
                        // 监听关闭事件，重置标志
                        document.getElementById('editProjectModal').addEventListener('hidden.bs.modal', function handler() {
                            isEditModalOpen = false;
                            document.getElementById('editProjectModal').removeEventListener('hidden.bs.modal', handler);
                        });
                    } catch (domError) {
                        console.error('DOM 操作或模态框显示时发生错误:', domError);
                        alert('更新界面时发生错误：' + domError.message);
                        isEditModalOpen = false;
                        return;
                    }
                })
                .catch(error => {
                    console.error('获取 Todo 信息时发生网络错误或解析错误:', error);
                    alert('获取 Todo 信息时发生网络错误或解析错误。');
                    isEditModalOpen = false;
                });
        });
    }

    // Todo 完成勾选与反勾选自动提交
    document.querySelectorAll('.todo-complete-checkbox').forEach(cb => {
        cb.addEventListener('change', function () {
            const todoId = this.getAttribute('data-todo-id');
            const originStatus = parseInt(this.getAttribute('data-status'));
            const originPriority = parseInt(this.getAttribute('data-priority'));
            // 界面元素
            const listItem = this.closest('.list_item');
            const badge = listItem.querySelector('.todo-status-badge');
            const title = listItem.querySelector('.todo-title');
            // 勾选：设为完成
            if (this.checked) {
                fetch(`/Spirit/TodoPage/edit/${todoId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        status: 2,
                        priority: 0,
                        completed_time: new Date().toISOString().slice(0, 19).replace('T', ' ')
                    })
                })
                    .then(res => res.json())
                    .then(data => {
                        if (data.success) {
                            document.querySelectorAll(`.todo-complete-checkbox[data-todo-id="${todoId}"]`).forEach(cb2 => {
                                cb2.checked = true;
                                cb2.setAttribute('data-status', 2);
                                cb2.setAttribute('data-priority', 0);

                                const li2 = cb2.closest('.list_item');
                                li2.setAttribute('data-status', 2);
                                li2.setAttribute('data-priority', 0);

                                const badge2 = li2.querySelector('.todo-status-badge');
                                const title2 = li2.querySelector('.todo-title');
                                if (badge2) {
                                    badge2.className = "badge status-badge bg-primary text-light todo-status-badge";
                                    badge2.textContent = "Completed";
                                }
                                if (title2) {
                                    title2.classList.add("text-muted", "text-decoration-line-through");
                                }
                            });
                            updateBadges();
                            updateCountdowns();
                        } else {
                            alert(data.error || "Failed to complete todo");
                            this.checked = false;
                        }
                    });
            } else {
                // 取消勾选：恢复原状态
                fetch(`/Spirit/TodoPage/edit/${todoId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        status: (originStatus === 2 ? 1 : originStatus),
                        priority: (originPriority === 0 ? 1 : originPriority),
                        completed_time: null
                    })
                })
                    .then(res => res.json())
                    .then(data => {
                        if (data.success) {
                            document.querySelectorAll(`.todo-complete-checkbox[data-todo-id="${todoId}"]`).forEach(cb2 => {
                                cb2.checked = false;
                                cb2.setAttribute('data-status', (originStatus === 2 ? 1 : originStatus));
                                cb2.setAttribute('data-priority', (originPriority === 0 ? 1 : originPriority));

                                const li2 = cb2.closest('.list_item');
                                li2.setAttribute('data-status', (originStatus === 2 ? 1 : originStatus));
                                li2.setAttribute('data-priority', (originPriority === 0 ? 1 : originPriority));

                                const badge2 = li2.querySelector('.todo-status-badge');
                                const title2 = li2.querySelector('.todo-title');
                                if (badge2) {
                                    badge2.className = "badge status-badge bg-success todo-status-badge";
                                    badge2.textContent = "Time-sensitive";
                                }
                                if (title2) {
                                    title2.classList.remove("text-muted", "text-decoration-line-through");
                                }
                            });
                            updateBadges();
                            updateCountdowns();
                        } else {
                            alert(data.error || "Failed to revert todo");
                            this.checked = true;
                        }
                    });
            }
        });
    });

    // ===========================
    // 倒计时显示逻辑
    // ===========================
    function updateCountdowns() {
        document.querySelectorAll('.list_item[data-deadline-timestamp]').forEach(li => {
            const span = li.querySelector('.countdown');
            if (!span) return;
            const ddlTs = parseInt(li.getAttribute('data-deadline-timestamp'));
            if (!ddlTs) return;
            const now = Math.floor(Date.now() / 1000);
            let left = ddlTs - now;
            if (left < 0) {
                span.textContent = "Overdue";
                span.style.color = "red";
            } else {
                const d = Math.floor(left / 86400);
                const h = Math.floor((left % 86400) / 3600);
                const m = Math.floor((left % 3600) / 60);
                const s = left % 60;
                span.textContent = `${d > 0 ? d + 'd ' : ''}${(h > 0 || d > 0) ? h + 'h ' : ''}${(m > 0 || h > 0 || d > 0) ? m + 'm ' : ''}${s}s`;
                span.style.color = "#888";
            }
        });
    }
    setInterval(updateCountdowns, 1000);
    updateCountdowns();

    function updateBadges() {
        document.querySelectorAll('.list_item').forEach(item => {
            const badge = item.querySelector('.status-badge, .todo-status-badge');
            const status = parseInt(item.getAttribute('data-status'));
            const priority = parseInt(item.getAttribute('data-priority'));
            if (badge) {
                if (status === 2) {
                    badge.className = "badge status-badge bg-primary text-light todo-status-badge";
                    badge.textContent = "Completed";
                } else if (status === 3) {
                    badge.className = "badge status-badge bg-secondary text-light todo-status-badge";
                    badge.textContent = "Overdue";
                } else if (priority === 3) {
                    badge.className = "badge status-badge bg-danger todo-status-badge";
                    badge.textContent = "Urgent";
                } else if (priority === 2) {
                    badge.className = "badge status-badge bg-warning text-dark todo-status-badge";
                    badge.textContent = "Important";
                } else if (priority === 1) {
                    badge.className = "badge status-badge bg-success todo-status-badge";
                    badge.textContent = "Time-sensitive";
                } else if (priority === 0) {
                    badge.className = "badge status-badge bg-info text-dark todo-status-badge";
                    badge.textContent = "Non-urgent";
                }
            }
            const title = item.querySelector('.todo-title');
            if (title) {
                if (status === 2) {
                    title.classList.add("text-muted", "text-decoration-line-through");
                } else {
                    title.classList.remove("text-muted", "text-decoration-line-through");
                }
            }
        });
    }
    // ===========================
    // Trash tab loading logic
    // ===========================
    if (document.getElementById("trash_list")) {
        try {
            loadTrashData();
        } catch (e) {
            console.error("Error auto-refreshing trash:", e);
        }
    }

    function loadTrashData() {
        fetch('/Spirit/TodoPage/api/trash_data')
            .then(response => response.json())
            .then(data => {
                const trashListDiv = document.getElementById("trash_list");
                if (!trashListDiv) {
                    console.error("Element with id=trash_list not found, cannot render trash content!");
                    return;
                }
                trashListDiv.innerHTML = "";
                if (data && Array.isArray(data) && data.length > 0) {
                    data.forEach(todo => {
                        const item = document.createElement("li");
                        item.className = "d-flex justify-content-between align-items-center list_item py-3 px-3";
                        item.setAttribute("data-todo-id", todo.id);
                        // 计算倒计时
                        let deadlineText = '';
                        let isOverdue = false;
                        if (todo.deadline_ts) {
                            const now = Math.floor(Date.now() / 1000);
                            let left = todo.deadline_ts - now;
                            if (left < 0) {
                                deadlineText = '<span style="color:red;font-weight:bold;">Overdue</span>';
                                isOverdue = true;
                            } else {
                                const d = Math.floor(left / 86400);
                                const h = Math.floor((left % 86400) / 3600);
                                const m = Math.floor((left % 3600) / 60);
                                const s = left % 60;
                                deadlineText = `${d > 0 ? d + 'd ' : ''}${(h > 0 || d > 0) ? h + 'h ' : ''}${(m > 0 || h > 0 || d > 0) ? m + 'm ' : ''}${s}s`;
                            }
                        }
                        // SVG 示例（可根据实际需求替换）
                        const calendarSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-calendar" viewBox="0 0 16 16"><path d="M3.5 0a.5.5 0 0 1 .5.5V1h8V.5a.5.5 0 0 1 1 0V1h1.5A1.5 1.5 0 0 1 16 2.5V4H0V2.5A1.5 1.5 0 0 1 1.5 1H3V.5a.5.5 0 0 1 .5-.5zM16 14V5H0v9a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2z"></path></svg>`;
                        const clockSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-stopwatch" viewBox="0 0 16 16"><path d="M6.5 0a.5.5 0 0 1 .5.5V1h2V.5a.5.5 0 0 1 1 0V1h.5A2.5 2.5 0 0 1 13 3.5v.54A6.972 6.972 0 0 1 8 2a6.972 6.972 0 0 1-5 2.04V3.5A2.5 2.5 0 0 1 5.5 1H6V.5a.5.5 0 0 1 .5-.5zM8 4a5 5 0 1 1-4.546 2.914.5.5 0 1 1 .912-.408A4 4 0 1 0 8 5a.5.5 0 0 1 0 1z"/></svg>`;
                        item.innerHTML = `
                            <div class="d-flex align-items-center gap-3">
                                <div class="d-flex flex-column">
                                    <div class="fw-bold">${todo.title}${todo.brief ? ' : ' + todo.brief : ''}</div>
                                    <div class="text-muted small mt-1 d-flex align-items-center gap-2">
                                        <span style="margin: 1vh 0">Deletion Time: ${todo.deleted_time || ''}</span>
                                        <span>·</span>
                                        <span>${clockSvg} ${deadlineText}</span>
                                    </div>
                                </div>
                            </div>
                            <div class="d-flex align-items-center gap-2">
                                <button class="d-flex btn btn-sm btn-info restore-btn align-items-center" data-id="${todo.id}" title="恢复">Recover <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="size-6"><path fill-rule="evenodd" d="M4.755 10.059a7.5 7.5 0 0 1 12.548-3.364l1.903 1.903h-3.183a.75.75 0 1 0 0 1.5h4.992a.75.75 0 0 0 .75-.75V4.356a.75.75 0 0 0-1.5 0v3.18l-1.9-1.9A9 9 0 0 0 3.306 9.67a.75.75 0 1 0 1.45.388Zm15.408 3.352a.75.75 0 0 0-.919.53 7.5 7.5 0 0 1-12.548 3.364l-1.902-1.903h3.183a.75.75 0 0 0 0-1.5H2.984a.75.75 0 0 0-.75.75v4.992a.75.75 0 0 0 1.5 0v-3.18l1.9 1.9a9 9 0 0 0 15.059-4.035.75.75 0 0 0-.53-.918Z" clip-rule="evenodd"></path></svg></button>
                                <button class="d-flex btn btn-sm btn-danger delete-btn align-items-center" data-id="${todo.id}" title="彻底删除">Delete completely <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="size-6"><path fill-rule="evenodd" d="M5.47 5.47a.75.75 0 0 1 1.06 0L12 10.94l5.47-5.47a.75.75 0 1 1 1.06 1.06L13.06 12l5.47 5.47a.75.75 0 1 1-1.06 1.06L12 13.06l-5.47 5.47a.75.75 0 0 1-1.06-1.06L10.94 12 5.47 6.53a.75.75 0 0 1 0-1.06Z" clip-rule="evenodd"></path></svg></button>
                            </div>
                        `;
                        trashListDiv.appendChild(item);
                    });
                    // 绑定彻底删除事件
                    trashListDiv.querySelectorAll('.delete-btn').forEach(btn => {
                        btn.addEventListener('click', function () {
                            const todoId = this.getAttribute('data-id');
                            if (confirm("Are you sure to permanently delete this task? This action cannot be undone!")) {
                                fetch(`/Spirit/TodoPage/api/permanent_delete/${todoId}`, { method: "POST" })
                                    .then(response => response.json())
                                    .then(result => {
                                        if (result.success) {
                                            loadTrashData();
                                        } else {
                                            alert("Delete failed");
                                        }
                                    });
                            }
                        });
                    });
                    // 绑定恢复事件
                    trashListDiv.querySelectorAll('.restore-btn').forEach(btn => {
                        btn.addEventListener('click', function() {
                            const todoId = this.getAttribute('data-id');
                            if (confirm("Are you sure to restore this task?")) {
                                fetch(`/Spirit/TodoPage/api/restore/${todoId}`, {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json',
                                        'X-Requested-With': 'XMLHttpRequest'
                                    }
                                })
                                .then(response => {
                                    if (response.ok) {
                                        alert("Task restored successfully");
                                        // 跳转到 Todo List 页面并添加时间戳参数确保刷新
                                        const timestamp = new Date().getTime();
                                        window.location.href = `/Spirit/TodoPage/Todo?restored=${todoId}&t=${timestamp}`;
                                    } else {
                                        alert("Restore failed");
                                    }
                                })
                                .catch(error => {
                                    console.error('Error restoring task:', error);
                                    alert("Error occurred while restoring");
                                });
                            }
                        });
                    });
                } else {
                    trashListDiv.innerHTML = '<li class="list-group-item text-center text-muted">No tasks in trash,please click the refresh button above.</li>';
                    console.warn("/api/trash_data returned empty, no tasks in trash.");
                }
            })
            .catch(err => {
                console.error("Error loading trash data:", err);
            });
    }

    // Hook Trash tab button click to loadTrashData
    document.querySelector('button[data-tab="logs"]')?.addEventListener("click", loadTrashData);

    window.loadTrashData = loadTrashData;

    // 绑定删除按钮事件
    document.querySelectorAll('.delete-todo-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const todoId = this.getAttribute('data-todo-id');
            
            if (!todoId) {
                console.error('未找到任务ID');
                return;
            }
            
            if (confirm("Are you sure to delete this task? It can be recovered from the trash.")) {
                fetch(`/Spirit/TodoPage/delete/${todoId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => {
                    if (response.ok) {
                        alert("Task moved to trash");
                        // 刷新页面以显示最新状态
                        location.reload();
                    } else {
                        alert("Delete failed");
                    }
                })
                .catch(error => {
                    console.error('Error deleting task:', error);
                    alert("Error occurred while deleting");
                });
            }
        });
    });

    // 绑定回收站中的永久删除按钮事件
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const todoId = this.getAttribute('data-id');
            if (confirm("Are you sure to permanently delete this task? This action cannot be undone!")) {
                fetch(`/Spirit/TodoPage/api/permanent_delete/${todoId}`, { method: "POST" })
                    .then(response => response.json())
                    .then(result => {
                        if (result.success) {
                            loadTrashData();
                        } else {
                            alert("Delete failed");
                        }
                    });
            }
        });
    });

    // 绑定编辑项目提交按钮逻辑（确保在 todo 页面也能正常工作）
    const oldBtn = document.getElementById("edit-project-submit");
    if (oldBtn) {
        const newBtn = oldBtn.cloneNode(true);
        oldBtn.replaceWith(newBtn);
        const boundBtn = document.getElementById("edit-project-submit"); // 再次获取替换后的按钮引用
        boundBtn.addEventListener("click", function (e) {
            e.preventDefault(); // 阻止表单默认提交
            fetch("/Spirit/Project/api/edit", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest"
                },
                body: JSON.stringify({
                    id: document.getElementById("edit-project-id").value,
                    title: document.getElementById("edit-title").value,
                    brief: document.getElementById("edit-brief").value,
                    content: document.getElementById("edit-content").value,
                    start_time: document.getElementById("edit-start-time").value ? document.getElementById("edit-start-time").value + "T00:00" : null,
                    deadline: document.getElementById("edit-deadline").value ? document.getElementById("edit-deadline").value + "T00:00" : null,
                    completed_time: document.getElementById("edit-completed-time").value ? document.getElementById("edit-completed-time").value + "T00:00" : null,
                    mail_notify: document.getElementById("edit-mail-notify").checked
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert("Project updated successfully!");
                    location.reload();
                } else {
                    alert("Update failed: " + (data.error || "Unknown error"));
                }
            })
            .catch(err => {
                console.error("Request error:", err);
                alert("Network error while editing project.");
            });
        });
    }
});
// ===========================
// 新建项目表单校验逻辑
// ===========================
document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("newProjectForm");
    if (form) {
        console.log("✅ JS 校验逻辑运行了！");
        form.addEventListener("submit", function (e) {
            const startInput = document.getElementById("start_time");
            const deadlineInput = document.getElementById("deadline");
            const completedInput = document.getElementById("completed_time");

            if (!startInput) return;

            const startTime = new Date(startInput.value);

            if (deadlineInput && deadlineInput.value) {
                const deadline = new Date(deadlineInput.value);
                if (startTime > deadline) {
                    alert("Start time must be earlier than deadline.");
                    e.preventDefault();
                    return;
                }
            }

            if (completedInput && completedInput.value) {
                const completed = new Date(completedInput.value);
                if (startTime > completed) {
                    alert("Start time must be earlier than completed time.");
                    e.preventDefault();
                    return;
                }
            }
        });
    }
});