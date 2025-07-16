// 全局定义 needUpdateStats
let needUpdateStats = false;

// ===========================
// Project Edit/Delete/Countdown 事件绑定统一函数
function bindEditProjectEvents() {
    // Edit Project 按钮
    document.querySelectorAll('.edit_project_button').forEach(function (btn) {
        btn.removeEventListener('_editProjectHandler', btn._editProjectHandler || (() => {}));
        // 事件处理函数
        btn._editProjectHandler = function () {
            const projectTitle = this.getAttribute('data-project-title');
            const projectId = this.getAttribute('data-project-id');

            // 填入模态框，判空
            let elem = document.getElementById('edit-title');
            if (elem) elem.value = projectTitle;
            elem = document.getElementById('edit-project-id');
            if (elem) elem.value = projectId;

            // 弹出模态框
            var modal = new bootstrap.Modal(document.getElementById('editProjectModal'));
            modal.show();
        };
        btn.addEventListener('click', btn._editProjectHandler);
    });

    // Delete Project 按钮
    document.querySelectorAll('.delete-project-btn').forEach(function (btn) {
        btn.removeEventListener('_deleteProjectHandler', btn._deleteProjectHandler || (() => {}));
        btn._deleteProjectHandler = function () {
            const projectId = this.getAttribute('data-project-id');
            if (!projectId) {
                console.error('未找到项目ID');
                return;
            }
            
            if (confirm("Are you sure to delete this project? It can be recovered from the trash.")) {
                fetch(`/Spirit/TodoPage/delete/${projectId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Delete request failed');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        alert("Project moved to trash");
                        // 刷新页面以显示最新状态
                        location.reload();
                    } else {
                        throw new Error(data.error || 'Delete failed');
                    }
                })
                .catch(error => {
                    console.error('Error deleting project:', error);
                    alert(error.message || "Error occurred while deleting");
                });
            }
        };
        btn.addEventListener('click', btn._deleteProjectHandler);
    });
}

// Project 编辑按钮（.edit-project-btn）统一事件绑定
function bindEditProjectBtnApiEvents() {
    document.querySelectorAll('.edit-project-btn').forEach(button => {
        button.removeEventListener('_editProjectApiHandler', button._editProjectApiHandler || (() => {}));
        button._editProjectApiHandler = function () {
            const projectId = this.getAttribute('data-project-id');
            fetch(`/Spirit/TodoPage/api/get_todo_info/${projectId}`)
                .then(res => res.json())
                .then(data => {
                    if (data.error) {
                        console.error("Todo not found");
                        return;
                    }
                    // 填充表单字段，判空
                    let elem = document.getElementById('edit-project-id');
                    if (elem) elem.value = data.id || "";
                    elem = document.getElementById('edit-title');
                    if (elem) elem.value = data.title || "";
                    elem = document.getElementById('edit-brief');
                    if (elem) elem.value = data.brief || "";
                    elem = document.getElementById('edit-content');
                    if (elem) elem.value = data.content || "";
                    elem = document.getElementById('edit-start-time');
                    if (elem) elem.value = data.start_time || "";
                    elem = document.getElementById('edit-deadline');
                    if (elem) elem.value = data.deadline || "";
                    elem = document.getElementById('edit-completed-time');
                    if (elem) elem.value = data.completed_time || "";
                    elem = document.getElementById('edit-mail-notify');
                    if (elem) elem.checked = data.mail_notify || false;
                    elem = document.getElementById('edit-important');
                    if (elem) elem.checked = data.important || false;
                })
                .catch(error => console.error("Fetch failed", error));
        };
        button.addEventListener('click', button._editProjectApiHandler);
    });
}

// Countdown Timer
function updateProjectCountdown() {
    const countdownEls = document.querySelectorAll('.countdown');
    countdownEls.forEach(function (el) {
        const deadlineStr = el.getAttribute('data-deadline');
        const deadlineDate = new Date(deadlineStr + 'T23:59:59');
        const now = new Date();

        const diff = deadlineDate - now;
        if (diff <= 0) {
            el.textContent = 'Overdue';
            el.style.color = 'red';
        } else {
            const days = Math.floor(diff / (1000 * 60 * 60 * 24));
            const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
            const minutes = Math.floor((diff / (1000 * 60)) % 60);
            el.textContent = `${days}d ${hours}h ${minutes}m`;
        }
    });
}

document.addEventListener("DOMContentLoaded", function () {

    console.log("✅ DOM 已加载，开始初始化统计");
    let currentRange = "today";
    // DOMContentLoaded 内初始化
    // let needUpdateStats = false;

    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl)
    })

    function updateClock() {
        const now = new Date();
        const formatted = now.toLocaleString(); // 显示日期 + 时间（含时分秒）
        const dateElement = document.getElementById("date");
        if (dateElement) {
            dateElement.textContent = formatted;
        }
    }
    updateClock();
    setInterval(updateClock, 1000);

    // 设置日期和问候语
    const now = new Date();
    const hour = now.getHours();
    let greeting = "";

    if (hour >= 21 || hour < 5) {
        greeting = "Good Night";
    } else if (hour >= 18) {
        greeting = "Good Evening";
    } else if (hour >= 13) {
        greeting = "Good Afternoon";
    } else if (hour >= 11) {
        greeting = "Good Noon";
    } else {
        greeting = "Good Morning";
    }
    
    const greetingElement = document.getElementById("greeting");
    if (greetingElement) {
        greetingElement.textContent = greeting;
    }

    const dropdownButton = document.getElementById("dropdown_button");
    const dropdownItems = document.querySelectorAll(".time_option");

    dropdownItems.forEach(item => {
        item.addEventListener("click", function (e) {
            e.preventDefault();
            const selectedText = this.textContent.trim();
            if (dropdownButton) dropdownButton.textContent = selectedText;
            const selectedRange = this.dataset.value;
            currentRange = selectedRange;
            updateTodoCounts(selectedRange);
        });
    });

    function updateTodoCounts(range) {
        const todos = document.querySelectorAll(".todo_item");
        let completed = 0;
        let inProgress = 0;
        let overdue = 0;
        let preparation = 0;

        todos.forEach(todo => {
            const status = parseInt(todo.dataset.status);
            const priority = parseInt(todo.dataset.priority);
            const isCompleted = todo.dataset.completed === "1";
            let inRange = false;

            switch (range) {
                case "today":
                    inRange = todo.dataset.today === "1";
                    break;
                case "yesterday":
                    inRange = todo.dataset.yesterday === "1";
                    break;
                case "this_week":
                    inRange = todo.dataset.thisWeek === "1";
                    break;
                case "this_month":
                    inRange = todo.dataset.thisMonth === "1";
                    break;
                case "this_year":
                    inRange = todo.dataset.thisYear === "1";
                    break;
                case "all":
                default:
                    inRange = true;
            }

            if (inRange) {
                if (isCompleted) completed++;
                else if (status === 1) inProgress++;
                else if (status === 3) overdue++;
                else if (priority === 0) preparation++;
            }
        });

        const doneCountElement = document.getElementById("todo_done_count");
        if (doneCountElement) doneCountElement.textContent = completed;

        const doingCountElement = document.getElementById("todo_doing_count");
        if (doingCountElement) doingCountElement.textContent = inProgress;

        const overdueCountElement = document.getElementById("todo_overdue_count");
        if (overdueCountElement) overdueCountElement.textContent = overdue;

        const preparationCountElement = document.getElementById("todo_preparation_count");
        if (preparationCountElement) preparationCountElement.textContent = preparation;
    }

    // 默认初始化统计
    const todos = document.querySelectorAll(".todo_item");
    if (todos.length > 0) {
        updateTodoCounts("today");
    }

    // 设置第一个 todo_option_button 默认选中
    const optionButtons = document.querySelectorAll(".todo_option_button");
    if (optionButtons.length > 0) {
        optionButtons.forEach(btn => btn.classList.remove("active")); // 清除所有按钮的 active 状态
        optionButtons[0].classList.add("active"); // 默认第一个按钮选中

        // 为 todo_option_button 添加点击事件监听以切换 active 状态
        optionButtons.forEach(btn => {
            btn.addEventListener("click", function () {
                optionButtons.forEach(b => b.classList.remove("active"));
                this.classList.add("active");

                const selectedFilter = this.dataset.filter;
                const filterType = this.dataset.filterType || "status"; // 默认按状态筛选

                // 只筛选 block_todo 里的 todo_item
                const localTodos = document.querySelectorAll("#block_todo .todo_item");

                localTodos.forEach(todo => {
                    const status = parseInt(todo.dataset.status);
                    const priority = parseInt(todo.dataset.priority);

                    // Preparation 按钮：只显示优先级为0
                    if (filterType === "priority" && selectedFilter === "0") {
                        todo.style.display = (priority === 0) ? "block" : "none";
                    }
                    // In Progress：只显示 status==1 且 priority!=0
                    else if (selectedFilter === "1") {
                        todo.style.display = (status === 1 && priority !== 0) ? "block" : "none";
                    }
                    // 其他按钮正常筛选
                    else if (selectedFilter === "all" || status === parseInt(selectedFilter)) {
                        todo.style.display = "block";
                    } else {
                        todo.style.display = "none";
                    }
                });
            });
        });
    }

    // 保存原始HTML片段
    window.blockProjectsHTML = document.querySelector('.block_todo[data-block="projects"]')?.outerHTML;
    window.blockFriendsHTML = document.querySelector('.block_todo[data-block="friends"]')?.outerHTML;
    // 关闭按钮逻辑
    document.querySelectorAll('.close_block[data-block]').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const blockType = btn.getAttribute('data-block');
            const block = btn.closest('.block_todo');
            if (block) {
                block.parentNode.removeChild(block);
                // 可选: 调用后端同步 remove_block
            }
        });
    });
    // Add Blocks 按钮弹窗
    const addBlocksBtn = document.getElementById('add_blocks');
    if (addBlocksBtn) {
        addBlocksBtn.addEventListener('click', function() {
            // 进入弹窗前标记需要更新统计
            needUpdateStats = true;
            const allBlocks = [
                {type: 'projects', name: 'My Projects'},
                {type: 'friends', name: 'Friends'}
            ];

            // 实时获取当前存在的 block
            const presentBlocks = Array.from(document.querySelectorAll('.block_todo[data-block]'))
                .map(b => b.getAttribute('data-block'));

            // 仅可添加未 present 的 block
            const canAddBlocks = allBlocks.filter(b => !presentBlocks.includes(b.type));

            const optionsDiv = document.getElementById('add-blocks-options');
            if (optionsDiv) optionsDiv.innerHTML = '';

            if (canAddBlocks.length === 0) {
                if (optionsDiv) optionsDiv.innerHTML = '<p>所有模块都已添加。</p>';
                const confirmBtn = document.getElementById('add-blocks-confirm');
                if (confirmBtn) confirmBtn.disabled = true;
            } else {
                canAddBlocks.forEach(b => {
                    if (optionsDiv) optionsDiv.innerHTML += `
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" value="${b.type}" id="add-block-${b.type}">
                            <label class="form-check-label" for="add-block-${b.type}">${b.name}</label>
                        </div>
                    `;
                });
                const confirmBtn = document.getElementById('add-blocks-confirm');
                if (confirmBtn) confirmBtn.disabled = false;
            }

            var modal = new bootstrap.Modal(document.getElementById('addBlocksModal'));
            modal.show();
        });
    }
    // 添加按钮逻辑
    const addBlocksConfirm = document.getElementById('add-blocks-confirm');
    if (addBlocksConfirm) {
        addBlocksConfirm.addEventListener('click', function() {
            const checked = Array.from(document.querySelectorAll('#add-blocks-options input[type=checkbox]:checked')).map(i => i.value);
            checked.forEach(type => {
                if (type === 'projects' && window.blockProjectsHTML) {
                    document.querySelector('.left_blocks').insertAdjacentHTML('afterbegin', window.blockProjectsHTML);
                }
                if (type === 'friends' && window.blockFriendsHTML) {
                    const after = document.querySelector('.block_todo[data-block="projects"]');
                    if (after) {
                        after.insertAdjacentHTML('afterend', window.blockFriendsHTML);
                    } else {
                        document.querySelector('.left_blocks').insertAdjacentHTML('afterbegin', window.blockFriendsHTML);
                    }
                }
            });
            // 重新绑定关闭按钮事件和项目编辑按钮事件（100ms后以确保插入）
            setTimeout(() => {
                document.querySelectorAll('.close_block[data-block]').forEach(function(btn) {
                    btn.onclick = function() {
                        const blockType = btn.getAttribute('data-block');
                        const block = btn.closest('.block_todo');
                        if (block) {
                            block.parentNode.removeChild(block);
                            // 可选: 调用后端同步 remove_block
                        }
                    }
                });
                bindEditProjectEvents();
                bindEditProjectBtnApiEvents();
            }, 100);
            // 在关闭弹窗前标记需要统计更新
            needUpdateStats = true;
            var modal = bootstrap.Modal.getInstance(document.getElementById('addBlocksModal'));
            if (modal) modal.hide();
        });
    }

    // 选项卡按钮逻辑（含统计tab刷新控制）
    const tabBtns = document.querySelectorAll(".todo_content_button");
    if (tabBtns.length > 0) {
        tabBtns.forEach(btn => {
            btn.addEventListener("click", function () {
                const tab = this.dataset.tab;
                // 只在 statistics tab 处理刷新逻辑
                if (tab === "statistics") {
                    if (needUpdateStats) {
                        console.log("✅ needUpdateStats 为 true，更新统计");
                        updateTodoCounts(currentRange);
                        needUpdateStats = false;
                    } else {
                        console.log("⏩ needUpdateStats 为 false，跳过更新");
                    }
                }
            });
        });
    }

    // ===========================
    // 示例: updateStatistics 函数
    // 假设该函数在别处被调用
    function updateStatistics(stats) {
        // 修改为更安全的方式
        const totalTasksElem = document.getElementById("total-tasks");
        const completedTasksElem = document.getElementById("completed-tasks");
        const unfinishedTasksElem = document.getElementById("unfinished-tasks");
        const overdueTasksElem = document.getElementById("overdue-tasks");

        if (totalTasksElem) totalTasksElem.textContent = stats.total_tasks;
        if (completedTasksElem) completedTasksElem.textContent = stats.completed_tasks;
        if (unfinishedTasksElem) unfinishedTasksElem.textContent = stats.unfinished_tasks;
        if (overdueTasksElem) overdueTasksElem.textContent = stats.overdue_tasks;
    }

    // ===========================
    // 示例: updateTimeRangeStats 函数
    // 假设该函数在别处被调用
    function updateTimeRangeStats(stats) {
        const trTotalElem = document.getElementById("time-range-total");
        const trCompletedElem = document.getElementById("time-range-completed");
        const trUnfinishedElem = document.getElementById("time-range-unfinished");
        const trOverdueElem = document.getElementById("time-range-overdue");

        if (trTotalElem) trTotalElem.textContent = stats.total_tasks;
        if (trCompletedElem) trCompletedElem.textContent = stats.completed_tasks;
        if (trUnfinishedElem) trUnfinishedElem.textContent = stats.unfinished_tasks;
        if (trOverdueElem) trOverdueElem.textContent = stats.overdue_tasks;
    }

// 绑定项目相关按钮事件
    bindEditProjectEvents();
    bindEditProjectBtnApiEvents();
    // 启动倒计时
    updateProjectCountdown();
    setInterval(updateProjectCountdown, 60000); // 每分钟更新1次

    // 新增：编辑项目按钮（.edit-project-btn）简单填充逻辑
    document.querySelectorAll('.edit-project-btn').forEach(button => {
        button.addEventListener('click', function () {
            const projectId = this.getAttribute('data-project-id');
            const projectTitle = this.getAttribute('data-project-title');

            const idElem = document.getElementById('edit-project-id');
            const titleElem = document.getElementById('edit-title');
            
            if (idElem) idElem.value = projectId;
            if (titleElem) titleElem.value = projectTitle;
        });
    });

    // 绑定编辑项目提交按钮逻辑
    document.getElementById("edit-project-submit")?.addEventListener("click", function (e) {
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
                mail_notify: document.getElementById("edit-mail-notify").checked,
                important: document.getElementById("edit-important").checked
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
});

// 每隔30分钟自动刷新页面
setInterval(function() {
    window.location.reload();
}, 1800000);

// ===========================
// Dashboard Todo Select/Detail (for dashboard page)
document.addEventListener("DOMContentLoaded", function () {
    const select = document.getElementById('dashboard-todo-select');
    const detailDiv = document.getElementById('dashboard-todo-detail');
    // dashboardTodos 由模板渲染并挂载到 window
    const allTodos = window.dashboardTodos || {};
    
    if (select && detailDiv) {
        select.addEventListener('change', function () {
            const todoId = this.value;
            if (!todoId || !allTodos[todoId]) {
                detailDiv.innerHTML = `
                    <p style="padding: 1rem; color: #666;">To-Do is not selected</p>
                `;
                return;
            }
            const todo = allTodos[todoId];
            // Map status and priority to labels
            const statusLabels = {
                0: 'Not Started',
                1: 'In Progress',
                2: 'Completed',
                3: 'Overdue'
            };
            const priorityLabels = {
                0: 'Preparation',
                1: 'Normal',
                2: 'Important',
                3: 'Urgent'
            };
            const statusText = statusLabels[todo.status] || todo.status;
            const priorityText = priorityLabels[todo.priority] || todo.priority;
            detailDiv.innerHTML = `
                <div class="card" style="background: rgba(255, 255, 255, 0.01); color: #e0d7f4; border-radius: 20px;">
                     <div class="card-body" style="height: 97.4vh !important;">
                         <h3 align="center" class="card-title mb-2">${todo.title}</h3>
                         <br>
                        <p>Brief:</p>
                        <h6 class="card-subtitle mb-2 text-muted todo_brief">${todo.brief || 'No brief'}</h6>
                        <br>
                        <p>Content:</p>
                        <p class="card-text todo_content">${todo.content || 'No content'}</p>
                        <br>
                        <ul class="list-group list-group-flush mt-2">
                          <li class="list-group-item todo_others" style="background: transparent;">Start time: ${todo.start_time || '—'}</li>
                          <li class="list-group-item todo_others" style="background: transparent;">Deadline: ${todo.deadline || '—'}</li>
                          <li class="list-group-item todo_others" style="background: transparent;">Completion time: ${todo.completed_time || '—'}</li>
                          <li class="list-group-item todo_others" style="background: transparent;">Status: ${statusText}</li>
                          <li class="list-group-item todo_others" style="background: transparent;">Priority: ${priorityText}</li>
                        </ul>
                      </div>
                </div>
            `;
        });
    }
});